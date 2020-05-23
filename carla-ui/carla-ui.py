# -*- coding: utf-8 -*-
import os
import sys
import argparse
import time

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from threading import Thread
import xmlrpc.client

from carla_daemon import client_thread

MAX_STATUS_BUFFER_LEN = 8

t1 = Thread(target=client_thread, args=())
t1.start()

# with xmlrpc.client.ServerProxy("http://localhost:8000/") as proxy:
#     print(proxy.add(9, 5))
#     print(proxy.system.listMethods())

proxy = xmlrpc.client.ServerProxy("http://localhost:8000/")
# print(proxy.add(123, 234))

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

ui_towns = dbc.Col([
    html.H6('Towns'),
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
    )
])

ui_ip_adress = dbc.Col([
    html.H6('IP address'),
    dbc.Row([
        dcc.Input(id='ip1', type='number', min=0, max=255, step=1, size='3', value=127),
        html.Label('.'),
        dcc.Input(id='ip2', type='number', min=0, max=255, step=1, size='3', value=0),
        html.Label('.'),
        dcc.Input(id='ip3', type='number', min=0, max=255, step=1, size='3', value=0),
        html.Label('.'),
        dcc.Input(id='ip4', type='number', min=0, max=255, step=1, size='3', value=1)
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

app.layout = dbc.Container([
    html.Div(id='devnull', children=''),
    html.Div(id='devnull2', children=''),
    html.Div(id='devnull3', children=''),
    dcc.Interval(
        id='interval-component',
        interval=1*1000, # in milliseconds
        n_intervals=0
    ),

    dbc.Row([
        html.H4('CARLA UI'),
    ]),
    dbc.Row([
        dbc.Card(dbc.CardBody(ui_ip_adress),
                 style={"width": "600px"}),
        html.Button('Connect to CARLA server', id='carla_load_client'),
    ]),
    dbc.Row([
        dbc.Card(dbc.CardBody(ui_towns),
                 style={"width": "600px"}),
        html.Button('Select town', id='carla_select_world'),
    ]),
    dbc.Row([
        dbc.Card(dbc.CardBody(ui_weather),
                 style={"width": "600px"}),
        # html.Button('Select weather', id='carla_select_weather'),
    ]),
    dbc.Row([
        dcc.Textarea(
            id='status-area',
            value='STATUS:\n',
            style={'width': '100%', 'height': 300},
        ),
    ]),
])


# @app.callback(dash.dependencies.Output('status-area', 'value'),
#               [dash.dependencies.Input('interval-component', 'n_intervals')],
#               [dash.dependencies.State('status-area', 'value')])
# def update_status(n, status_buffer):
#     status_buffer_list = status_buffer.split('\n')
#     if len(status_buffer_list) > MAX_STATUS_BUFFER_LEN:
#         status_buffer_list.pop(1)
#     try:
#         msg = proxy.get_status()
#     except:
#         msg = '-no status available-'
#     status_buffer_list.append(msg)
#     return '\n'.join(status_buffer_list)


@app.callback(
    dash.dependencies.Output('devnull', 'children'),
    [dash.dependencies.Input('carla_load_client', 'n_clicks')],
    [])
def load_client(n_clicks):
    if n_clicks is not None:
        proxy.load_client()
    return ''


@app.callback(
    dash.dependencies.Output('devnull2', 'children'),
    [dash.dependencies.Input('carla_select_world', 'n_clicks')],
    [dash.dependencies.State('dropdown_towns', 'value')])
def load_world(n_clicks, value):
    if n_clicks is not None:
        proxy.load_world(value)
    return ''

@app.callback(
    dash.dependencies.Output('devnull3', 'children'),
    [dash.dependencies.Input('weather_cloudiness', 'value'),
     dash.dependencies.Input('weather_precipitation', 'value'),
     dash.dependencies.Input('weather_deposits', 'value'),
     dash.dependencies.Input('weather_wetness', 'value'),
     dash.dependencies.Input('sun_azimuth_angle', 'value'),
     dash.dependencies.Input('sun_altitude_angle', 'value')
     ])
def change_weather(value_cloudiness, value_precipitation,
                   value_deposits, value_wetness,
                   value_sun_azimuth_angle, value_sun_altitude_angle):
    proxy.change_weather(value_cloudiness, value_precipitation,
                         value_deposits, value_wetness,
                         value_sun_azimuth_angle, value_sun_altitude_angle)
    return ''


if __name__ == '__main__':

    app.run_server(debug=False)
