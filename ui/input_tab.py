import dash
from dash import dcc, html


def create_input_tab(params, colors):
    """Создает вкладку ввода параметров в современном стиле"""

    return html.Div([
        # Карточка 1: Пластовые параметры
        html.Div([
            html.Div([
                html.I(className="fas fa-mountain",
                       style={'marginRight': '10px'}),
                html.H3("Пластовые параметры",
                        style={'fontSize': '16px', 'fontWeight': '600', 'margin': 0})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),

            html.Div([
                # Строка 1
                html.Div([
                    html.Div([
                        html.Label("Начальное пластовое давление (МПа)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-P_pl',
                            type='number',
                            value=params.get('P_pl', 25),
                            step=0.5,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Пластовая температура (°C)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-T_pl',
                            type='number',
                            value=params.get('T_pl', 80),
                            step=1,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Начальные запасы (млрд м³)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-G_nach',
                            type='number',
                            value=params.get('G_nach', 100),
                            step=10,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1})
                ], style={'display': 'flex', 'marginBottom': '12px'}),

                # Строка 2
                html.Div([
                    html.Div([
                        html.Label("Относительная плотность газа",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-rho_otn',
                            type='number',
                            value=params.get('rho_otn', 0.6),
                            step=0.05,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1})
                ], style={'display': 'flex'})
            ])
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'border': '1px solid #e2e8f0',
            'padding': '20px',
            'marginBottom': '20px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'
        }),

        # Карточка 2: Параметры скважины
        html.Div([
            html.Div([
                html.I(className="fas fa-oil-can",
                       style={'marginRight': '10px'}),
                html.H3("Параметры скважины",
                        style={'fontSize': '16px', 'fontWeight': '600', 'margin': 0})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),

            html.Div([
                # Строка 1
                html.Div([
                    html.Div([
                        html.Label("Количество скважин (шт)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-N_skv',
                            type='number',
                            value=params.get('N_skv', 10),
                            step=1,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Глубина скважины (м)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-H_skv',
                            type='number',
                            value=params.get('H_skv', 2500),
                            step=100,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Диаметр НКТ (мм)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-d_NKT',
                            type='number',
                            value=params.get('d_NKT', 100),
                            step=10,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1})
                ], style={'display': 'flex', 'marginBottom': '12px'}),

                # Строка 2
                html.Div([
                    html.Div([
                        html.Label("Коэффициент a",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-a_coef',
                            type='number',
                            value=params.get('a_coef', 0.15),
                            step=0.05,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Коэффициент b",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-b_coef',
                            type='number',
                            value=params.get('b_coef', 0.0003),
                            step=0.00005,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Макс. депрессия (МПа)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-dP_max',
                            type='number',
                            value=params.get('dP_max', 10),
                            step=1,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1})
                ], style={'display': 'flex', 'marginBottom': '12px'}),

                # Строка 3
                html.Div([
                    html.Div([
                        html.Label("Коэффициент эксплуатации",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-K_eks',
                            type='number',
                            value=params.get('K_eks', 0.95),
                            step=0.02,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1})
                ], style={'display': 'flex'})
            ])
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'border': '1px solid #e2e8f0',
            'padding': '20px',
            'marginBottom': '20px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'
        }),

        # Карточка 3: Параметры прогноза (полка)
        html.Div([
            html.Div([
                html.I(className="fas fa-chart-line",
                       style={'marginRight': '10px'}),
                html.H3("Параметры прогноза",
                        style={'fontSize': '16px', 'fontWeight': '600', 'margin': 0})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),

            html.Div([
                html.Div([
                    html.Label("Режим полки",
                               style={'fontSize': '12px', 'color': '#666', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.RadioItems(
                        id='input-plateau_mode',
                        options=[
                            {'label': ' Максимально длинная полка', 'value': 'auto'},
                            {'label': ' Заданный темп отбора', 'value': 'manual'}
                        ],
                        value=params.get('plateau_mode', 'auto'),
                        inline=False,
                        style={'marginBottom': '12px'}
                    )
                ]),

                html.Div([
                    html.Div([
                        html.Label("Целевой темп отбора (% в год)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-target_recovery_rate',
                            type='number',
                            value=params.get('target_recovery_rate', 8),
                            step=0.5,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'marginBottom': '12px'}),

                    html.Div([
                        html.Label("Полка вручную (млрд м³/год, 0 = по темпу)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-Q_polka',
                            type='number',
                            value=params.get('Q_polka', 0),
                            step=0.5,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'marginBottom': '12px'})
                ])
            ])
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'border': '1px solid #e2e8f0',
            'padding': '20px',
            'marginBottom': '20px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'
        }),

        # Карточка 4: ДКС
        html.Div([
            html.Div([
                html.I(className="fas fa-industry",
                       style={'marginRight': '10px'}),
                html.H3("Дожимная компрессорная станция",
                        style={'fontSize': '16px', 'fontWeight': '600', 'margin': 0})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),

            html.Div([
                html.Div([
                    html.Label("Режим работы ДКС",
                               style={'fontSize': '12px', 'color': '#666', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='input-DKS_mode',
                        options=[
                            {'label': 'Расчетный', 'value': 'расчетный'},
                            {'label': 'Ограничительный',
                                'value': 'ограничительный'}
                        ],
                        value=params.get('DKS_mode', 'расчетный'),
                        style={
                            'width': '100%',
                            'border': '1px solid #e2e8f0',
                            'borderRadius': '8px'
                        }
                    )
                ], style={'marginBottom': '12px'}),

                html.Div([
                    html.Div([
                        html.Label("Давление на входе (МПа)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-P_vh_DKS',
                            type='number',
                            value=params.get('P_vh_DKS', 5),
                            step=0.5,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Давление на выходе (МПа)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-P_vyh_DKS',
                            type='number',
                            value=params.get('P_vyh_DKS', 7.5),
                            step=0.5,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Мощность ДКС (МВт)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-N_DKS',
                            type='number',
                            value=params.get('N_DKS', 50),
                            step=10,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1})
                ], style={'display': 'flex'})
            ])
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'border': '1px solid #e2e8f0',
            'padding': '20px',
            'marginBottom': '20px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'
        }),

        # Карточка 5: Обводнение
        html.Div([
            html.Div([
                html.I(className="fas fa-water",
                       style={'marginRight': '10px'}),
                html.H3("Обводнение",
                        style={'fontSize': '16px', 'fontWeight': '600', 'margin': 0})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),

            html.Div([
                html.Div([
                    html.Div([
                        html.Label("Начальный ВГФ (г/м³)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-VGF_nach',
                            type='number',
                            value=params.get('VGF_nach', 0),
                            step=1,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Интенсивность роста ВГФ (г/м³)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-dVGF_dG',
                            type='number',
                            value=params.get('dVGF_dG', 10),
                            step=1,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Критический ВГФ (г/м³)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-VGF_krit',
                            type='number',
                            value=params.get('VGF_krit', 200),
                            step=10,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1})
                ], style={'display': 'flex'})
            ])
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'border': '1px solid #e2e8f0',
            'padding': '20px',
            'marginBottom': '20px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'
        }),

        # Карточка 6: Временные параметры
        html.Div([
            html.Div([
                html.I(className="fas fa-calendar",
                       style={'marginRight': '10px'}),
                html.H3("Временные параметры",
                        style={'fontSize': '16px', 'fontWeight': '600', 'margin': 0})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),

            html.Div([
                html.Div([
                    html.Div([
                        html.Label("Год начала разработки",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-start_year',
                            type='number',
                            value=params.get('start_year', 2025),
                            step=1,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1, 'marginRight': '12px'}),
                    html.Div([
                        html.Label("Горизонт прогноза (лет)",
                                   style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px', 'display': 'block'}),
                        dcc.Input(
                            id='input-T_max',
                            type='number',
                            value=params.get('T_max', 35),
                            step=1,
                            style={
                                'width': '100%',
                                'padding': '8px 12px',
                                'border': '1px solid #e2e8f0',
                                'borderRadius': '8px',
                                'fontSize': '14px',
                                'backgroundColor': '#f8fafc'
                            }
                        )
                    ], style={'flex': 1})
                ], style={'display': 'flex'})
            ])
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'border': '1px solid #e2e8f0',
            'padding': '20px',
            'marginBottom': '20px',
            'boxShadow': '0 1px 3px rgba(0,0,0,0.05)'
        })
    ], style={'padding': '0'})
