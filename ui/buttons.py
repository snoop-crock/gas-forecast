"""
Buttons component for Gas Forecast App
"""


def create_buttons(colors):
    """Создает кнопки управления"""
    import dash
    from dash import html

    return html.Div([
        html.Button("🔄 Сбросить", id='btn-reset', n_clicks=0,
                    style={'backgroundColor': colors['warning'], 'color': 'white',
                           'padding': '8px 16px', 'border': 'none', 'borderRadius': 5, 'marginRight': 10}),
        html.Button("📊 Рассчитать", id='btn-calculate', n_clicks=0,
                    style={'backgroundColor': colors['primary'], 'color': 'white',
                           'padding': '8px 16px', 'border': 'none', 'borderRadius': 5, 'marginRight': 10}),
        html.Button("💾 Экспорт в Excel", id='btn-export', n_clicks=0,
                    style={'backgroundColor': colors['success'], 'color': 'white',
                           'padding': '8px 16px', 'border': 'none', 'borderRadius': 5}),
    ], style={'marginBottom': 20})
