from __future__ import annotations

from datetime import datetime
import math
from typing import Any

from .dcs import DKS
from .pvt import PVT
from .scenario import (
    RECOVERY_RATE_COLUMN,
    WELLS_COLUMN,
    schedule_to_year_map,
)


# ============================================================================
# ПАРАМЕТРЫ ПО УМОЛЧАНИЮ (ДЕФОЛТНЫЕ ЗНАЧЕНИЯ)
# ============================================================================

default_params = {
    "start_year": 2025,
    "T_max": 50,
    "plateau_mode": "manual",              # только ручной режим
    "target_recovery_rate": 5.0,          # 5% отбор = 5 млрд м³/год
    
    # Пластовые параметры
    "P_pl": 25.0,                         # 250 бар
    "T_pl": 50,
    "G_nach": 100,
    "rho_otn": 0.56,
    
    # Параметры скважины
    "N_skv": 20,
    "H_skv": 1000,
    "d_NKT": 100,
    "a_coef": 0.2,
    "b_coef": 0.00001,
    "theta": 0.00003,
    "S_param": 0.0606,
    "min_debit_well": 5.0,
    "min_p_wellhead": 0.6,                # 6 бар
    
    # ДКС (только ограничительный режим)
    "DKS_mode": "ограничительный",         # всегда ограничительный
    "P_vh_DKS": 3.0,
    "P_vyh_DKS": 5.5,                     # 55 бар
    "N_DKS": 12,                          # максимальная мощность ДКС (МВт)
    "t_inlet": 10.0,
    "Q_max_DKS": 0,
    
    # Обводнение (отключено)
    "VGF_nach": 0,
    "dVGF_dG": 0,
    "VGF_krit": 200,
    "opt_water": 0,
    "opt_friction": 1,
    "pvt_method": "latonov",
    "wells_schedule": [],
    "recovery_schedule": [],
    "gathering_loss": 0.03,
}


def _to_kelvin(temp_c: float) -> float:
    return temp_c + 273.15


def _get_days_in_month(year: int, month: int) -> int:
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    days = days_in_month[month - 1]
    if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
        return 29
    return days


# ============================================================================
# ОСНОВНЫЕ РАСЧЁТНЫЕ ФУНКЦИИ
# ============================================================================

def calc_z_factor(pressure_bar: float, temp_c: float, gas_gravity: float) -> float:
    """Расчёт Z-фактора по методике коллеги"""
    T_K = temp_c + 273.15
    P_MPa = pressure_bar * 0.1
    Ppc = 4.604 + 0.35 * gas_gravity
    Tpc = 92.2 + 175.5 * gas_gravity
    
    Ppr = P_MPa / Ppc if Ppc > 0 else 1.0
    Tpr = T_K / Tpc if Tpc > 0 else 1.0
    
    z = 1 - (3.52 * Ppr) / (10 ** (0.9813 * Tpr)) + (0.274 * Ppr * Ppr) / (10 ** (0.8157 * Tpr))
    
    if z < 0.6:
        z = 0.6
    if z > 1.2:
        z = 1.2
    return z


def calc_z_inlet(p_inlet_mpa: float, t_inlet_c: float, gas_gravity: float) -> float:
    """Расчёт Z-фактора на входе ДКС"""
    Tpr_in = ((9 / 5) * (t_inlet_c + 273.15)) / (168 + 325 * gas_gravity - 12.5 * gas_gravity * gas_gravity)
    P_psi_in = p_inlet_mpa * 10 * 14.50377
    Ppc_in = 677 + 15 * gas_gravity - 37.5 * gas_gravity * gas_gravity
    Ppr_in = P_psi_in / Ppc_in if Ppc_in > 0 else 1.0
    
    A = 1.39 * math.sqrt(max(Tpr_in - 0.92, 0.0001)) - 0.36 * Tpr_in - 0.101
    B = 0.62 - 0.23 * Tpr_in
    C = 0.066 / max(Tpr_in - 0.86, 0.0001) - 0.037
    D = 0.32
    E = 9 * (Tpr_in - 1)
    F = 0.132 - 0.32 * math.log10(Tpr_in)
    G = 10 ** (0.3106 - 0.49 * Tpr_in + 0.1824 * Tpr_in * Tpr_in)
    
    ExpVal = B * Ppr_in + C * Ppr_in * Ppr_in + (D * (Ppr_in ** 6)) / (10 ** E)
    
    z = A + (1 - A) / math.exp(ExpVal) + F * (Ppr_in ** G)
    return max(0.6, min(z, 1.2))


def calc_debit_from_depression(p_res_bar: float, depression_bar: float,
                                a_coef: float, b_coef: float) -> float:
    """Расчёт дебита по депрессии (тыс.м³/сут на скважину)"""
    p_wf_bar = max(0.1, p_res_bar - depression_bar)
    dP2 = p_res_bar ** 2 - p_wf_bar ** 2
    
    if dP2 <= 0:
        return 0.0
    
    if b_coef == 0:
        return dP2 / a_coef if a_coef > 0 else 0.0
    
    D = a_coef ** 2 + 4 * b_coef * dP2
    if D <= 0:
        return 0.0
    
    return (-a_coef + math.sqrt(D)) / (2 * b_coef)


def calc_wellhead_pressure(p_wf_bar: float, q_day_thousand: float,
                           theta: float, s_param: float) -> float:
    """Расчёт устьевого давления (бар)"""
    if p_wf_bar <= 0 or q_day_thousand <= 0:
        return 6.0
    
    term = theta * (q_day_thousand ** 2)
    if p_wf_bar ** 2 <= term:
        return 6.0
    
    expr = (p_wf_bar ** 2 - term) / math.exp(2 * s_param)
    if expr <= 0:
        return 6.0
    
    return math.sqrt(expr)


def calc_dks_power(q_mm3day: float, p_inlet_mpa: float, p_out_mpa: float,
                   t_inlet_c: float, gas_gravity: float) -> float:
    """Расчёт мощности ДКС (МВт)"""
    if q_mm3day <= 0 or p_inlet_mpa <= 0.01:
        return 0.0
    
    z_in = calc_z_inlet(p_inlet_mpa, t_inlet_c, gas_gravity)
    ratio = p_out_mpa / p_inlet_mpa
    if ratio <= 1:
        return 0.0
    
    T_abs = t_inlet_c + 273.15
    power = 2.04 * z_in * T_abs * (ratio - 1) * (q_mm3day / 800)
    return max(0.0, power)


def compute_year(test_prod_mcm: float, cum_prod_mcm: float, params: dict[str, Any],
                 n_wells: int, max_depress_bar: float, pmg_bar: float,
                 max_dks_mw: float, enforce: bool) -> dict[str, Any]:
    """Расчёт для одного года"""
    result = {
        "ok": True,
        "debit": 0.0,
        "pRes": 0.0,
        "pWf": 0.0,
        "depr": 0.0,
        "pWh": 0.0,
        "pIn": 0.0,
        "dks": 0.0,
    }
    
    g_nach_mcm = params["G_nach"] * 1000
    a_coef = params["a_coef"]
    b_coef = params["b_coef"]
    p_pl_init_bar = params["P_pl"] * 10
    t_pl_c = params["T_pl"]
    rho_otn = params["rho_otn"]
    theta = params["theta"]
    s_param = params["S_param"]
    min_p_wh_bar = params["min_p_wellhead"] * 10
    min_debit_well = params["min_debit_well"]
    t_inlet_c = params.get("t_inlet", 10.0)
    
    debit = (test_prod_mcm / n_wells / 365) * 1000 if n_wells > 0 else 0
    result["debit"] = debit
    
    temp_remaining = g_nach_mcm - (cum_prod_mcm + test_prod_mcm)
    if temp_remaining < 0:
        result["ok"] = False
        return result
    
    # Расчёт пластового давления
    z_initial = calc_z_factor(p_pl_init_bar, t_pl_c, rho_otn)
    p_res_bar = p_pl_init_bar * (temp_remaining / g_nach_mcm)
    
    for _ in range(20):
        z_f = calc_z_factor(p_res_bar, t_pl_c, rho_otn)
        p_over_z = (p_pl_init_bar / z_initial) * (temp_remaining / g_nach_mcm)
        p_res_bar = p_over_z * z_f
        if p_res_bar < 0:
            result["ok"] = False
            return result
    
    result["pRes"] = p_res_bar
    
    # Забойное давление
    expr = p_res_bar ** 2 - a_coef * debit - b_coef * (debit ** 2)
    if expr <= 0:
        result["ok"] = False
        return result
    
    p_wf_bar = math.sqrt(expr)
    depr = max(0.0, p_res_bar - p_wf_bar)
    result["pWf"] = p_wf_bar
    result["depr"] = depr
    
    if enforce and depr > max_depress_bar:
        result["ok"] = False
        return result
    
    # Устьевое давление
    p_wh_bar = calc_wellhead_pressure(p_wf_bar, debit, theta, s_param)
    result["pWh"] = p_wh_bar
    
    if enforce and p_wh_bar < min_p_wh_bar:
        result["ok"] = False
        return result
    
    # Давление на входе ДКС
    p_inlet_mpa = p_wh_bar / 10
    result["pIn"] = p_inlet_mpa
    
    # Мощность ДКС (всегда считаем для ограничительного режима)
    dks_power = 0.0
    if p_inlet_mpa > 0.01 and pmg_bar > 0:
        q_mm3day = test_prod_mcm / 365
        dks_power = calc_dks_power(q_mm3day, p_inlet_mpa, pmg_bar / 10, t_inlet_c, rho_otn)
    
    if enforce and max_dks_mw > 0 and dks_power > max_dks_mw:
        result["ok"] = False
        return result
    
    result["dks"] = dks_power
    
    if enforce and n_wells > 0 and debit < min_debit_well:
        result["ok"] = False
        return result
    
    return result


def calculate_forecast(params: dict[str, Any]) -> dict[str, Any]:
    """Расчёт прогноза добычи газа"""
    
    params = {**default_params, **params}
    
    start_year = int(params["start_year"])
    horizon_years = int(params["T_max"])
    g_nach_bcm = params["G_nach"]
    g_nach_mcm = g_nach_bcm * 1000
    
    # Сценарии
    wells_by_year = schedule_to_year_map(
        raw_schedule=params.get("wells_schedule"),
        start_year=start_year,
        horizon_years=horizon_years,
        default_value=params["N_skv"],
        value_column=WELLS_COLUMN,
        minimum_value=0,
        cast_type=int,
    )
    
    recovery_by_year = schedule_to_year_map(
        raw_schedule=params.get("recovery_schedule"),
        start_year=start_year,
        horizon_years=horizon_years,
        default_value=params["target_recovery_rate"],
        value_column=RECOVERY_RATE_COLUMN,
        minimum_value=0,
        cast_type=float,
    )
    
    cumulative_mcm = 0.0
    yearly_rows = []
    
    # Дефолтные параметры для ограничений
    max_depress_bar = 30.0      # 30 бар
    pmg_bar = 55.0              # 55 бар
    max_dks_mw = params.get("N_DKS", 12.0)
    
    for year in range(start_year, start_year + horizon_years):
        n_wells = wells_by_year.get(year, params["N_skv"])
        target_rate_pct = recovery_by_year.get(year, params["target_recovery_rate"])
        target_annual_mcm = (target_rate_pct / 100) * g_nach_mcm
        
        if cumulative_mcm + target_annual_mcm > g_nach_mcm:
            target_annual_mcm = max(0.0, g_nach_mcm - cumulative_mcm)
        
        if target_annual_mcm <= 0:
            break
        
        # Проверка возможности добычи
        test = compute_year(
            test_prod_mcm=target_annual_mcm,
            cum_prod_mcm=cumulative_mcm,
            params=params,
            n_wells=n_wells,
            max_depress_bar=max_depress_bar,
            pmg_bar=pmg_bar,
            max_dks_mw=max_dks_mw,
            enforce=True
        )
        
        # Если не прошло — бинарный поиск
        if not test["ok"]:
            lo, hi = 0.0, target_annual_mcm
            for _ in range(30):
                mid = (lo + hi) / 2
                r = compute_year(
                    test_prod_mcm=mid,
                    cum_prod_mcm=cumulative_mcm,
                    params=params,
                    n_wells=n_wells,
                    max_depress_bar=max_depress_bar,
                    pmg_bar=pmg_bar,
                    max_dks_mw=max_dks_mw,
                    enforce=True
                )
                if r["ok"]:
                    lo = mid
                    test = r
                else:
                    hi = mid
            actual_prod_mcm = lo
        else:
            actual_prod_mcm = target_annual_mcm
        
        cumulative_mcm += actual_prod_mcm
        recovery_pct = (cumulative_mcm / g_nach_mcm) * 100 if g_nach_mcm > 0 else 0
        remaining_mcm = g_nach_mcm - cumulative_mcm
        
        yearly_rows.append({
            "Год": year,
            "Количество скважин": n_wells,
            "Целевой темп отбора, %": round(target_rate_pct, 2),
            "Целевая добыча, млн м³/год": round(target_annual_mcm, 0),
            "Добыча газа, млн м³/год": round(actual_prod_mcm, 0),
            "Добыча газа, млрд м³/год": round(actual_prod_mcm / 1000, 3),
            "Накоплено, млрд м³": round(cumulative_mcm / 1000, 3),
            "Остаток, млрд м³": round(remaining_mcm / 1000, 3),
            "КИГ, %": round(recovery_pct, 2),
            "P_пл, бар": round(test["pRes"], 2),
            "P_заб, бар": round(test["pWf"], 2),
            "Депрессия, бар": round(test["depr"], 2),
            "P_у, бар": round(test["pWh"], 2),
            "Дебит скв, тыс.м³/сут": round(test["debit"], 2),
            "Мощность ДКС, МВт": round(test["dks"], 2),
        })
        
        if cumulative_mcm >= g_nach_mcm:
            break
    
    # Конвертация в месячные данные
    monthly_rows = []
    month_names = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", 
                   "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    
    cumulative_mcm = 0
    for i, year_row in enumerate(yearly_rows):
        year = year_row["Год"]
        prod_mcm = year_row["Добыча газа, млн м³/год"]
        monthly_prod_mcm = prod_mcm / 12
        
        prev_row = yearly_rows[i-1] if i > 0 else None
        
        for month in range(12):
            cumulative_mcm += monthly_prod_mcm
            frac = (month + 0.5) / 12
            
            def interp(a, b):
                if a is None or b is None:
                    return b if b is not None else a
                return a + (b - a) * frac
            
            monthly_rows.append({
                "Дата": datetime(year, month + 1, 1),
                "Год": year,
                "Месяц": month + 1,
                "Название месяца": month_names[month],
                "Количество скважин": year_row["Количество скважин"],
                "Добыча газа, млн м³/мес": round(monthly_prod_mcm, 0),
                "Добыча газа, млрд м³/мес": round(monthly_prod_mcm / 1000, 4),
                "Накоплено, млрд м³": round(cumulative_mcm / 1000, 3),
                "КИГ, %": round((cumulative_mcm / g_nach_mcm) * 100, 2),
                "P_пл, бар": round(interp(prev_row.get("P_пл, бар") if prev_row else None, year_row["P_пл, бар"]), 2),
                "P_заб, бар": round(interp(prev_row.get("P_заб, бар") if prev_row else None, year_row["P_заб, бар"]), 2),
                "P_у, бар": round(interp(prev_row.get("P_у, бар") if prev_row else None, year_row["P_у, бар"]), 2),
                "Дебит скв, тыс.м³/сут": round(interp(prev_row.get("Дебит скв, тыс.м³/сут") if prev_row else None, year_row["Дебит скв, тыс.м³/сут"]), 2),
                "Мощность ДКС, МВт": round(interp(prev_row.get("Мощность ДКС, МВт") if prev_row else None, year_row["Мощность ДКС, МВт"]), 2),
            })
    
    return {
        "yearly_df": yearly_rows,
        "monthly_df": monthly_rows,
        "params": params,
        "G_nach": params["G_nach"],
        "plateau_level": yearly_rows[0]["Добыча газа, млрд м³/год"] if yearly_rows else 0,
        "plateau_years": len(yearly_rows),
        "warning": None,
    }