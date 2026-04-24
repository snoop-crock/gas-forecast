from __future__ import annotations

from typing import Any


YEAR_COLUMN = "Год"
WELLS_COLUMN = "Количество скважин"
RECOVERY_RATE_COLUMN = "Темп отбора (%)"


def _to_int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cast_schedule_value(value: float, cast_type: type) -> float | int:
    return cast_type(round(value)) if cast_type is int else cast_type(value)


def build_yearly_schedule(
    start_year: int,
    horizon_years: int,
    default_value: float,
    value_column: str,
    raw_schedule: list[dict[str, Any]] | None = None,
    minimum_value: float = 0,
    cast_type: type = float,
) -> list[dict[str, float | int]]:
    years = list(range(int(start_year), int(start_year) + max(int(horizon_years), 0)))
    if not years:
        return []

    normalized_default = _cast_schedule_value(max(default_value, minimum_value), cast_type)
    normalized_changes: dict[int, float | int] = {}

    for item in raw_schedule or []:
        year = _to_int(item.get(YEAR_COLUMN))
        value = _to_float(item.get(value_column))
        if year is None or year not in years or value is None:
            continue
        normalized_changes[year] = _cast_schedule_value(max(value, minimum_value), cast_type)

    current_value = normalized_default
    schedule_rows: list[dict[str, float | int]] = []
    for year in years:
        if year in normalized_changes:
            current_value = normalized_changes[year]
        schedule_rows.append({YEAR_COLUMN: year, value_column: current_value})

    return schedule_rows


def schedule_to_year_map(
    raw_schedule: list[dict[str, Any]] | None,
    start_year: int,
    horizon_years: int,
    default_value: float,
    value_column: str,
    minimum_value: float = 0,
    cast_type: type = float,
) -> dict[int, float | int]:
    schedule_rows = build_yearly_schedule(
        start_year=start_year,
        horizon_years=horizon_years,
        default_value=default_value,
        value_column=value_column,
        raw_schedule=raw_schedule,
        minimum_value=minimum_value,
        cast_type=cast_type,
    )
    return {int(item[YEAR_COLUMN]): item[value_column] for item in schedule_rows}


def validate_forecast_params(params: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    validators = [
        (params.get("P_pl", 0) > 0, "Начальное пластовое давление должно быть > 0"),
        (params.get("T_pl", 0) > 0, "Пластовая температура должна быть > 0"),
        (params.get("G_nach", 0) > 0, "Начальные запасы должны быть > 0"),
        (0 < params.get("rho_otn", 0) < 1, "Относительная плотность газа должна быть между 0 и 1"),
        (params.get("N_skv", 0) > 0, "Количество скважин должно быть > 0"),
        (params.get("H_skv", 0) > 0, "Глубина скважин должна быть > 0"),
        (params.get("T_max", 0) > 0, "Горизонт прогноза должен быть > 0"),
        (params.get("start_year", 0) > 1900, "Год начала разработки указан некорректно"),
        (0 < params.get("K_eks", 0) <= 1, "Коэффициент эксплуатации должен быть в диапазоне (0; 1]"),
        (params.get("d_NKT", 0) > 0, "Диаметр НКТ должен быть > 0"),
        (params.get("dP_max", 0) > 0, "Максимальная депрессия должна быть > 0"),
    ]

    for is_valid, message in validators:
        if not is_valid:
            errors.append(message)

    schedule_configs = [
        ("wells_schedule", WELLS_COLUMN, 0, "Сценарий по скважинам"),
        ("recovery_schedule", RECOVERY_RATE_COLUMN, 0, "Сценарий по темпам отбора"),
    ]

    for schedule_key, value_column, minimum_value, label in schedule_configs:
        for row in params.get(schedule_key, []) or []:
            year = _to_int(row.get(YEAR_COLUMN))
            value = _to_float(row.get(value_column))

            if year is None:
                errors.append(f"{label}: у каждой строки должен быть указан год")
                break
            if value is None:
                errors.append(f"{label}: у каждой строки должно быть указано значение")
                break
            if value < minimum_value:
                errors.append(f"{label}: значения не могут быть меньше {minimum_value}")
                break

    return errors
