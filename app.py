import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import pandas as pd
import os
import json

from calculations import calculate_forecast, default_params, validate_forecast_params
from ui.excel_export import export_to_excel
from ui.input_tab import create_input_tab
from ui.results_tab import create_results_tab
from ui.charts_tab import create_charts_tab
from ui.options_tab import create_options_tab
from ui.instructions_tab import create_instructions_tab

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Газовый расчетник"

# Цветовая схема
colors = {
    'background': '#f8fafc',
    'card': '#ffffff',
    'primary': "#0747d0",
    'primary_hover': "#c300ff",
    'accent': "#ff9913",
    'success': '#10b981',
    'danger': '#ef4444',
    'warning': "#e2bc12",
    'text': '#1f2937',
    'text_secondary': '#6b7280',
    'border': '#e5e7eb'
}

# ==================== КАСТОМНЫЙ HTML ШАБЛОН С CSS ====================
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Газовый расчетник</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        {%favicon%}
        {%css%}
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #f8fafc;
                color: #1f2937;
            }
            
            /* ========== HEADER ========== */
            .header {
                background: linear-gradient(135deg, #0f172a, #1e293b);
                border-bottom: 1px solid #334155;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .header-content {
                max-width: 1280px;
                margin: 0 auto;
                padding: 16px 24px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 16px;
            }
            
            .logo-container {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .logo-icon {
                width: 44px;
                height: 44px;
                background: #faae19;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 22px;
                font-weight: 700;
                color: white;
            }
            
            .logo-title {
                font-size: 20px;
                font-weight: 700;
                color: white;
                margin: 0;
                letter-spacing: -0.3px;
            }
            
            .logo-subtitle {
                font-size: 12px;
                color: #94a3b8;
                margin: 2px 0 0 0;
            }
            
            .header-buttons {
                display: flex;
                gap: 12px;
            }
            
            /* ========== КНОПКИ ========== */
            .btn-primary {
                background: #faae19;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 40px;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .btn-primary:hover {
                background: #0f5fd4;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(25, 117, 250, 0.3);
            }
            
            .btn-secondary {
                background: transparent;
                border: 1px solid #475569;
                color: #cbd5e1;
                padding: 8px 20px;
                border-radius: 40px;
                font-weight: 500;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .btn-secondary:hover {
                border-color: #faae19;
                color: #faae19;
            }
            
            .btn-success {
                background: transparent;
                border: 1px solid #475569;
                color: #cbd5e1;
                padding: 8px 20px;
                border-radius: 40px;
                font-weight: 500;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .btn-success:hover {
                border-color: #10b981;
                color: #10b981;
            }
            
            /* ========== TOGGLE SWITCH ========== */
            .toggle-container {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 16px;
            }
            
            .toggle-switch {
                position: relative;
                width: 60px;
                height: 30px;
                background: #475569;
                border-radius: 15px;
                cursor: pointer;
                transition: background 0.3s;
            }
            
            .toggle-switch.active {
                background: #faae19;
            }
            
            .toggle-slider {
                position: absolute;
                top: 2px;
                left: 2px;
                width: 26px;
                height: 26px;
                background: white;
                border-radius: 50%;
                transition: transform 0.3s;
            }
            
            .toggle-switch.active .toggle-slider {
                transform: translateX(30px);
            }
            
            .toggle-label {
                font-size: 14px;
                font-weight: 500;
                color: white;
                cursor: pointer;
            }
            

            /* ========== TOGGLE SWITCH ========== */
            .toggle-container {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 16px;
            }
            
            .toggle-switch {
                position: relative;
                width: 60px;
                height: 30px;
                background: #475569;
                border-radius: 15px;
                cursor: pointer;
                transition: background 0.3s;
            }
            
            .toggle-switch.active {
                background: #faae19;
            }
            
            .toggle-slider {
                position: absolute;
                top: 2px;
                left: 2px;
                width: 26px;
                height: 26px;
                background: white;
                border-radius: 50%;
                transition: transform 0.3s;
            }
            
            .toggle-switch.active .toggle-slider {
                transform: translateX(30px);
            }
            
            .toggle-label {
                font-size: 14px;
                font-weight: 500;
                color: white;
                cursor: pointer;
            }
            
            /* ========== MAIN ========== */

            .main-container {
                max-width: 1280px;
                margin: 0 auto;
                padding: 24px;
            }
            
            /* ========== TABS ========== */
            .custom-tabs {
                background: white;
                border-radius: 16px;
                border: 1px solid #e5e7eb;
                padding: 4px;
                margin-bottom: 24px;
                display: flex;
            }
            
            .custom-tab {
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 500;
                color: #6b7280;
                border-radius: 12px;
                transition: all 0.2s;
                background: transparent;
                border: none;
                cursor: pointer;
            }
            
            .custom-tab:hover {
                color: #faae19;
                background: #eef4ff;
            }
            
            .custom-tab-selected,
            .custom-tab.selected {
                background: transparent !important;
                border: none !important;
                border-bottom: none !important;
                border-top: 2px solid #faae19 !important;
                color: #666 !important;
                border-radius: 0 !important;
                padding-top: 8px !important;
            }
            
            .tabs-content {
                background: transparent;
                padding: 0;
            }
            

            /* ========== СОРТИРОВКА ТАБЛИЦЫ ========== */
            .sortable-header {
                transition: background-color 0.2s;
            }

            .sortable-header:hover {
                background-color: #eef4ff !important;
            }

            .sortable-header:active {
                background-color: #dbeafe !important;
            }
            /* ========== TOAST ========== */
            .toast-hidden {
                display: none;
            }
            
            .toast-success, .toast-error, .toast-warning {
                position: fixed;
                bottom: 30px;
                right: 30px;
                z-index: 9999;
                min-width: 320px;
                padding: 14px 20px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                font-weight: 500;
                font-size: 14px;
                display: block;
                animation: slideIn 0.3s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            .toast-success {
                background: #f0fdf4;
                border-left: 4px solid #10b981;
                color: #1f2937;
            }
            
            .toast-error {
                background: #fef2f2;
                border-left: 4px solid #ef4444;
                color: #1f2937;
            }
            
            .toast-warning {
                background: #fffbeb;
                border-left: 4px solid #f59e0b;
                color: #1f2937;
            }
            
            /* ========== INPUT FIELDS ========== */
            input, .Select-control {
                border-radius: 8px !important;
                border: 1px solid #e5e7eb !important;
                background: #ffffff !important;
                font-size: 14px !important;
                transition: all 0.2s;
            }
            
            input:focus, .Select-control:focus {
                border-color: #faae19 !important;
                outline: none !important;
                box-shadow: 0 0 0 3px rgba(25, 117, 250, 0.1) !important;
            }
            
            /* Убираем красную обводку для поля "Коэффициент эксплуатации" */
            input:invalid, input:out-of-range {
                border-color: #e5e7eb !important;
                box-shadow: none !important;
            }
            
            /* ========== CARDS ========== */
            .stat-card {
                background: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
                padding: 16px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }
            
            .stat-card-dark {
                background: linear-gradient(135deg, #1e293b, #0f172a);
                border-radius: 12px;
                padding: 16px;
                color: white;
            }
            
            /* ========== RESPONSIVE ========== */
            @media (max-width: 768px) {
                .header-content {
                    flex-direction: column;
                    align-items: flex-start;
                }
                
                .header-buttons {
                    width: 100%;
                    justify-content: flex-start;
                }
                
                .main-container {
                    padding: 16px;
                }
                
                .custom-tab {
                    padding: 8px 16px;
                    font-size: 12px;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


app.layout = html.Div([
    # Header с кнопками
    html.Div([
        html.Div([
            html.Div([
                html.Div("Г", className="logo-icon"),
                html.Div([
                    html.H1("Газовый Расчётник", className="logo-title"),
                    html.P("Прогноз добычи газа - упрощенный вариант", id='logo-subtitle', className="logo-subtitle")
                ])
            ], className="logo-container"),

            # Выбор режима
            html.Div([
                html.Label("Режим расчета:", style={'fontSize': '14px', 'fontWeight': '500', 'marginBottom': '8px', 'display': 'block', 'color': 'white'}),
                html.Div([
                    html.Span("Упрощенный", className="toggle-label", id="toggle-simple", n_clicks=0),
                    html.Div([
                        html.Div(className="toggle-slider", id="toggle-slider")
                    ], className="toggle-switch", id="toggle-switch", n_clicks=0),
                    html.Span("Усложненный", className="toggle-label", id="toggle-advanced", n_clicks=0)
                ], className="toggle-container")
            ], style={'marginBottom': '20px'}),

            html.Div([
                html.Button("Рассчитать", id='btn-calculate',
                            n_clicks=0, className="btn-primary"),
                html.Button("Сбросить", id='btn-reset',
                            n_clicks=0, className="btn-secondary"),
                html.Button("Экспорт в Excel", id='btn-export',
                            n_clicks=0, className="btn-success"),
                # html.Button("Экспорт в PDF", id='btn-export-pdf',
                #             n_clicks=0, className="btn-success"),
            ], className="header-buttons")
        ], className="header-content")
    ], className="header"),

    # Контент
    html.Div([
        dcc.Tabs(id='tabs', value='tab-input', className="custom-tabs", children=[
            dcc.Tab(label='Параметры', value='tab-input',
                    className="custom-tab", selected_className="custom-tab-selected"),
            dcc.Tab(label='Расчёты', value='tab-calc', className="custom-tab",
                    selected_className="custom-tab-selected"),
            dcc.Tab(label='Графики', value='tab-charts',
                    className="custom-tab", selected_className="custom-tab-selected"),
            dcc.Tab(label='Опции', value='tab-options',
                    className="custom-tab", selected_className="custom-tab-selected"),
            dcc.Tab(label='Справка', value='tab-instructions',
                    className="custom-tab", selected_className="custom-tab-selected"),
        ]),

        html.Div(id='tabs-content', className="tabs-content"),

        dcc.Store(id='store-params', data=default_params.copy()),
        dcc.Store(id='store-results', data={}),
        dcc.Store(id='store-mode', data='simple'),
        dcc.Store(id='toast-control',
                  data={'show': False, 'message': '', 'type': 'success'}),
        dcc.Store(id='table-sort-column', data=None),
        dcc.Store(id='table-sort-direction', data='asc'),
        dcc.Store(id='period-selector-store', data='monthly'),
        dcc.Store(id='period-store', data='monthly'),

        dcc.Download(id='download-excel'),

        dcc.Download(id='download-pdf'),

        # Toast уведомление
        html.Div(id='toast', className="toast-hidden", children=[]),
        dcc.Interval(id='toast-timer', interval=3000,
                     n_intervals=0, disabled=True),

    ], className="main-container")
], className="app-container")


# ==================== ФУНКЦИЯ ПОКАЗА TOAST ====================
def show_toast(message, type='success'):
    colors_toast = {
        'success': {'class': 'toast-success', 'icon': '✅'},
        'error': {'class': 'toast-error', 'icon': '❌'},
        'warning': {'class': 'toast-warning', 'icon': '⚠️'}
    }

    return {
        'className': colors_toast[type]['class'],
        'children': html.Div([
            html.Span(colors_toast[type]['icon'], style={
                      'marginRight': '12px', 'fontSize': '16px'}),
            html.Span(message, style={'fontSize': '14px'})
        ])
    }


# ==================== TOAST КОЛБЭК ====================
@app.callback(
    [Output('toast', 'className'),
     Output('toast', 'children'),
     Output('toast-timer', 'disabled'),
     Output('toast-timer', 'n_intervals')],
    [Input('toast-control', 'data'),
     Input('toast-timer', 'n_intervals')],
    prevent_initial_call=True
)
def update_toast(toast_control, n_intervals):
    ctx = callback_context
    if not ctx.triggered:
        return 'toast-hidden', [], True, 0

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'toast-timer':
        return 'toast-hidden', [], True, 0

    if triggered_id == 'toast-control' and toast_control.get('show', False):
        result = show_toast(
            toast_control.get('message', ''),
            toast_control.get('type', 'success')
        )
        return result['className'], result['children'], False, 0

    return 'toast-hidden', [], True, 0


# ==================== ПЕРЕКЛЮЧЕНИЕ РЕЖИМА ====================
@app.callback(
    [Output('store-mode', 'data'),
     Output('toggle-switch', 'className')],
    [Input('toggle-simple', 'n_clicks'),
     Input('toggle-advanced', 'n_clicks'),
     Input('toggle-switch', 'n_clicks')],
    [State('store-mode', 'data')]
)
def toggle_mode(simple_clicks, advanced_clicks, switch_clicks, current_mode):
    ctx = callback_context
    if not ctx.triggered:
        class_name = "toggle-switch active" if current_mode == 'advanced' else "toggle-switch"
        return current_mode or 'simple', class_name
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == 'toggle-simple':
        return 'simple', "toggle-switch"
    elif triggered_id == 'toggle-advanced':
        return 'advanced', "toggle-switch active"
    elif triggered_id == 'toggle-switch':
        next_mode = 'simple' if current_mode == 'advanced' else 'advanced'
        return next_mode, ("toggle-switch active" if next_mode == 'advanced' else "toggle-switch")
    
    return current_mode or 'simple', "toggle-switch"

# ==================== ОБНОВЛЕНИЕ ПОДЗАГОЛОВКА ====================
@app.callback(
    Output('logo-subtitle', 'children'),
    Input('store-mode', 'data')
)
def update_subtitle(mode):
    if mode == 'advanced':
        return 'Прогноз добычи газа - усложненный вариант'
    else:
        return 'Прогноз добычи газа - упрощенный вариант'


# ==================== РЕНДЕР ВКЛАДОК ====================
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_tab(tab):
    if tab == 'tab-input':
        return html.Div(id='input-tab-container')
    elif tab == 'tab-calc':
        return html.Div([html.Div(id='results-tab-container')])
    elif tab == 'tab-charts':
        return html.Div([html.Div(id='charts-tab-container')])
    elif tab == 'tab-options':
        return html.Div(id='options-tab-container')
    else:
        return html.Div(id='instructions-tab-container')


# ==================== ЗАГРУЗКА ВКЛАДОК ====================
@app.callback(
    Output('input-tab-container', 'children'),
    [Input('store-params', 'data'),
     Input('store-mode', 'data')]
)
def load_input_tab(params, mode):
    return create_input_tab(params, colors, mode)


@app.callback(
    Output('options-tab-container', 'children'),
    Input('store-params', 'data')
)
def load_options_tab(params):
    return create_options_tab(params, colors)


@app.callback(
    Output('instructions-tab-container', 'children'),
    Input('tabs', 'value')
)
def load_instructions_tab(tab):
    if tab == 'tab-instructions':
        return create_instructions_tab(colors)
    return dash.no_update


@app.callback(
    Output('results-tab-container', 'children'),
    [Input('store-results', 'data'),
     Input('period-selector-store', 'data')]
)
def load_results_tab(results, period):
    print(f"load_results_tab: results={'есть' if results else 'нет'}") 
    return create_results_tab(results, colors, period)


@app.callback(
    Output('charts-tab-container', 'children'),
    Input('store-results', 'data')
)
def load_charts_tab(results):
    return create_charts_tab(results, colors)


# ==================== СОХРАНЕНИЕ ПЕРИОДА ====================
@app.callback(
    Output('period-selector-store', 'data'),
    Input('period-selector', 'value'),
    prevent_initial_call=True
)
def save_period(period):
    return period


# ==================== СПИСОК ID ПОЛЕЙ ВВОДА ====================
INPUT_IDS = [
    'input-start_year', 'input-T_max', 'input-Q_polka', 'input-plateau_mode',
    'input-target_recovery_rate',
    'input-P_pl', 'input-T_pl', 'input-G_nach', 'input-rho_otn',
    'input-N_skv', 'input-H_skv', 'input-d_NKT',
    'input-a_coef', 'input-b_coef', 'input-dP_max', 'input-K_eks',
    'input-DKS_mode', 'input-P_vh_DKS', 'input-P_vyh_DKS', 'input-N_DKS',
    'input-VGF_nach', 'input-dVGF_dG', 'input-VGF_krit'
]

INPUT_PARAM_MAPPING = {
    'input-start_year': 'start_year',
    'input-T_max': 'T_max',
    'input-Q_polka': 'Q_polka',
    'input-plateau_mode': 'plateau_mode',
    'input-target_recovery_rate': 'target_recovery_rate',
    'input-P_pl': 'P_pl',
    'input-T_pl': 'T_pl',
    'input-G_nach': 'G_nach',
    'input-rho_otn': 'rho_otn',
    'input-N_skv': 'N_skv',
    'input-H_skv': 'H_skv',
    'input-d_NKT': 'd_NKT',
    'input-a_coef': 'a_coef',
    'input-b_coef': 'b_coef',
    'input-dP_max': 'dP_max',
    'input-K_eks': 'K_eks',
    'input-DKS_mode': 'DKS_mode',
    'input-P_vh_DKS': 'P_vh_DKS',
    'input-P_vyh_DKS': 'P_vyh_DKS',
    'input-N_DKS': 'N_DKS',
    'input-VGF_nach': 'VGF_nach',
    'input-dVGF_dG': 'dVGF_dG',
    'input-VGF_krit': 'VGF_krit'
}


def build_calc_params(params):
    merged = default_params.copy()
    if params:
        merged.update(params)

    calc_params = {param_name: merged.get(param_name, default_value) for param_name, default_value in default_params.items()}
    calc_params['wells_schedule'] = merged.get('wells_schedule', [])
    calc_params['recovery_schedule'] = merged.get('recovery_schedule', [])
    return calc_params


# ==================== КНОПКА СБРОСА ====================
@app.callback(
    [Output('store-params', 'data', allow_duplicate=True)] +
    [Output(id, 'value') for id in INPUT_IDS],
    Input('btn-reset', 'n_clicks'),
    prevent_initial_call=True
)
def reset_params(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return [dash.no_update] * (len(INPUT_IDS) + 1)

    results = [default_params.copy()]
    for input_id in INPUT_IDS:
        param_name = input_id.replace('input-', '')
        if param_name in default_params:
            results.append(default_params[param_name])
        else:
            results.append(None)

    return results


# ==================== СОХРАНЕНИЕ ОПЦИЙ ====================
@app.callback(
    Output('store-params', 'data', allow_duplicate=True),
    [Input('opt-friction', 'value'),
     Input('opt-pvt_method', 'value')],
    [State('store-params', 'data')],
    prevent_initial_call=True
)
def update_options(opt_friction, opt_pvt_method, current_params):
    if current_params is None:
        current_params = default_params.copy()
    else:
        current_params = current_params.copy()

    if opt_friction is not None:
        current_params['opt_friction'] = opt_friction
    if opt_pvt_method is not None:
        current_params['pvt_method'] = opt_pvt_method

    return current_params


# ==================== СИНХРОНИЗАЦИЯ ПОЛЕЙ ====================
@app.callback(
    Output('store-params', 'data', allow_duplicate=True),
    [Input(id, 'value') for id in INPUT_IDS],
    [State('store-params', 'data')],
    prevent_initial_call=True
)
def sync_inputs_to_store(*args):
    current_params = args[-1]
    if current_params is None:
        current_params = default_params.copy()
    else:
        current_params = current_params.copy()

    for i, input_id in enumerate(INPUT_IDS):
        value = args[i]
        if value is not None:
            param_name = INPUT_PARAM_MAPPING.get(input_id)
            if param_name:
                current_params[param_name] = value

    return current_params


# ==================== СОХРАНЕНИЕ ДАННЫХ ИЗ ТАБЛИЦ ====================
@app.callback(
    Output('store-params', 'data', allow_duplicate=True),
    [Input('wells-table', 'data'),
     Input('recovery-rate-table', 'data')],
    [State('store-params', 'data')],
    prevent_initial_call=True
)
def sync_table_data(wells_data, recovery_data, current_params):
    if current_params is None:
        current_params = default_params.copy()
    else:
        current_params = current_params.copy()

    if wells_data:
        current_params['wells_schedule'] = wells_data
    if recovery_data:
        current_params['recovery_schedule'] = recovery_data

    return current_params


# ==================== КНОПКА РАСЧЕТА ====================
@app.callback(
    [Output('store-results', 'data'),
     Output('toast-control', 'data')],
    Input('btn-calculate', 'n_clicks'),
    [State('store-params', 'data')],
    prevent_initial_call=True
)
def run_calculation(n_clicks, params):
    if n_clicks is None or n_clicks == 0:
        return {}, {'show': False, 'message': '', 'type': 'success'}

    if params is None:
        params = default_params.copy()

    # Валидация параметров
    validation_errors = []
    if params.get('P_pl', 0) <= 0:
        validation_errors.append("Начальное пластовое давление должно быть > 0")
    if params.get('T_pl', 0) <= 0:
        validation_errors.append("Пластовая температура должна быть > 0")
    if params.get('G_nach', 0) <= 0:
        validation_errors.append("Начальные запасы должны быть > 0")
    if not (0 < params.get('rho_otn', 0) < 1):
        validation_errors.append("Относительная плотность газа должна быть между 0 и 1")
    if params.get('N_skv', 0) <= 0:
        validation_errors.append("Количество скважин должно быть > 0")
    if params.get('H_skv', 0) <= 0:
        validation_errors.append("Глубина скважин должна быть > 0")
    if params.get('K_eks', 0) <= 0 or params.get('K_eks', 0) > 1:
        validation_errors.append("Коэффициент эксплуатации должен быть между 0 и 1")

    if validation_errors:
        return {}, {'show': True, 'message': 'Ошибки валидации: ' + '; '.join(validation_errors), 'type': 'error'}

    calc_params = {
        'start_year': params.get('start_year', 2025),
        'T_max': params.get('T_max', 35),
        'Q_polka': params.get('Q_polka', 0),
        'plateau_mode': params.get('plateau_mode', 'auto'),
        'target_recovery_rate': params.get('target_recovery_rate', 8),
        'P_pl': params.get('P_pl', 25),
        'T_pl': params.get('T_pl', 80),
        'G_nach': params.get('G_nach', 100),
        'rho_otn': params.get('rho_otn', 0.6),
        'N_skv': params.get('N_skv', 10),
        'H_skv': params.get('H_skv', 2500),
        'd_NKT': params.get('d_NKT', 100),
        'a_coef': params.get('a_coef', 0.15),
        'b_coef': params.get('b_coef', 0.0003),
        'dP_max': params.get('dP_max', 10),
        'K_eks': params.get('K_eks', 0.95),
        'DKS_mode': params.get('DKS_mode', 'расчетный'),
        'P_vh_DKS': params.get('P_vh_DKS', 5),
        'P_vyh_DKS': params.get('P_vyh_DKS', 7.5),
        'N_DKS': params.get('N_DKS', 50),
        'VGF_nach': params.get('VGF_nach', 0),
        'dVGF_dG': params.get('dVGF_dG', 10),
        'VGF_krit': params.get('VGF_krit', 200),
        'opt_friction': params.get('opt_friction', 1),
        'pvt_method': params.get('pvt_method', 'latonov'),
        'wells_schedule': params.get('wells_schedule', []),
        'recovery_schedule': params.get('recovery_schedule', [])
    }

    try:
        results = calculate_forecast(calc_params)
        return results, {'show': True, 'message': 'Расчёт выполнен успешно! Результаты готовы.', 'type': 'success'}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {}, {'show': True, 'message': f'Ошибка: {str(e)}', 'type': 'error'}

# ==================== ТАБЛИЦА С СОРТИРОВКОЙ И ИНДИКАТОРАМИ ====================
@app.callback(
    Output('table-container', 'children'),
    [Input('period-store', 'data'),
     Input('store-results', 'data'),
     Input('table-sort-column', 'data'),
     Input('table-sort-direction', 'data')],
    prevent_initial_call=True
)
def update_table(period, results, sort_column, sort_direction):
    if not results or 'monthly_df' not in results:
        return html.Div("Нет данных. Выполните расчет.", 
                        style={'textAlign': 'center', 'padding': '50px', 'color': '#f59e0b'})

    if period == 'yearly':
        df = pd.DataFrame(results['yearly_df'])
        df['Год'] = df['Год'].astype(int)
        df['Добыча газа, млрд м³/год'] = df['Добыча газа, млрд м³/год'].round(3)
        df['Накоплено, млрд м³'] = df['Накоплено, млрд м³'].round(3)
        df['Среднее P_пл, МПа'] = df['Среднее P_пл, МПа'].round(3)
        df['Средний темп отбора, %'] = df['Средний темп отбора, %'].round(3)
        df['Средняя мощность ДКС, МВт'] = df['Средняя мощность ДКС, МВт'].round(3)
        df['На полке'] = df['На полке'].astype(int)
    else:
        df = pd.DataFrame(results['monthly_df'])
        df['Год'] = df['Год'].astype(int)
        df['P_пл, МПа'] = df['P_пл, МПа'].round(3)
        df['Добыча газа, млрд м³/мес'] = df['Добыча газа, млрд м³/мес'].round(3)
        df['Накоплено, млрд м³'] = df['Накоплено, млрд м³'].round(3)
        df['Остаток, млрд м³'] = df['Остаток, млрд м³'].round(3)
        df['Темп отбора, %'] = df['Темп отбора, %'].round(3)
        df['P_у, МПа'] = df['P_у, МПа'].round(3)
        df['P_заб, МПа'] = df['P_заб, МПа'].round(3)
        df['ВГФ, г/м³'] = df['ВГФ, г/м³'].round(3)
        df['Добыча воды, тыс. м³/мес'] = df['Добыча воды, тыс. м³/мес'].round(3)
        df['Мощность ДКС, МВт'] = df['Мощность ДКС, МВт'].round(3)
        df['На полке'] = df['На полке'].astype(int)

    # Сортировка
    if sort_column and sort_column in df.columns:
        ascending = (sort_direction == 'asc')
        df = df.sort_values(by=sort_column, ascending=ascending)

    df_display = df

    # Функция для отображения индикатора сортировки
    def get_sort_indicator(col):
        if sort_column == col:
            return " ▲" if sort_direction == 'asc' else " ▼"
        return " ↕️"

    return html.Div([
        html.Div([
            html.I(className="fas fa-info-circle", style={'marginRight': '8px', 'color': '#666'}),
            html.Span("Кликните по заголовку колонки для сортировки", 
                      style={'fontSize': '12px', 'color': '#666'})
        ], style={'marginBottom': '10px', 'padding': '8px', 'backgroundColor': '#f0f9ff', 'borderRadius': '8px'}),
        
        html.Table([
            html.Thead([
                html.Tr([
                    html.Th(
                        html.Div([
                            html.Span(col, style={'marginRight': '8px'}),
                            html.Span(get_sort_indicator(col), 
                                      style={'fontSize': '10px', 'color': '#1975FA' if sort_column == col else '#aaa'})
                        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),
                        id={'type': 'sort-header', 'index': col},
                        style={
                            'padding': '12px',
                            'border': '1px solid #e5e7eb',
                            'backgroundColor': '#f8fafc',
                            'fontWeight': '600',
                            'fontSize': '12px',
                            'color': '#1f2937',
                            'cursor': 'pointer',
                            'userSelect': 'none',
                            'position': 'sticky',
                            'top': 0,
                            'textAlign': 'left'
                        },
                        n_clicks=0
                    ) for col in df_display.columns
                ])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(str(row[col]), style={
                            'padding': '10px', 
                            'border': '1px solid #e5e7eb', 
                            'fontSize': '12px'
                    })
                    for col in df_display.columns
                ])
                for _, row in df_display.iterrows()
            ])
        ], style={
            'borderCollapse': 'collapse', 
            'width': '100%', 
            'borderRadius': '8px', 
            'overflow': 'hidden',
            'display': 'block',
            'overflowX': 'auto'
        })
    ], style={'overflowX': 'auto', 'maxHeight': '600px', 'overflowY': 'auto'})

# ==================== ПЕРЕКЛЮЧЕНИЕ МЕЖДУ МЕСЯЧНЫМ И ГОДОВЫМ ====================
@app.callback(
    [Output('period-store', 'data'),
     Output('btn-monthly', 'style'),
     Output('btn-yearly', 'style')],
    [Input('btn-monthly', 'n_clicks'),
     Input('btn-yearly', 'n_clicks')],
    prevent_initial_call=True
)
def switch_period(monthly_clicks, yearly_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return 'monthly', _btn_style('monthly', True), _btn_style('yearly', False)
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'btn-monthly':
        return 'monthly', _btn_style('monthly', True), _btn_style('yearly', False)
    else:
        return 'yearly', _btn_style('monthly', False), _btn_style('yearly', True)


def _btn_style(period, is_active):
    """Стиль для кнопок переключения"""
    if is_active:
        return {
            'backgroundColor': '#faae19',
            'color': 'white',
            'border': 'none',
            'padding': '8px 24px',
            'borderRadius': '8px 0 0 8px' if period == 'monthly' else '0 8px 8px 0',
            'cursor': 'pointer',
            'fontWeight': '500',
            'transition': 'all 0.2s'
        }
    else:
        return {
            'backgroundColor': '#e0e0e0',
            'color': '#333',
            'border': 'none',
            'padding': '8px 24px',
            'borderRadius': '8px 0 0 8px' if period == 'monthly' else '0 8px 8px 0',
            'cursor': 'pointer',
            'fontWeight': '500',
            'transition': 'all 0.2s'
        }


# ==================== СОРТИРОВКА ТАБЛИЦЫ ====================
@app.callback(
    [Output('table-sort-column', 'data'),
     Output('table-sort-direction', 'data')],
    [Input({'type': 'sort-header', 'index': dash.ALL}, 'n_clicks')],
    [State('table-sort-column', 'data'),
     State('table-sort-direction', 'data')],
    prevent_initial_call=True
)
def handle_sort_click(n_clicks_list, current_column, current_direction):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    triggered_id = ctx.triggered[0]['prop_id']
    try:
        prop_parts = triggered_id.split('.')
        if len(prop_parts) > 0:
            id_str = prop_parts[0]
            id_dict = json.loads(id_str.replace("'", '"'))
            clicked_column = id_dict.get('index')
        else:
            return dash.no_update, dash.no_update
    except:
        return dash.no_update, dash.no_update

    if clicked_column == current_column:
        new_direction = 'desc' if current_direction == 'asc' else 'asc'
    else:
        new_direction = 'asc'

    return clicked_column, new_direction


# ==================== ЭКСПОРТ В EXCEL ====================
@app.callback(
    Output('download-excel', 'data'),
    Input('btn-export', 'n_clicks'),
    State('store-results', 'data'),
    prevent_initial_call=True
)
def export_excel(n_clicks, results):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update
    if not results:
        print("Нет данных для экспорта")
        return dash.no_update
    try:
        filepath = export_to_excel(results)
        with open(filepath, 'rb') as f:
            content = f.read()
        return dcc.send_bytes(content, filename=os.path.basename(filepath))
    except Exception as e:
        print(f"Ошибка экспорта: {e}")
        return dash.no_update


# ==================== ЗАГРУЗКА ДАННЫХ В ТАБЛИЦЫ ПРИ ПЕРЕКЛЮЧЕНИИ РЕЖИМА ====================
@app.callback(
    [Output('wells-table', 'data', allow_duplicate=True),
     Output('recovery-rate-table', 'data', allow_duplicate=True)],
    [Input('store-mode', 'data'),
     Input('store-params', 'data')],
    prevent_initial_call=True
)
def load_tables_on_mode_change(mode, params):
    """При переключении на усложненный режим загружает данные из store-params в таблицы"""
    if mode != 'advanced':
        return dash.no_update, dash.no_update
    
    if params is None:
        params = default_params.copy()
    
    wells = params.get('wells_schedule', [])
    recovery = params.get('recovery_schedule', [])
    
    # Если нет данных, создаем начальную строку
    if not wells:
        wells = [{"Год": params.get('start_year', 2025), "Количество скважин": params.get('N_skv', 10)}]
    if not recovery:
        recovery = [{"Год": params.get('start_year', 2025), "Темп отбора (%)": params.get('target_recovery_rate', 1.5)}]
    
    return wells, recovery


# # ==================== СОХРАНЕНИЕ ТАБЛИЦЫ СКВАЖИН В STORE ====================
# @app.callback(
#     Output('store-params', 'data', allow_duplicate=True),
#     Input('wells-table', 'data'),
#     [State('store-params', 'data')],
#     prevent_initial_call=True
# )
# def save_wells_table(wells_data, current_params):
#     if wells_data is None:
#         return dash.no_update
#     if current_params is None:
#         current_params = default_params.copy()
#     else:
#         current_params = current_params.copy()
#     current_params['wells_schedule'] = wells_data
#     print(f"✅ Сохранены скважины: {len(wells_data)} записей")
#     return current_params


# # ==================== СОХРАНЕНИЕ ТАБЛИЦЫ ТЕМПА ОТБОРА В STORE ====================
# @app.callback(
#     Output('store-params', 'data', allow_duplicate=True),
#     Input('recovery-rate-table', 'data'),
#     [State('store-params', 'data')],
#     prevent_initial_call=True
# )
# def save_recovery_table(recovery_data, current_params):
#     if recovery_data is None:
#         return dash.no_update
#     if current_params is None:
#         current_params = default_params.copy()
#     else:
#         current_params = current_params.copy()
#     current_params['recovery_schedule'] = recovery_data
#     print(f"✅ Сохранен темп отбора: {len(recovery_data)} записей")
#     return current_params


# ==================== ДОБАВЛЕНИЕ/УДАЛЕНИЕ СТРОК В ТАБЛИЦАХ ====================
# @app.callback(
#     Output('wells-table', 'data', allow_duplicate=True),
#     Input('btn-add-wells-row', 'n_clicks'),
#     State('wells-table', 'data'),
#     prevent_initial_call=True
# )
# def add_wells_row(n_clicks, current_data):
#     if n_clicks is None or n_clicks == 0:
#         return dash.no_update
#     if current_data is None:
#         current_data = []
#     if current_data:
#         last_year = current_data[-1].get('Год', 2025)
#         last_value = current_data[-1].get('Количество скважин', 10)
#         new_row = {'Год': last_year + 1, 'Количество скважин': last_value}
#         return current_data + [new_row]
#     return [{'Год': 2025, 'Количество скважин': 10}]


# @app.callback(
#     Output('recovery-rate-table', 'data', allow_duplicate=True),
#     Input('btn-add-recovery-row', 'n_clicks'),
#     State('recovery-rate-table', 'data'),
#     prevent_initial_call=True
# )
# def add_recovery_row(n_clicks, current_data):
#     if n_clicks is None or n_clicks == 0:
#         return dash.no_update
#     if current_data is None:
#         current_data = []
#     if current_data:
#         last_year = current_data[-1].get('Год', 2025)
#         last_value = current_data[-1].get('Темп отбора (%)', 1.5)
#         new_row = {'Год': last_year + 1, 'Темп отбора (%)': last_value}
#         return current_data + [new_row]
#     return [{'Год': 2025, 'Темп отбора (%)': 1.5}]

if __name__ == '__main__':
    app.run_server(debug=True)
