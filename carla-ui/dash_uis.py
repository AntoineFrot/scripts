import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq

ui_towns = dbc.Col([
    # html.H6('Towns'),
    dbc.Col([
        dcc.Dropdown(
            id='dropdown_towns',
            options=[
                {'label': 'Town01', 'value': 'Town01'},
                {'label': 'Town02', 'value': 'Town02'},
                {'label': 'Town03', 'value': 'Town03'},
                {'label': 'Town04', 'value': 'Town04'},
                {'label': 'Town05', 'value': 'Town05'},
                {'label': 'Town06', 'value': 'Town06'},
                {'label': 'Town07', 'value': 'Town07'},
                {'label': 'Town10HD', 'value': 'Town10HD'}
            ],
            value='Town06',
            clearable=False,
            style=dict(
                width='150px',
                verticalAlign="middle"
            )
        ),
        html.Button('Select town', id='carla_select_world'),
    ])
])

ui_ip_adress = dbc.Col([
    html.H6('IP address'),
    dbc.Row([
        dcc.Input(id='ip1', type='number', min=0, max=255, step=1, size='4', value=127),
        html.Label('.'),
        dcc.Input(id='ip2', type='number', min=0, max=255, step=1, size='4', value=0),
        html.Label('.'),
        dcc.Input(id='ip3', type='number', min=0, max=255, step=1, size='4', value=0),
        html.Label('.'),
        dcc.Input(id='ip4', type='number', min=0, max=255, step=1, size='4', value=1),
        html.Label('|    |'),
        daq.Indicator(
            id='client-status',
            value=False,
            # color="#00cc96",
            color="#aaaaaa",
            size=40
        )
    ])
])

ui_weather = dbc.Col([
    html.H6('Weather'),
    dbc.Col([
        html.Label('Cloudiness'),
        dcc.Slider(id='weather_cloudiness',
                   min=0,
                   max=100,
                   step=1,
                   value=0),
    ]),
    dbc.Col([
        html.Label('Precipitation'),
        dcc.Slider(id='weather_precipitation',
                   min=0,
                   max=100,
                   step=1,
                   value=0),
    ]),
    dbc.Col([
        html.Label('Precipitation deposits'),
        dcc.Slider(id='weather_deposits',
                   min=0,
                   max=100,
                   step=1,
                   value=0),
    ]),
    dbc.Col([
        html.Label('Wetness'),
        dcc.Slider(id='weather_wetness',
                   min=0,
                   max=100,
                   step=1,
                   value=0),
    ]),
    html.H6('Sun'),
    dbc.Col([
        html.Label('Azimuth angle'),
        dcc.Slider(id='sun_azimuth_angle',
                   min=0,
                   max=180,
                   step=1,
                   value=90),
    ]),
    dbc.Col([
        html.Label('Altitude angle'),
        dcc.Slider(id='sun_altitude_angle',
                   min=-90,
                   max=90,
                   step=1,
                   value=0),
    ]),
])

ui_vehicle = dbc.Col([
    html.Button('Add vehicle', id='add_vehicle'),
    daq.Gauge(
        id='speed-gauge',
        min=0,
        max=100,
        value=0.0,
        color={"gradient": True,
               "ranges": {"green": [0, 33],
                          "yellow": [33, 66],
                          "red": [66, 100]}},
        showCurrentValue=True,
        units="kph",
    ),
])

ui_main = dbc.Container([
    html.Div(id='hidden-div1', style={'display': 'none'}),
    html.Div(id='hidden-div2', style={'display': 'none'}),
    html.Div(id='hidden-div3', style={'display': 'none'}),
    dcc.Interval(
        id='interval-component-fast',
        interval=100,  # in milliseconds
        n_intervals=0
    ),
    dcc.Interval(
        id='interval-component-slow',
        interval=2000,  # in milliseconds
        n_intervals=0
    ),

    dbc.Col([
        html.H4('CARLA UI'),
        dbc.Row([
            dbc.Col([
                dbc.Card(dbc.CardBody(ui_ip_adress), style={"width": "600px"}),
                # html.Button('Connect to CARLA server', id='carla_load_client'),

                dbc.Card(dbc.CardBody(ui_weather), style={"width": "600px"}),
                # html.Button('Select weather', id='carla_select_weather'),
            ]),

            dbc.Col([
                dbc.Card(dbc.CardBody(ui_towns), style={"width": "300px"}),
                dbc.Card(dbc.CardBody(ui_vehicle), style={"width": "300px"}),
            ]),
        ]),

        dbc.Row([
            dcc.Textarea(
                id='status-area',
                value='STATUS:',
                style={'width': '100%', 'height': 300},
            ),
        ]),
    ]),
])
