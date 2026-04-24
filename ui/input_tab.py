import dash
from dash import dcc, html
import dash.dash_table as dt

from calculations.scenario import RECOVERY_RATE_COLUMN, WELLS_COLUMN, build_yearly_schedule


def _build_schedule_data(params, schedule_key, value_column, default_value, cast_type=float):
    return build_yearly_schedule(
        start_year=params.get("start_year", 2025),
        horizon_years=params.get("T_max", 35),
        default_value=default_value,
        value_column=value_column,
        raw_schedule=params.get(schedule_key),
        minimum_value=0,
        cast_type=cast_type,
    )


def _card_style():
    return {
        "backgroundColor": "white",
        "borderRadius": "12px",
        "border": "1px solid #e2e8f0",
        "padding": "20px",
        "marginBottom": "20px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.05)",
    }


def _input_style():
    return {
        "width": "100%",
        "padding": "8px 12px",
        "border": "1px solid #e2e8f0",
        "borderRadius": "8px",
        "fontSize": "14px",
        "backgroundColor": "#f8fafc",
    }


def _label(text):
    return html.Label(
        text,
        style={"fontSize": "12px", "color": "#666", "marginBottom": "4px", "display": "block"},
    )


def create_input_tab(params, colors, mode="simple"):
    """Создает вкладку ввода параметров в современном стиле."""

    wells_table_data = _build_schedule_data(
        params,
        schedule_key="wells_schedule",
        value_column=WELLS_COLUMN,
        default_value=params.get("N_skv", 10),
        cast_type=int,
    )
    recovery_table_data = _build_schedule_data(
        params,
        schedule_key="recovery_schedule",
        value_column=RECOVERY_RATE_COLUMN,
        default_value=params.get("target_recovery_rate", 1.5),
        cast_type=float,
    )

    advanced_blocks = []
    if mode == "advanced":
        advanced_blocks = [
            html.Div([
                html.Div([
                    html.I(className="fas fa-layer-group", style={"marginRight": "10px"}),
                    html.H3("Количество скважин по годам",
                            style={"fontSize": "16px", "fontWeight": "600", "margin": 0}),
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),
                html.P(
                    "Основные параметры считаются по средней скважине. Здесь задается только количество работающих скважин по годам. Последнее заданное значение автоматически переносится на следующие годы до нового изменения.",
                    style={"fontSize": "12px", "color": "#666", "marginBottom": "12px"},
                ),
                dt.DataTable(
                    id="wells-table",
                    columns=[
                        {"name": "Год", "id": "Год", "type": "numeric"},
                        {"name": WELLS_COLUMN, "id": WELLS_COLUMN, "type": "numeric", "editable": True},
                    ],
                    data=wells_table_data,
                    editable=True,
                    style_table={"width": "100%", "maxHeight": "360px", "overflowY": "auto"},
                    style_cell={"textAlign": "center", "padding": "8px", "border": "1px solid #e2e8f0"},
                    style_header={"backgroundColor": "#f8fafc", "fontWeight": "bold"},
                ),
            ], style=_card_style()),
            html.Div([
                html.Div([
                    html.I(className="fas fa-percentage", style={"marginRight": "10px"}),
                    html.H3("Темп отбора по годам (%)",
                            style={"fontSize": "16px", "fontWeight": "600", "margin": 0}),
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),
                html.P(
                    "Если целевой годовой темп отбора должен меняться по годам, задай его здесь. Последнее заданное значение автоматически переносится на следующие годы до нового изменения.",
                    style={"fontSize": "12px", "color": "#666", "marginBottom": "12px"},
                ),
                dt.DataTable(
                    id="recovery-rate-table",
                    columns=[
                        {"name": "Год", "id": "Год", "type": "numeric"},
                        {"name": RECOVERY_RATE_COLUMN, "id": RECOVERY_RATE_COLUMN, "type": "numeric", "editable": True},
                    ],
                    data=recovery_table_data,
                    editable=True,
                    style_table={"width": "100%", "maxHeight": "360px", "overflowY": "auto"},
                    style_cell={"textAlign": "center", "padding": "8px", "border": "1px solid #e2e8f0"},
                    style_header={"backgroundColor": "#f8fafc", "fontWeight": "bold"},
                ),
            ], style=_card_style()),
        ]

    return html.Div([
        html.Div([
            html.Div([
                html.I(className="fas fa-mountain", style={"marginRight": "10px"}),
                html.H3("Пластовые параметры", style={"fontSize": "16px", "fontWeight": "600", "margin": 0}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),
            html.Div([
                html.Div([
                    html.Div([
                        _label("Начальное пластовое давление (МПа)"),
                        dcc.Input(id="input-P_pl", type="number", value=params.get("P_pl", 25), step=0.5, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Пластовая температура (°C)"),
                        dcc.Input(id="input-T_pl", type="number", value=params.get("T_pl", 80), step=1, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Начальные запасы (млрд м³)"),
                        dcc.Input(id="input-G_nach", type="number", value=params.get("G_nach", 100), step=10, style=_input_style()),
                    ], style={"flex": 1}),
                ], style={"display": "flex", "marginBottom": "12px"}),
                html.Div([
                    html.Div([
                        _label("Относительная плотность газа"),
                        dcc.Input(id="input-rho_otn", type="number", value=params.get("rho_otn", 0.6), step=0.05, style=_input_style()),
                    ], style={"flex": 1}),
                ], style={"display": "flex"}),
            ]),
        ], style=_card_style()),

        html.Div([
            html.Div([
                html.I(className="fas fa-oil-can", style={"marginRight": "10px"}),
                html.H3("Параметры скважины", style={"fontSize": "16px", "fontWeight": "600", "margin": 0}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),
            html.Div([
                html.Div([
                    html.Div([
                        _label("Количество скважин (шт)"),
                        dcc.Input(id="input-N_skv", type="number", value=params.get("N_skv", 10), step=1, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Глубина скважины (м)"),
                        dcc.Input(id="input-H_skv", type="number", value=params.get("H_skv", 2500), step=100, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Диаметр НКТ (мм)"),
                        dcc.Input(id="input-d_NKT", type="number", value=params.get("d_NKT", 100), step=10, style=_input_style()),
                    ], style={"flex": 1}),
                ], style={"display": "flex", "marginBottom": "12px"}),
                html.Div([
                    html.Div([
                        _label("Коэффициент a"),
                        dcc.Input(id="input-a_coef", type="number", value=params.get("a_coef", 0.15), step=0.05, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Коэффициент b"),
                        dcc.Input(id="input-b_coef", type="number", value=params.get("b_coef", 0.0003), step=0.00005, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Макс. депрессия (МПа)"),
                        dcc.Input(id="input-dP_max", type="number", value=params.get("dP_max", 10), step=1, style=_input_style()),
                    ], style={"flex": 1}),
                ], style={"display": "flex", "marginBottom": "12px"}),
                html.Div([
                    html.Div([
                        _label("Коэффициент эксплуатации"),
                        dcc.Input(id="input-K_eks", type="number", value=params.get("K_eks", 0.95), step=0.02, style=_input_style()),
                    ], style={"flex": 1}),
                ], style={"display": "flex"}),
            ]),
        ], style=_card_style()),

        html.Div([
            html.Div([
                html.I(className="fas fa-chart-line", style={"marginRight": "10px"}),
                html.H3("Параметры прогноза", style={"fontSize": "16px", "fontWeight": "600", "margin": 0}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),
            html.Div([
                html.Div([
                    _label("Режим полки"),
                    dcc.RadioItems(
                        id="input-plateau_mode",
                        options=[
                            {"label": " Максимально длинная полка", "value": "auto"},
                            {"label": " Заданный темп отбора", "value": "manual"},
                        ],
                        value=params.get("plateau_mode", "auto"),
                        inline=False,
                        style={"marginBottom": "12px"},
                    ),
                ]),
                html.Div([
                    html.Div([
                        _label("Целевой темп отбора (% в год)"),
                        dcc.Input(
                            id="input-target_recovery_rate",
                            type="number",
                            value=params.get("target_recovery_rate", 8),
                            step=0.5,
                            style=_input_style(),
                        ),
                    ], style={"marginBottom": "12px"}),
                    html.Div([
                        _label("Полка вручную (млрд м³/год, 0 = по темпу)"),
                        dcc.Input(id="input-Q_polka", type="number", value=params.get("Q_polka", 0), step=0.5, style=_input_style()),
                    ], style={"marginBottom": "12px"}),
                ]),
            ]),
        ], style=_card_style()),

        html.Div([
            html.Div([
                html.I(className="fas fa-industry", style={"marginRight": "10px"}),
                html.H3("Дожимная компрессорная станция", style={"fontSize": "16px", "fontWeight": "600", "margin": 0}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),
            html.Div([
                html.Div([
                    _label("Режим работы ДКС"),
                    dcc.Dropdown(
                        id="input-DKS_mode",
                        options=[
                            {"label": "Расчетный", "value": "расчетный"},
                            {"label": "Ограничительный", "value": "ограничительный"},
                        ],
                        value=params.get("DKS_mode", "расчетный"),
                        style={"width": "100%", "border": "1px solid #e2e8f0", "borderRadius": "8px"},
                    ),
                ], style={"marginBottom": "12px"}),
                html.Div([
                    html.Div([
                        _label("Давление на входе (МПа)"),
                        dcc.Input(id="input-P_vh_DKS", type="number", value=params.get("P_vh_DKS", 5), step=0.5, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Давление на выходе (МПа)"),
                        dcc.Input(id="input-P_vyh_DKS", type="number", value=params.get("P_vyh_DKS", 7.5), step=0.5, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Мощность ДКС (МВт)"),
                        dcc.Input(id="input-N_DKS", type="number", value=params.get("N_DKS", 50), step=10, style=_input_style()),
                    ], style={"flex": 1}),
                ], style={"display": "flex"}),
            ]),
        ], style=_card_style()),

        html.Div([
            html.Div([
                html.I(className="fas fa-water", style={"marginRight": "10px"}),
                html.H3("Обводнение", style={"fontSize": "16px", "fontWeight": "600", "margin": 0}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),
            html.Div([
                html.Div([
                    html.Div([
                        _label("Начальный ВГФ (г/м³)"),
                        dcc.Input(id="input-VGF_nach", type="number", value=params.get("VGF_nach", 0), step=1, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Интенсивность роста ВГФ (г/м³)"),
                        dcc.Input(id="input-dVGF_dG", type="number", value=params.get("dVGF_dG", 10), step=1, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Критический ВГФ (г/м³)"),
                        dcc.Input(id="input-VGF_krit", type="number", value=params.get("VGF_krit", 200), step=10, style=_input_style()),
                    ], style={"flex": 1}),
                ], style={"display": "flex"}),
            ]),
        ], style=_card_style()),

        html.Div([
            html.Div([
                html.I(className="fas fa-calendar", style={"marginRight": "10px"}),
                html.H3("Временные параметры", style={"fontSize": "16px", "fontWeight": "600", "margin": 0}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),
            html.Div([
                html.Div([
                    html.Div([
                        _label("Год начала разработки"),
                        dcc.Input(id="input-start_year", type="number", value=params.get("start_year", 2025), step=1, style=_input_style()),
                    ], style={"flex": 1, "marginRight": "12px"}),
                    html.Div([
                        _label("Горизонт прогноза (лет)"),
                        dcc.Input(id="input-T_max", type="number", value=params.get("T_max", 35), step=1, style=_input_style()),
                    ], style={"flex": 1}),
                ], style={"display": "flex"}),
            ]),
        ], style=_card_style()),

        *advanced_blocks,
    ], style={"padding": "0"})
