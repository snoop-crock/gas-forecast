import dash
from dash import dcc, html
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd

def find_plateau_level(yearly_df):
    """Определяет уровень полки"""
    if len(yearly_df) < 3:
        return yearly_df['Добыча газа, млрд м³/год'].max()
    
    best_plateau = 0
    best_std = float('inf')
    
    for i in range(len(yearly_df) - 2):
        window = yearly_df.iloc[i:i+3]['Добыча газа, млрд м³/год']
        mean = window.mean()
        std = window.std()
        
        if std < best_std and mean > 0:
            best_std = std
            best_plateau = mean
    
    if best_plateau > 0 and best_std < 0.1:
        return round(best_plateau, 2)
    
    early_years = yearly_df.head(min(5, len(yearly_df)))
    return round(early_years['Добыча газа, млрд м³/год'].max(), 2)

def create_charts_tab(results, colors):
    if not results or 'monthly_df' not in results:
        return html.Div(
            "Нет данных. Выполните расчет.",
            style={'textAlign': 'center', 'marginTop': 50, 'color': '#ef4444', 'fontSize': '16px'}
        )

    monthly_df = pd.DataFrame(results['monthly_df'])
    
    # Создаём yearly_df
    if 'yearly_df' in results and results['yearly_df']:
        yearly_df = pd.DataFrame(results['yearly_df'])
    else:
        yearly_df = monthly_df.groupby('Год', as_index=False).agg({
            'Добыча газа, млрд м³/мес': 'sum',
            'Накоплено, млрд м³': 'last',
            'КИГ, %': 'last',
        }).rename(columns={'Добыча газа, млрд м³/мес': 'Добыча газа, млрд м³/год'})
        
        # Добавляем давления из monthly_df
        if 'P_пл, МПа' in monthly_df.columns:
            yearly_df['P_пл, МПа'] = monthly_df.groupby('Год')['P_пл, МПа'].mean().values
        if 'P_заб, МПа' in monthly_df.columns:
            yearly_df['P_заб, МПа'] = monthly_df.groupby('Год')['P_заб, МПа'].mean().values
        if 'P_у, МПа' in monthly_df.columns:
            yearly_df['P_у, МПа'] = monthly_df.groupby('Год')['P_у, МПа'].mean().values
        if 'P_вх_ДКС, МПа' in monthly_df.columns:
            yearly_df['P_вх_ДКС, МПа'] = monthly_df.groupby('Год')['P_вх_ДКС, МПа'].mean().values

    if yearly_df.empty:
        return html.Div(
            "Нет данных для отображения",
            style={'textAlign': 'center', 'marginTop': 50, 'color': '#f59e0b'}
        )

    # Определяем колонки
    pressure_col = None
    for col in ['Среднее P_пл, МПа', 'P_пл, МПа', 'Среднее P_пл, бар', 'P_пл, бар']:
        if col in yearly_df.columns:
            pressure_col = col
            break
    
    # Определяем колонки для давлений (поддержка разных форматов)
    p_res_col = None
    p_wf_col = None
    p_wh_col = None
    p_inlet_col = None
    
    for col in ['P_пл, МПа', 'Среднее P_пл, МПа', 'P_пл, бар', 'Среднее P_пл, бар']:
        if col in yearly_df.columns:
            p_res_col = col
            break
    
    for col in ['P_заб, МПа', 'Среднее P_заб, МПа', 'P_заб, бар']:
        if col in yearly_df.columns:
            p_wf_col = col
            break
    
    for col in ['P_у, МПа', 'Среднее P_у, МПа', 'P_у, бар']:
        if col in yearly_df.columns:
            p_wh_col = col
            break
    
    for col in ['P_вх_ДКС, МПа', 'P_вх_ДКС, бар']:
        if col in yearly_df.columns:
            p_inlet_col = col
            break
    
    power_col = None
    for col in ['Средняя мощность ДКС, МВт', 'Мощность ДКС, МВт']:
        if col in yearly_df.columns:
            power_col = col
            break

    # Определяем единицы измерения (бары или МПа)
    if p_res_col and 'бар' in p_res_col:
        pressure_unit = 'бар'
        pressure_title = 'Давление, бар'
    else:
        pressure_unit = 'МПа'
        pressure_title = 'Давление, МПа'

    # ==================== ГРАФИК 1: ПРОФИЛЬ ДОБЫЧИ ====================
    fig1 = go.Figure()

    fig1.add_trace(go.Scatter(
        x=yearly_df['Год'],
        y=yearly_df['Добыча газа, млрд м³/год'],
        mode='lines+markers',
        name='Годовая добыча',
        line=dict(color='#3b82f6', width=3, shape='spline'),
        marker=dict(size=10, color='#3b82f6', symbol='circle', line=dict(width=2, color='white')),
        hovertemplate='<b>%{x} г.</b><br>Добыча: %{y:.2f} млрд м³<extra></extra>'
    ))

    fig1.add_trace(go.Scatter(
        x=yearly_df['Год'],
        y=yearly_df['Накоплено, млрд м³'],
        mode='lines+markers',
        name='Накопленная добыча',
        line=dict(color='#ef4444', width=3, shape='spline', dash='dot'),
        marker=dict(size=8, color='#ef4444', symbol='diamond'),
        yaxis='y2',
        hovertemplate='<b>%{x} г.</b><br>Накоплено: %{y:.1f} млрд м³<extra></extra>'
    ))

    fig1.update_layout(
        title=dict(text='<b>Профиль добычи газа</b>', x=0.05, xanchor='left', font=dict(size=20, color='#1f2937')),
        xaxis=dict(title='<b>Год</b>', tickangle=-45, showgrid=True, gridcolor='#e5e7eb'),
        yaxis=dict(title='<b>Добыча, млрд м³/год</b>', titlefont=dict(color='#3b82f6'), tickfont=dict(color='#3b82f6')),
        yaxis2=dict(title='<b>Накоплено, млрд м³</b>', titlefont=dict(color='#ef4444'), tickfont=dict(color='#ef4444'),
                    overlaying='y', side='right', showgrid=False),
        plot_bgcolor='white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, bgcolor='rgba(255,255,255,0.9)'),
        margin=dict(l=60, r=60, t=80, b=50),
        template='plotly_white'
    )

    # ==================== ГРАФИК 2: ВСЕ ДАВЛЕНИЯ (ПЛАСТОВОЕ, ЗАБОЙНОЕ, УСТЬЕВОЕ) ====================
    fig2 = go.Figure()

    colors_pressure = ['#8b5cf6', '#ec4899', '#f59e0b', '#06b6d4']
    
    if p_res_col:
        fig2.add_trace(go.Scatter(
            x=yearly_df['Год'],
            y=yearly_df[p_res_col],
            mode='lines+markers',
            name='Пластовое давление (P_пл)',
            line=dict(color=colors_pressure[0], width=3, shape='spline'),
            marker=dict(size=8, color=colors_pressure[0], symbol='circle'),
            # fill='tonexty',
            hovertemplate=f'<b>%{{x}} г.</b><br>P_пл: %{{y:.1f}} {pressure_unit}<extra></extra>'
        ))
    
    if p_wf_col:
        fig2.add_trace(go.Scatter(
            x=yearly_df['Год'],
            y=yearly_df[p_wf_col],
            mode='lines+markers',
            name='Забойное давление (P_заб)',
            line=dict(color=colors_pressure[1], width=3, shape='spline', dash='dash'),
            marker=dict(size=8, color=colors_pressure[1], symbol='square'),
            hovertemplate=f'<b>%{{x}} г.</b><br>P_заб: %{{y:.1f}} {pressure_unit}<extra></extra>'
        ))
    
    if p_wh_col:
        fig2.add_trace(go.Scatter(
            x=yearly_df['Год'],
            y=yearly_df[p_wh_col],
            mode='lines+markers',
            name='Устьевое давление (P_у)',
            line=dict(color=colors_pressure[2], width=3, shape='spline', dash='dot'),
            marker=dict(size=8, color=colors_pressure[2], symbol='diamond'),
            hovertemplate=f'<b>%{{x}} г.</b><br>P_у: %{{y:.1f}} {pressure_unit}<extra></extra>'
        ))
    
    if p_inlet_col:
        fig2.add_trace(go.Scatter(
            x=yearly_df['Год'],
            y=yearly_df[p_inlet_col],
            mode='lines+markers',
            name='Давление на входе ДКС (P_вх)',
            line=dict(color=colors_pressure[3], width=3, shape='spline', dash='dashdot'),
            marker=dict(size=8, color=colors_pressure[3], symbol='cross'),
            hovertemplate=f'<b>%{{x}} г.</b><br>P_вх_ДКС: %{{y:.1f}} {pressure_unit}<extra></extra>'
        ))

    fig2.update_layout(
        title=dict(text='<b>Динамика давлений</b>', x=0.05, xanchor='left', font=dict(size=20, color='#1f2937')),
        xaxis=dict(title='<b>Год</b>', tickangle=-45, showgrid=True, gridcolor='#e5e7eb'),
        yaxis=dict(title=f'<b>{pressure_title}</b>', showgrid=True, gridcolor='#e5e7eb'),
        plot_bgcolor='white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, bgcolor='rgba(255,255,255,0.9)'),
        margin=dict(l=60, r=40, t=80, b=50),
        template='plotly_white'
    )

    # ==================== ГРАФИК 3: КИГ ====================
    fig3 = go.Figure()

    fig3.add_trace(go.Scatter(
        x=yearly_df['Год'],
        y=yearly_df['КИГ, %'],
        mode='lines+markers',
        name='КИГ',
        line=dict(color='#10b981', width=3, shape='spline'),
        marker=dict(size=10, color='#10b981', symbol='circle', line=dict(width=2, color='white')),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.15)',
        hovertemplate='<b>%{x} г.</b><br>КИГ: %{y:.1f}%<extra></extra>'
    ))

    fig3.add_hline(y=100, line_dash="dash", line_color="#9ca3af", opacity=0.5, 
                   annotation_text="100%", annotation_position="bottom right")

    fig3.update_layout(
        title=dict(text='<b>Коэффициент извлечения газа (КИГ)</b>', x=0.05, xanchor='left', font=dict(size=20, color='#1f2937')),
        xaxis=dict(title='<b>Год</b>', tickangle=-45, showgrid=True, gridcolor='#e5e7eb'),
        yaxis=dict(title='<b>КИГ, %</b>', titlefont=dict(color='#10b981'), tickfont=dict(color='#10b981'),
                   range=[0, 100], showgrid=True, gridcolor='#e5e7eb'),
        plot_bgcolor='white',
        hovermode='x unified',
        margin=dict(l=60, r=40, t=80, b=50),
        template='plotly_white'
    )

    # ==================== ГРАФИК 4: МОЩНОСТЬ ДКС ====================
    fig4 = go.Figure()

    if power_col:
        fig4.add_trace(go.Scatter(
            x=yearly_df['Год'],
            y=yearly_df[power_col],
            mode='lines+markers',
            name='Мощность ДКС',
            line=dict(color='#f59e0b', width=3, shape='spline'),
            marker=dict(size=10, color='#f59e0b', symbol='square', line=dict(width=2, color='white')),
            fill='tozeroy',
            fillcolor='rgba(245, 158, 11, 0.1)',
            hovertemplate='<b>%{x} г.</b><br>Мощность: %{y:.2f} МВт<extra></extra>'
        ))
        
        fig4.update_layout(
            title=dict(text='<b>Мощность ДКС</b>', x=0.05, xanchor='left', font=dict(size=20, color='#1f2937')),
            xaxis=dict(title='<b>Год</b>', tickangle=-45, showgrid=True, gridcolor='#e5e7eb'),
            yaxis=dict(title='<b>Мощность, МВт</b>', titlefont=dict(color='#f59e0b'), tickfont=dict(color='#f59e0b'),
                       showgrid=True, gridcolor='#e5e7eb'),
            plot_bgcolor='white',
            hovermode='x unified',
            margin=dict(l=60, r=40, t=80, b=50),
            template='plotly_white'
        )

    # ========== СТАТИСТИКА ==========
    max_gas = find_plateau_level(yearly_df)
    plateau_year = None
    for _, row in yearly_df.iterrows():
        if row['Добыча газа, млрд м³/год'] >= max_gas * 0.95:
            plateau_year = row['Год']
            break
    
    total_produced = yearly_df['Накоплено, млрд м³'].iloc[-1]
    initial_gas = results.get('G_nach', 100)
    recovery_factor = min((total_produced / initial_gas * 100), 100) if initial_gas > 0 else 0

    # Год начала падения
    decline_start_year = None
    plateau_started = False
    plateau_count = 0
    for _, row in yearly_df.iterrows():
        if row['Добыча газа, млрд м³/год'] >= max_gas * 0.95:
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

        html.H2("Интерактивные графики", style={'marginBottom': 25, 'color': '#1f2937', 'fontSize': '28px', 'fontWeight': '600'}),
        
        html.Div([
            dcc.Graph(figure=fig1, config={'displayModeBar': True}),
        ], style={'marginBottom': 30}),
        
        html.Div([
            dcc.Graph(figure=fig2, config={'displayModeBar': True}),
        ], style={'marginBottom': 30}),
        
        html.Div([
            dcc.Graph(figure=fig3, config={'displayModeBar': True}),
        ], style={'marginBottom': 30}),
        
        html.Div([
            dcc.Graph(figure=fig4, config={'displayModeBar': True}),
        ], style={'marginBottom': 30}),
        
    ], style={'padding': '20px', 'backgroundColor': '#f8fafc', 'borderRadius': '16px'})