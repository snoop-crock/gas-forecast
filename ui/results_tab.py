import dash
from dash import dcc, html
import pandas as pd

def find_plateau_level(yearly_df):
    """
    Определяет уровень полки как среднее значение за 3 последовательных года
    с минимальным отклонением (истинное плато, а не случайный пик)
    """
    if len(yearly_df) < 3:
        return yearly_df['Добыча газа, млрд м³/год'].max()
    
    best_plateau = 0
    best_std = float('inf')
    
    # Ищем 3 последовательных года с минимальным стандартным отклонением
    for i in range(len(yearly_df) - 2):
        window = yearly_df.iloc[i:i+3]['Добыча газа, млрд м³/год']
        mean = window.mean()
        std = window.std()
        
        # Чем меньше отклонение, тем стабильнее полка
        if std < best_std and mean > 0:
            best_std = std
            best_plateau = mean
    
    # Если нашли стабильный участок — это полка
    if best_plateau > 0 and best_std < 0.1:  # отклонение менее 0.1 млрд м³/год
        return round(best_plateau, 2)
    
    # Иначе берем максимальное значение за первые 5 лет
    early_years = yearly_df.head(min(5, len(yearly_df)))
    return round(early_years['Добыча газа, млрд м³/год'].max(), 2)

def create_results_tab(results, colors, period='monthly'):
    """
    Создает вкладку с результатами
    """
    if not results or 'monthly_df' not in results:
        return html.Div(
            "Нет данных. Выполните расчет на вкладке 'Ввод параметров'.",
            style={'textAlign': 'center', 'marginTop': 50,
                   'color': colors['danger'], 'fontSize': '16px'}
        )

    monthly_df = pd.DataFrame(results['monthly_df'])
    yearly_df = pd.DataFrame(results['yearly_df'])

    if len(yearly_df) == 0:
        return html.Div("Нет данных для отображения",
                        style={'textAlign': 'center', 'marginTop': 50, 'color': colors['danger']})

    # ========== ФОРМАТИРОВАНИЕ ДАННЫХ ==========
    # Год в int (целое число)
    yearly_df['Год'] = yearly_df['Год'].astype(int)
    monthly_df['Год'] = monthly_df['Год'].astype(int)
    
    # Округление годовых данных (3 знака после запятой)
    yearly_df['Добыча газа, млрд м³/год'] = yearly_df['Добыча газа, млрд м³/год'].round(3)
    yearly_df['Накоплено, млрд м³'] = yearly_df['Накоплено, млрд м³'].round(3)
    yearly_df['Среднее P_пл, МПа'] = yearly_df['Среднее P_пл, МПа'].round(3)
    yearly_df['Средний темп отбора, %'] = yearly_df['Средний темп отбора, %'].round(3)
    yearly_df['Средняя мощность ДКС, МВт'] = yearly_df['Средняя мощность ДКС, МВт'].round(3)
    yearly_df['На полке'] = yearly_df['На полке'].astype(int)
    
    # Округление помесячных данных (3 знака после запятой)
    monthly_df['P_пл, МПа'] = monthly_df['P_пл, МПа'].round(3)
    monthly_df['Добыча газа, млрд м³/мес'] = monthly_df['Добыча газа, млрд м³/мес'].round(3)
    monthly_df['Накоплено, млрд м³'] = monthly_df['Накоплено, млрд м³'].round(3)
    monthly_df['Остаток, млрд м³'] = monthly_df['Остаток, млрд м³'].round(3)
    monthly_df['Темп отбора, %'] = monthly_df['Темп отбора, %'].round(3)
    monthly_df['P_у, МПа'] = monthly_df['P_у, МПа'].round(3)
    monthly_df['P_заб, МПа'] = monthly_df['P_заб, МПа'].round(3)
    monthly_df['ВГФ, г/м³'] = monthly_df['ВГФ, г/м³'].round(3)
    monthly_df['Добыча воды, тыс. м³/мес'] = monthly_df['Добыча воды, тыс. м³/мес'].round(3)
    monthly_df['Мощность ДКС, МВт'] = monthly_df['Мощность ДКС, МВт'].round(3)
    monthly_df['На полке'] = monthly_df['На полке'].astype(int)

    # ========== СТАТИСТИКА ==========
    max_gas = find_plateau_level(yearly_df)
    plateau_year = None
    for _, row in yearly_df.iterrows():
        if row['Добыча газа, млрд м³/год'] >= max_gas * 0.95:
            plateau_year = row['Год']
            break
    total_produced = yearly_df['Накоплено, млрд м³'].iloc[-1]
    initial_gas = results.get('G_nach', yearly_df['Накоплено, млрд м³'].iloc[0])
    recovery_factor = min((total_produced / initial_gas * 100), 100) if initial_gas > 0 else 0

    # Год начала падения
    plateau_level = max_gas
    decline_start_year = None
    plateau_started = False
    plateau_count = 0
    for _, row in yearly_df.iterrows():
        if row['Добыча газа, млрд м³/год'] >= plateau_level * 0.95:
            plateau_started = True
            plateau_count += 1
        elif plateau_started and plateau_count >= 2:
            decline_start_year = row['Год']
            break

    return html.Div([

        # ========== КРАТКАЯ СТАТИСТИКА ==========
        html.Div([
            html.H3("Ключевые показатели", style={'marginTop': 20, 'marginBottom': 10}),
            html.Div([
                html.Div([
                    html.Div("Полка добычи", style={'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{max_gas:.3f} млрд м³/год",
                             style={'fontSize': '18px', 'fontWeight': 'bold', 'color': colors['success']})
                ], style={'display': 'inline-block', 'marginRight': 40}),
                html.Div([
                    html.Div("Год выхода на полку", style={'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{plateau_year}",
                             style={'fontSize': '18px', 'fontWeight': 'bold', 'color': colors['primary']})
                ], style={'display': 'inline-block', 'marginRight': 40}),
                html.Div([
                    html.Div("Год начала падения", style={'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{decline_start_year if decline_start_year else '—'}",
                             style={'fontSize': '18px', 'fontWeight': 'bold', 'color': colors['warning']})
                ], style={'display': 'inline-block', 'marginRight': 40}),
                html.Div([
                    html.Div("Конечный КИГ", style={'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{recovery_factor:.1f}%",
                             style={'fontSize': '18px', 'fontWeight': 'bold', 'color': colors['danger']})
                ], style={'display': 'inline-block'}),
            ], style={'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': 10, 'marginBottom': 20}),
        ]),

        # ========== ПОШАГОВЫЕ РЕЗУЛЬТАТЫ ==========
        html.H3("Пошаговые результаты", style={'marginBottom': 20}),

        # Кнопки переключения между месячным и годовым
        html.Div([
            html.Button(
                "📅 Помесячно", 
                id='btn-monthly',
                n_clicks=0,
                style={
                    'backgroundColor': '#1975FA' if period == 'monthly' else '#e0e0e0',
                    'color': 'white' if period == 'monthly' else '#333',
                    'border': 'none',
                    'padding': '8px 24px',
                    'borderRadius': '8px 0 0 8px',
                    'cursor': 'pointer',
                    'fontWeight': '500',
                    'transition': 'all 0.2s'
                }
            ),
            html.Button(
                "📆 По годам", 
                id='btn-yearly',
                n_clicks=0,
                style={
                    'backgroundColor': '#1975FA' if period == 'yearly' else '#e0e0e0',
                    'color': 'white' if period == 'yearly' else '#333',
                    'border': 'none',
                    'padding': '8px 24px',
                    'borderRadius': '0 8px 8px 0',
                    'cursor': 'pointer',
                    'fontWeight': '500',
                    'transition': 'all 0.2s'
                }
            ),
        ], style={'marginBottom': 20, 'display': 'inline-flex'}),

        # Контейнер для таблицы
        html.Div(id='table-container', style={'marginTop': 20}),

        # Скрытое хранилище для выбранного периода
        dcc.Store(id='period-store', data=period),

    ])