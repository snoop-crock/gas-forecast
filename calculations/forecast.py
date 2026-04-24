from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

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
    "dP_max": 10,
    "K_eks": 0.9,
    "DKS_mode": "расчетный",
    "P_vh_DKS": 5,
    "P_vyh_DKS": 7.5,
    "N_DKS": 50,
    "VGF_nach": 0,
    "dVGF_dG": 10,
    "VGF_krit": 200,
    "opt_water": 1,
    "opt_friction": 1,
    "pvt_method": "latonov",
    "wells_schedule": [],
    "recovery_schedule": [],
}


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
    p_vyh_dks = params["P_vyh_DKS"]
    n_dks_max = params["N_DKS"]
    vgf_nach = params["VGF_nach"]
    dvgf_dg = params["dVGF_dG"]
    vgf_krit = params["VGF_krit"]
    opt_friction = params["opt_friction"]

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

        p_zab_max = max(0.5, p_pl_curr - d_p_max)
        q_skv_day_potential = Inflow.Q_gas(p_pl_curr, p_zab_max, a_coef, b_coef)
        q_skv_day_potential *= WaterInflux.rel_perm_gas(vgf, vgf_krit)
        q_total_day_potential = q_skv_day_potential * current_wells * k_eks
        q_monthly_potential = q_total_day_potential * days / 1e6

        meets_target = q_monthly_potential >= target_monthly_production and target_monthly_production > 0
        if target_monthly_production > 0:
            q_monthly = min(q_monthly_potential, target_monthly_production)
        else:
            q_monthly = q_monthly_potential
        q_total_day = q_monthly * 1e6 / days if days else 0

        if opt_friction == 1:
            p_u = Hydraulics.P_u_from_P_zab(p_zab_max, q_total_day, h_skv, rho_otn, t_pl, d_nkt)
        else:
            p_u = max(0.5, p_zab_max - 0.001 * h_skv * rho_otn)

        if dks_mode == "ограничительный":
            q_max_dks = DKS.Q_max_from_power(n_dks_max, p_u, p_vyh_dks, t_pl, rho_otn) * 1e6
            if q_max_dks > 0 and q_total_day > q_max_dks:
                q_total_day = q_max_dks
                q_monthly = q_total_day * days / 1e6
            n_dks = n_dks_max
        else:
            n_dks = DKS.power_calc(q_total_day / 1e6, p_u, p_vyh_dks, t_pl, rho_otn)

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

    monthly_df = pd.DataFrame(monthly_rows)
    if monthly_df.empty:
        wells_schedule, recovery_schedule = _build_output_schedules(params)
        return {
            "monthly_df": [],
            "yearly_df": [],
            "params": params,
            "warning": warning_message,
            "wells_schedule": wells_schedule,
            "recovery_schedule": recovery_schedule,
        }

    yearly_df = monthly_df.groupby("Год", as_index=False).agg(
        {
            "Количество скважин": "max",
            "Целевой темп отбора, %": "mean",
            "Целевая добыча, млрд м³/год": "mean",
            "Добыча газа, млрд м³/мес": "sum",
            "Накоплено, млрд м³": "last",
            "P_пл, МПа": "mean",
            "Темп отбора, %": "mean",
            "Мощность ДКС, МВт": "mean",
            "На полке": "max",
        }
    )
    yearly_df = yearly_df.rename(
        columns={
            "Добыча газа, млрд м³/мес": "Добыча газа, млрд м³/год",
            "P_пл, МПа": "Среднее P_пл, МПа",
            "Темп отбора, %": "Средний темп отбора, %",
            "Мощность ДКС, МВт": "Средняя мощность ДКС, МВт",
        }
    )
    yearly_df["Год"] = yearly_df["Год"].astype(int)
    yearly_df["На полке"] = yearly_df["На полке"].astype(int)

    wells_schedule, recovery_schedule = _build_output_schedules(params)
    plateau_years = int(yearly_df[yearly_df["На полке"] == 1]["Год"].count())

    return {
        "monthly_df": monthly_df.to_dict("records"),
        "yearly_df": yearly_df.to_dict("records"),
        "params": params,
        "G_nach": g_nach / 1e9,
        "plateau_level": round(plateau_level, 3),
        "plateau_years": plateau_years,
        "optimal_rate": actual_recovery_rate if plateau_mode == "auto" else None,
        "warning": warning_message,
        "wells_schedule": wells_schedule,
        "recovery_schedule": recovery_schedule,
    }
