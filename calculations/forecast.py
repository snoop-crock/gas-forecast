from __future__ import annotations

from datetime import datetime
import math
from typing import Any

from .dcs import DKS
from .hydraulics import Hydraulics
from .inflow import Inflow
from .material_balance import MaterialBalance
from .scenario import (
    RECOVERY_RATE_COLUMN,
    WELLS_COLUMN,
    build_yearly_schedule,
    schedule_to_year_map,
)
from .water_influx import WaterInflux


default_params = {
    "start_year": 2025,
    "T_max": 60,
    "Q_polka": 0,
    "plateau_mode": "auto",
    "target_recovery_rate": 1.5,
    "P_pl": 25,
    "T_pl": 80,
    "G_nach": 100,
    "rho_otn": 0.6,
    "N_skv": 10,
    "H_skv": 2500,
    "d_NKT": 100,
    "a_coef": 0.15,
    "b_coef": 0.0003,
    "theta": 0.00003,
    "S_param": 0.0606,
    "min_debit_well": 0.0,
    "min_p_wellhead": 0.0,
    "dP_max": 10,
    "K_eks": 0.9,
    "DKS_mode": "расчетный",
    "P_vh_DKS": 5,
    "P_vyh_DKS": 7.5,
    "N_DKS": 50,
    "Q_max_DKS": 0,
    "T_in_DKS": 0,
    "VGF_nach": 0,
    "dVGF_dG": 10,
    "VGF_krit": 200,
    "opt_water": 1,
    "opt_friction": 1,
    "pvt_method": "latonov",
    "wells_schedule": [],
    "recovery_schedule": [],
    "gathering_loss": 0.03,
}


def _max_well_rate_thousand_m3day(
    p_pl: float,
    p_u_min: float,
    a_coef: float,
    b_coef: float,
    d_p_max: float,
    h_skv: float,
    rho_otn: float,
    t_pl: float,
    d_nkt: float,
    vgf: float,
    vgf_krit: float,
    opt_friction: int,
) -> tuple[float, float, float]:
    """
    Returns (q_well_thousand_m3day, p_zab, p_u).
    Constraint: p_pl - p_zab <= d_p_max and p_u >= p_u_min.
    """
    p_pl = float(p_pl)
    p_u_min = float(p_u_min)

    if p_pl <= 0.5:
        return 0.0, max(0.5, p_pl), max(0.1, p_pl)

    p_zab_min = max(0.5, p_pl - float(d_p_max))
    p_zab_max = p_pl

    # If even at p_zab=p_pl (zero inflow) the wellhead pressure is below requirement -> infeasible.
    p_u_at_max = Hydraulics.P_u_from_P_zab(p_zab_max, 0, h_skv, rho_otn, t_pl, d_nkt) if opt_friction == 1 else max(0.5, p_zab_max - 0.001 * h_skv * rho_otn)
    if p_u_at_max < p_u_min:
        return 0.0, p_zab_max, p_u_at_max

    best_q = 0.0
    best_p_zab = p_zab_max
    best_p_u = p_u_at_max

    low = p_zab_min
    high = p_zab_max
    for _ in range(30):
        mid = (low + high) / 2

        q = Inflow.Q_gas(p_pl, mid, a_coef, b_coef)
        q *= WaterInflux.rel_perm_gas(vgf, vgf_krit)

        if opt_friction == 1:
            p_u = Hydraulics.P_u_from_P_zab(mid, q, h_skv, rho_otn, t_pl, d_nkt)
        else:
            p_u = max(0.5, mid - 0.001 * h_skv * rho_otn)

        if p_u >= p_u_min:
            # Can try lower p_zab -> higher q (while keeping p_u >= min)
            best_q = q
            best_p_zab = mid
            best_p_u = p_u
            high = mid
        else:
            low = mid

    return float(best_q), float(best_p_zab), float(best_p_u)


def _wellhead_pressure_mpa(p_wf_mpa: float, q_thousand_m3day: float, theta: float, s_param: float) -> float:
    """
    VBA reference:
        Pwh(bar)^2 = ((Pwf(bar)^2 - theta*Q^2) / exp(2*S))
    Here pressures are in MPa, so bar = 10*MPa:
        Pwh(MPa)^2 = ((Pwf(MPa)^2 - (theta/100)*Q^2) / exp(2*S))
    """
    p_wf_mpa = float(p_wf_mpa)
    q_thousand_m3day = float(q_thousand_m3day)
    theta = float(theta)
    s_param = float(s_param)

    expr = (p_wf_mpa ** 2) - (theta / 100.0) * (q_thousand_m3day ** 2)
    if expr <= 0:
        return 0.0
    return (expr / math.exp(2.0 * s_param)) ** 0.5


def _max_well_rate_with_wellhead_constraints_thousand_m3day(
    p_pl: float,
    a_coef: float,
    b_coef: float,
    d_p_max: float,
    theta: float,
    s_param: float,
    min_p_wellhead: float,
    min_debit_well: float,
) -> tuple[float, float, float]:
    """
    Returns (q_well_thousand_m3day, p_wf_mpa, p_wellhead_mpa) under constraints:
      - p_pl - p_wf <= dP_max
      - p_wellhead >= min_p_wellhead (via theta/S transform)
      - q_well >= min_debit_well (if > 0)
    """
    p_pl = float(p_pl)
    min_p_wellhead = float(min_p_wellhead)
    min_debit_well = float(min_debit_well)

    if p_pl <= 0.5:
        return 0.0, max(0.5, p_pl), 0.0

    p_wf_min = max(0.5, p_pl - float(d_p_max))
    p_wf_max = p_pl

    def feasible(p_wf: float) -> tuple[bool, float, float]:
        q = Inflow.Q_gas(p_pl, p_wf, a_coef, b_coef)
        p_wh = _wellhead_pressure_mpa(p_wf, q, theta, s_param)
        ok = True
        if min_debit_well > 0 and q < min_debit_well:
            ok = False
        if min_p_wellhead > 0 and p_wh < min_p_wellhead:
            ok = False
        return ok, q, p_wh

    ok_at_max, _, _ = feasible(p_wf_max)
    if not ok_at_max:
        return 0.0, p_wf_max, 0.0

    best_q = 0.0
    best_p_wf = p_wf_max
    best_p_wh = 0.0

    low = p_wf_min
    high = p_wf_max
    for _ in range(40):
        mid = (low + high) / 2
        ok, q, p_wh = feasible(mid)
        if ok:
            best_q, best_p_wf, best_p_wh = q, mid, p_wh
            high = mid
        else:
            low = mid

    return float(best_q), float(best_p_wf), float(best_p_wh)

def _initial_potential_rate_bcm_per_year(params: dict[str, Any], wells_count: int | None = None) -> float:
    p_pl = params["P_pl"]
    d_p_max = params["dP_max"]
    p_zab_max = max(0.5, p_pl - d_p_max)
    q_skv_day = Inflow.Q_gas(p_pl, p_zab_max, params["a_coef"], params["b_coef"])
    wells = wells_count if wells_count is not None else params["N_skv"]
    return q_skv_day * wells * params["K_eks"] * 365 / 1e6


def _annual_target_bcm(
    year: int,
    params: dict[str, Any],
    default_rate: float,
    recovery_by_year: dict[int, float],
) -> float:
    if recovery_by_year:
        recovery_rate = recovery_by_year.get(year, default_rate)
        return (recovery_rate / 100) * params["G_nach"]

    if params["Q_polka"] and params["Q_polka"] > 0:
        return params["Q_polka"]

    return (default_rate / 100) * params["G_nach"]


def _scenario_maps(params: dict[str, Any]) -> tuple[dict[int, int], dict[int, float]]:
    start_year = int(params["start_year"])
    horizon = int(params["T_max"])
    wells_by_year = schedule_to_year_map(
        raw_schedule=params.get("wells_schedule"),
        start_year=start_year,
        horizon_years=horizon,
        default_value=params["N_skv"],
        value_column=WELLS_COLUMN,
        minimum_value=0,
        cast_type=int,
    )
    recovery_by_year = schedule_to_year_map(
        raw_schedule=params.get("recovery_schedule"),
        start_year=start_year,
        horizon_years=horizon,
        default_value=params["target_recovery_rate"],
        value_column=RECOVERY_RATE_COLUMN,
        minimum_value=0,
        cast_type=float,
    )
    return wells_by_year, recovery_by_year


def _build_output_schedules(params: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    wells_schedule = build_yearly_schedule(
        start_year=params["start_year"],
        horizon_years=params["T_max"],
        default_value=params["N_skv"],
        value_column=WELLS_COLUMN,
        raw_schedule=params.get("wells_schedule"),
        minimum_value=0,
        cast_type=int,
    )
    recovery_schedule = build_yearly_schedule(
        start_year=params["start_year"],
        horizon_years=params["T_max"],
        default_value=params["target_recovery_rate"],
        value_column=RECOVERY_RATE_COLUMN,
        raw_schedule=params.get("recovery_schedule"),
        minimum_value=0,
        cast_type=float,
    )
    return wells_schedule, recovery_schedule


def find_optimal_recovery_rate(params: dict[str, Any], max_years: int = 30) -> tuple[int, int]:
    g_nach = params["G_nach"] * 1e9
    p_pl_init = params["P_pl"]
    t_pl = params["T_pl"] + 273.15
    rho_otn = params["rho_otn"]
    n_skv = params["N_skv"]
    k_eks = params["K_eks"]
    a_coef = params["a_coef"]
    b_coef = params["b_coef"]
    d_p_max = params["dP_max"]
    vgf_nach = params.get("VGF_nach", 0)
    dvgf_dg = params.get("dVGF_dG", 10)
    vgf_krit = params.get("VGF_krit", 200)

    best_rate = 1
    best_years = 0

    for rate in range(1, 21):
        annual_target = (rate / 100) * (g_nach / 1e9)
        monthly_target = annual_target / 12
        q_cum = 0.0
        p_pl_curr = p_pl_init
        vgf = vgf_nach
        years_on_target = 0

        for year in range(1, max_years + 1):
            year_ok = True
            for _month in range(12):
                if q_cum > 0:
                    p_pl_curr = MaterialBalance.pressure_from_cumulative(
                        p_pl_init,
                        t_pl,
                        rho_otn,
                        g_nach,
                        q_cum,
                        prev_P_pl=p_pl_curr,
                    )

                if p_pl_curr < 0.5:
                    year_ok = False
                    break

                p_zab_max = max(0.5, p_pl_curr - d_p_max)
                q_skv_day = Inflow.Q_gas(p_pl_curr, p_zab_max, a_coef, b_coef)
                q_skv_day *= WaterInflux.rel_perm_gas(vgf, vgf_krit)
                q_monthly_potential = q_skv_day * n_skv * k_eks * 30 / 1e6

                if q_monthly_potential < monthly_target * 0.98:
                    year_ok = False
                    break

                q_cum += monthly_target * 1e9
                vgf = WaterInflux.VGF_from_cumulative(vgf_nach, dvgf_dg, q_cum, g_nach, vgf_krit)

            if not year_ok:
                break
            years_on_target = year

        if years_on_target > best_years:
            best_years = years_on_target
            best_rate = rate

    return best_rate, best_years


def calculate_forecast(params: dict[str, Any]) -> dict[str, Any]:
    params = {**default_params, **params}
    wells_by_year, recovery_by_year = _scenario_maps(params)

    plateau_mode = params.get("plateau_mode", "auto")
    actual_recovery_rate = float(params.get("target_recovery_rate", default_params["target_recovery_rate"]))
    warning_message = None

    if plateau_mode == "auto":
        optimal_rate, optimal_years = find_optimal_recovery_rate(params, max_years=30)
        actual_recovery_rate = float(max(optimal_rate, 1))
        warning_message = f"Оптимальный темп: {actual_recovery_rate:.1f}% (полка {optimal_years} лет)"
    else:
        sustainable_rate, sustainable_years = find_optimal_recovery_rate(params, max_years=5)
        if actual_recovery_rate > sustainable_rate:
            warning_message = (
                f"Темп {actual_recovery_rate:.1f}% может быть завышен. "
                f"Устойчиво около {sustainable_rate}% на горизонте {sustainable_years} лет"
            )

    start_year = int(params["start_year"])
    horizon_years = int(params["T_max"])
    g_nach = params["G_nach"] * 1e9
    t_pl = params["T_pl"] + 273.15
    p_pl_init = params["P_pl"]
    rho_otn = params["rho_otn"]
    h_skv = params["H_skv"]
    d_nkt = params["d_NKT"]
    a_coef = params["a_coef"]
    b_coef = params["b_coef"]
    d_p_max = params["dP_max"]
    k_eks = params["K_eks"]
    dks_mode = params["DKS_mode"]
    p_vh_dks = params["P_vh_DKS"]
    p_vyh_dks = params["P_vyh_DKS"]
    n_dks_max = params["N_DKS"]
    vgf_nach = params["VGF_nach"]
    dvgf_dg = params["dVGF_dG"]
    vgf_krit = params["VGF_krit"]
    opt_friction = params["opt_friction"]
    t_in_dks = float(params.get("T_in_DKS", params["T_pl"]) or params["T_pl"]) + 273.15

    q_cum = 0.0
    p_pl_curr = p_pl_init
    vgf = vgf_nach
    monthly_rows: list[dict[str, Any]] = []
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    initial_plateau_year = _annual_target_bcm(start_year, params, actual_recovery_rate, recovery_by_year)
    initial_max_potential = _initial_potential_rate_bcm_per_year(params, wells_by_year.get(start_year, params["N_skv"]))
    plateau_level = min(initial_plateau_year, initial_max_potential) if initial_plateau_year > 0 else initial_max_potential

    for step in range(horizon_years * 12):
        year = start_year + step // 12
        month = (step % 12) + 1
        days = days_in_month[month - 1]
        if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
            days = 29

        current_wells = int(wells_by_year.get(year, params["N_skv"]))
        target_annual_rate = float(recovery_by_year.get(year, actual_recovery_rate))
        target_annual_production = _annual_target_bcm(year, params, actual_recovery_rate, recovery_by_year)
        target_monthly_production = target_annual_production / 12

        if q_cum > 0:
            p_pl_curr = MaterialBalance.pressure_from_cumulative(
                p_pl_init,
                t_pl,
                rho_otn,
                g_nach,
                q_cum,
                prev_P_pl=p_pl_curr,
            )

        if p_pl_curr < 0.5:
            break

        # Excel/VBA-like constraints: inflow -> bottomhole pressure (p_wf) -> wellhead pressure (theta/S).
        # DKS turns on when discharge pressure is higher than suction pressure and a positive power is required.
        theta = float(params.get("theta", 0) or 0)
        s_param = float(params.get("S_param", 0) or 0)
        min_debit_well = float(params.get("min_debit_well", 0) or 0)
        min_p_wellhead = float(params.get("min_p_wellhead", 0) or 0)

        q_well_potential, p_wf_used, p_wh_used = _max_well_rate_with_wellhead_constraints_thousand_m3day(
            p_pl=p_pl_curr,
            a_coef=a_coef,
            b_coef=b_coef,
            d_p_max=d_p_max,
            theta=theta,
            s_param=s_param,
            min_p_wellhead=min_p_wellhead,
            min_debit_well=min_debit_well,
        )
        q_total_day_potential = q_well_potential * current_wells * k_eks
        q_monthly_potential = q_total_day_potential * days / 1e6

        meets_target = q_monthly_potential >= target_monthly_production and target_monthly_production > 0
        if target_monthly_production > 0:
            q_monthly = min(q_monthly_potential, target_monthly_production)
        else:
            q_monthly = q_monthly_potential

        q_total_day = q_monthly * 1e6 / days if days else 0

        P_before_dks = max(0.01, p_wh_used)
        dks_on = (p_vyh_dks > P_before_dks + 1e-9)

        # Optional hard cap on DKS throughput (its own plateau), bcm/year -> m3/day
        q_max_dks_bcm_year = float(params.get("Q_max_DKS", 0) or 0)
        q_max_dks_day_limit = (q_max_dks_bcm_year * 1e9 / 365) if q_max_dks_bcm_year > 0 else 0
        if dks_on and q_max_dks_day_limit > 0 and q_total_day > q_max_dks_day_limit:
            q_total_day = q_max_dks_day_limit
            q_monthly = q_total_day * days / 1e6

        if dks_mode == "ограничительный":
            if dks_on:
                q_max_dks = DKS.Q_max_from_power(n_dks_max, P_before_dks, p_vyh_dks, t_in_dks, rho_otn) * 1e6
                if q_max_dks_day_limit > 0:
                    q_max_dks = min(q_max_dks, q_max_dks_day_limit) if q_max_dks > 0 else q_max_dks_day_limit
                if q_max_dks > 0 and q_total_day > q_max_dks:
                    q_total_day = q_max_dks
                    q_monthly = q_total_day * days / 1e6
                n_dks = n_dks_max
            else:
                n_dks = 0
        else:
            n_dks = DKS.power_calc(q_total_day / 1e6, P_before_dks, p_vyh_dks, t_in_dks, rho_otn) if dks_on else 0

        # Keep representative pressures for outputs/diagnostics
        p_zab_max = p_wf_used
        p_u = P_before_dks

        q_cum += q_monthly * 1e9
        vgf = WaterInflux.VGF_from_cumulative(vgf_nach, dvgf_dg, q_cum, g_nach, vgf_krit)
        q_water_m3 = q_monthly * 1e9 * vgf / 1e6
        q_water_thousand_m3 = q_water_m3 / 1000
        actual_monthly_recovery_rate = (q_monthly * 12) / (g_nach / 1e9) * 100 if g_nach > 0 else 0

        monthly_rows.append(
            {
                "Дата": datetime(year, month, 1),
                "Год": year,
                "Квартал": (month - 1) // 3 + 1,
                "Месяц": month,
                "Количество скважин": current_wells,
                "Целевой темп отбора, %": round(target_annual_rate, 3),
                "Целевая добыча, млрд м³/год": round(target_annual_production, 4),
                "P_пл, МПа": round(p_pl_curr, 3),
                "Добыча газа, млрд м³/мес": round(q_monthly, 4),
                "Добыча газа, млрд м³/год": round(q_monthly * 12, 3),
                "Накоплено, млрд м³": round(q_cum / 1e9, 3),
                "Остаток, млрд м³": round(max(0, (g_nach - q_cum) / 1e9), 3),
                "Темп отбора, %": round(actual_monthly_recovery_rate, 3),
                "P_у, МПа": round(p_u, 3),
                "P_заб, МПа": round(p_zab_max, 3),
                "ВГФ, г/м³": round(vgf, 3),
                "Добыча воды, тыс. м³/мес": round(q_water_thousand_m3, 3),
                "Мощность ДКС, МВт": round(n_dks, 3),
                "На полке": int(meets_target),
                "Потенциал, млрд м³/мес": round(q_monthly_potential, 4),
            }
        )

    if not monthly_rows:
        wells_schedule, recovery_schedule = _build_output_schedules(params)
        return {
            "monthly_df": [],
            "yearly_df": [],
            "params": params,
            "warning": warning_message,
            "wells_schedule": wells_schedule,
            "recovery_schedule": recovery_schedule,
        }

    yearly_acc: dict[int, dict[str, float]] = {}
    yearly_last: dict[int, dict[str, Any]] = {}
    yearly_counts: dict[int, int] = {}

    for row in monthly_rows:
        year = int(row["Год"])
        yearly_counts[year] = yearly_counts.get(year, 0) + 1
        acc = yearly_acc.setdefault(
            year,
            {
                "sum_target_rate": 0.0,
                "sum_target_prod": 0.0,
                "sum_q_monthly": 0.0,
                "sum_p_pl": 0.0,
                "sum_recovery_rate": 0.0,
                "sum_dks_power": 0.0,
                "max_wells": 0.0,
                "max_plateau": 0.0,
            },
        )
        acc["sum_target_rate"] += float(row.get("Целевой темп отбора, %", 0) or 0)
        acc["sum_target_prod"] += float(row.get("Целевая добыча, млрд м³/год", 0) or 0)
        acc["sum_q_monthly"] += float(row.get("Добыча газа, млрд м³/мес", 0) or 0)
        acc["sum_p_pl"] += float(row.get("P_пл, МПа", 0) or 0)
        acc["sum_recovery_rate"] += float(row.get("Темп отбора, %", 0) or 0)
        acc["sum_dks_power"] += float(row.get("Мощность ДКС, МВт", 0) or 0)
        acc["max_wells"] = max(acc["max_wells"], float(row.get("Количество скважин", 0) or 0))
        acc["max_plateau"] = max(acc["max_plateau"], float(row.get("На полке", 0) or 0))
        yearly_last[year] = row

    yearly_rows: list[dict[str, Any]] = []
    for year in sorted(yearly_acc.keys()):
        n = max(1, yearly_counts.get(year, 1))
        acc = yearly_acc[year]
        last_row = yearly_last[year]
        yearly_rows.append(
            {
                "Год": int(year),
                "Количество скважин": int(round(acc["max_wells"])),
                "Целевой темп отбора, %": acc["sum_target_rate"] / n,
                "Целевая добыча, млрд м³/год": acc["sum_target_prod"] / n,
                "Добыча газа, млрд м³/год": acc["sum_q_monthly"],
                "Накоплено, млрд м³": float(last_row.get("Накоплено, млрд м³", 0) or 0),
                "Среднее P_пл, МПа": acc["sum_p_pl"] / n,
                "Средний темп отбора, %": acc["sum_recovery_rate"] / n,
                "Средняя мощность ДКС, МВт": acc["sum_dks_power"] / n,
                "На полке": int(round(acc["max_plateau"])),
            }
        )

    wells_schedule, recovery_schedule = _build_output_schedules(params)
    plateau_years = int(sum(1 for r in yearly_rows if int(r.get("На полке", 0) or 0) == 1))

    return {
        "monthly_df": monthly_rows,
        "yearly_df": yearly_rows,
        "params": params,
        "G_nach": g_nach / 1e9,
        "plateau_level": round(plateau_level, 3),
        "plateau_years": plateau_years,
        "optimal_rate": actual_recovery_rate if plateau_mode == "auto" else None,
        "warning": warning_message,
        "wells_schedule": wells_schedule,
        "recovery_schedule": recovery_schedule,
    }
