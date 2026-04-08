import dash
from dash import dcc, html
import plotly.graph_objs as go
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

def create_charts_tab(results, colors):
    if not results or 'monthly_df' not in results or 'yearly_df' not in results:
        return html.Div("Нет данных. Выполните расчет.",
                        style={'textAlign': 'center', 'marginTop': 50, 'color': colors['danger']})

    monthly_df = pd.DataFrame(results['monthly_df'])
    yearly_df = pd.DataFrame(results['yearly_df'])

    if len(yearly_df) == 0:
        return html.Div("Нет данных для отображения",
                        style={'textAlign': 'center', 'marginTop': 50, 'color': colors['warning']})

    # Находим уровень полки
    plateau_level = find_plateau_level(yearly_df)
    plateau_year = None
    for _, row in yearly_df.iterrows():
        if row['Добыча газа, млрд м³/год'] >= plateau_level * 0.95:
            plateau_year = row['Год']
            break

    # Год начала падения
    decline_start_year = None
    found_plateau = False
    for _, row in yearly_df.iterrows():
        if not found_plateau and row['Добыча газа, млрд м³/год'] >= plateau_level * 0.99:
            found_plateau = True
        elif found_plateau and row['Добыча газа, млрд м³/год'] < plateau_level * 0.99:
            decline_start_year = row['Год']
            break

    # Конечный КИГ
    initial_gas = results.get(
        'G_nach', yearly_df['Накоплено, млрд м³'].iloc[0])
    total_produced = yearly_df['Накоплено, млрд м³'].iloc[-1]
    recovery_factor = min(
        (total_produced / initial_gas * 100), 100) if initial_gas > 0 else 0

    # График 1: Профиль добычи газа (линия с точками + накопленная на второй оси)
    fig = go.Figure()

    # Годовая добыча - ЛИНИЯ С ТОЧКАМИ
    fig.add_trace(go.Scatter(
        x=yearly_df['Год'],
        y=yearly_df['Добыча газа, млрд м³/год'],
        mode='lines+markers',
        name='Годовая добыча',
        line=dict(color=colors['primary'], width=2.5),
        marker=dict(size=8, color=colors['primary'], symbol='circle'),
        text=yearly_df['Добыча газа, млрд м³/год'].round(1),
        textposition='top center',
        yaxis='y1'
    ))

    # Линия полки
    fig.add_trace(go.Scatter(
        x=[yearly_df['Год'].min(), yearly_df['Год'].max()],
        y=[plateau_level, plateau_level],
        mode='lines',
        name=f'Полка: {plateau_level:.1f} млрд м³/год',
        line=dict(color=colors['success'], width=2, dash='dash'),
        yaxis='y1'
    ))

    # Накопленная добыча (вторая ось)
    fig.add_trace(go.Scatter(
        x=yearly_df['Год'],
        y=yearly_df['Накоплено, млрд м³'],
        mode='lines+markers',
        name='Накопленная добыча',
        line=dict(color=colors['danger'], width=2),
        marker=dict(size=4, color=colors['danger']),
        yaxis='y2'
    ))

    fig.update_layout(
        title='Профиль добычи газа',
        xaxis=dict(title='Год', tickangle=-45),
        yaxis=dict(
            title='Добыча газа, млрд м³/год',
            titlefont=dict(color=colors['primary']),
            tickfont=dict(color='black')
        ),
        yaxis2=dict(
            title='Накопленная добыча, млрд м³',
            titlefont=dict(color=colors['danger']),
            tickfont=dict(color='black'),
            overlaying='y',
            side='right'
        ),
        plot_bgcolor='white',
        hovermode='x unified',
        legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.8)')
    )

    return html.Div([
        # Информационная панель
        html.Div([
            html.H2("Ключевые показатели", style={
                    'marginTop': 20, 'marginBottom': 10}),
            html.Div([
                html.Div([
                    html.Div("Полка добычи", style={
                             'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{plateau_level:.1f} млрд м³/год",
                             style={'fontSize': '20px', 'fontWeight': 'bold', 'color': colors['success']})
                ], style={'display': 'inline-block', 'marginRight': 40}),
                html.Div([
                    html.Div("Год выхода на полку", style={
                             'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{plateau_year}",
                             style={'fontSize': '20px', 'fontWeight': 'bold', 'color': colors['primary']})
                ], style={'display': 'inline-block', 'marginRight': 40}),
                html.Div([
                    html.Div("Год начала падения", style={
                             'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{decline_start_year if decline_start_year else '—'}",
                             style={'fontSize': '20px', 'fontWeight': 'bold', 'color': colors['warning']})
                ], style={'display': 'inline-block', 'marginRight': 40}),
                html.Div([
                    html.Div("Конечный КИГ", style={
                             'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{recovery_factor:.1f}%",
                             style={'fontSize': '20px', 'fontWeight': 'bold', 'color': colors['danger']})
                ], style={'display': 'inline-block'}),
            ], style={'padding': '15px', 'backgroundColor': "#ffffff", 'borderRadius': '8px', 'marginBottom': 10}),

            html.Div([
                html.Div([
                    html.Div("Начальные запасы", style={
                             'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{initial_gas:.0f} млрд м³",
                             style={'fontSize': '16px', 'fontWeight': 'bold'})
                ], style={'display': 'inline-block', 'marginRight': 40}),
                html.Div([
                    html.Div("Накопленная добыча", style={
                             'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{total_produced:.1f} млрд м³",
                             style={'fontSize': '16px', 'fontWeight': 'bold'})
                ], style={'display': 'inline-block', 'marginRight': 40}),
                html.Div([
                    html.Div("Остаточные запасы", style={
                             'fontSize': '12px', 'color': '#666'}),
                    html.Div(f"{max(0, initial_gas - total_produced):.1f} млрд м³",
                             style={'fontSize': '16px', 'fontWeight': 'bold'})
                ], style={'display': 'inline-block'}),
            ], style={'padding': '15px', 'backgroundColor': "#ffffff", 'borderRadius': '8px', 'marginBottom': 30,
                      'borderTop': f'1px solid {colors["background"]}'})
        ]),


        html.H2("Интерактивные графики", style={'marginBottom': 20}),

        dcc.Graph(figure=fig),

        # График 2: Падение пластового давления
        dcc.Graph(
            figure={
                'data': [go.Scatter(
                    x=yearly_df['Год'],
                    y=yearly_df['Среднее P_пл, МПа'],
                    mode='lines+markers',
                    name='Пластовое давление',
                    line=dict(color=colors['danger'], width=2),
                    marker=dict(size=6),
                    fill='tozeroy',
                    fillcolor='rgba(231, 76, 60, 0.1)'
                )],
                'layout': go.Layout(
                    title='Падение пластового давления',
                    xaxis=dict(title='Год'),
                    yaxis=dict(title='Давление, МПа'),
                    plot_bgcolor='white',
                    hovermode='x'
                )
            }
        ),

        # График 3: Темпы отбора
        dcc.Graph(
            figure={
                'data': [go.Scatter(
                    x=yearly_df['Год'],
                    y=yearly_df['Средний темп отбора, %'],
                    mode='lines+markers',
                    name='Темп отбора',
                    line=dict(color=colors['success'], width=2),
                    marker=dict(size=6),
                    fill='tozeroy',
                    fillcolor='rgba(39, 174, 96, 0.2)'
                )],
                'layout': go.Layout(
                    title='Темпы отбора',
                    xaxis=dict(title='Год'),
                    yaxis=dict(title='Темп отбора, %', range=[0, max(
                        20, yearly_df['Средний темп отбора, %'].max() + 2)]),
                    plot_bgcolor='white',
                    hovermode='x'
                )
            }
        ),

        # График 4: Мощность ДКС
        dcc.Graph(
            figure={
                'data': [go.Scatter(
                    x=yearly_df['Год'],
                    y=yearly_df['Средняя мощность ДКС, МВт'],
                    mode='lines+markers',
                    name='Мощность ДКС',
                    line=dict(color=colors['primary'], width=2),
                    marker=dict(size=6)
                )],
                'layout': go.Layout(
                    title='Мощность ДКС',
                    xaxis=dict(title='Год'),
                    yaxis=dict(title='Мощность, МВт'),
                    plot_bgcolor='white',
                    hovermode='x'
                )
            }
        ),

        # График 5: Динамика водогазового фактора
        dcc.Graph(
            figure={
                'data': [go.Scatter(
                    x=monthly_df['Дата'],
                    y=monthly_df['ВГФ, г/м³'],
                    mode='lines',
                    name='ВГФ',
                    line=dict(color=colors['warning'], width=2),
                    fill='tozeroy',
                    fillcolor='rgba(230, 126, 34, 0.2)'
                )],
                'layout': go.Layout(
                    title='Динамика водогазового фактора',
                    xaxis=dict(title='Год'),
                    yaxis=dict(title='ВГФ, г/м³'),
                    plot_bgcolor='white',
                    hovermode='x'
                )
            }
        ),
    ])
