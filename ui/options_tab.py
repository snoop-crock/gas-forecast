import dash
from dash import dcc, html


def create_options_tab(params, colors):
    return html.Div([
        html.H3("Настройки расчета", style={'marginBottom': 20}),

        html.Div([
            html.Label("Учет трения в стволе:", style={
                       'width': '300px', 'display': 'inline-block'}),
            dcc.RadioItems(id='opt-friction', options=[
                {'label': ' Включен', 'value': 1},
                {'label': ' Выключен', 'value': 0}
            ], value=params.get('opt_friction', 1), inline=True),
        ], style={'marginBottom': 15}),

        html.Div([
            html.Label("Метод расчета PVT:", style={
                       'width': '300px', 'display': 'inline-block'}),
            dcc.Dropdown(id='opt-pvt_method', options=[
                {'label': 'Латонова-Гуревича', 'value': 'latonov'},
                {'label': 'Брауна-Катца', 'value': 'brown'}
            ], value=params.get('pvt_method', 'latonov'), style={'width': '250px', 'display': 'inline-block'}),
        ], style={'marginBottom': 15}),

        html.Div(id='options-status',
                 style={'marginTop': 20, 'color': 'green'})
    ])