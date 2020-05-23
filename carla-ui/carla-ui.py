# -*- coding: utf-8 -*-
import os
import sys
import argparse
import time

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

import dash_daq as daq

# disable Dash HTTP log messages / see also SimpleXMLRPCServer: logRequests=False
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

from threading import Thread
import xmlrpc.client

from carla_daemon import client_thread
from carla_daemon import XMLRPC_PORT

MAX_STATUS_BUFFER_LEN = 8

t1 = Thread(target=client_thread, args=())
t1.start()


class CarlaUI:
    proxy = xmlrpc.client.ServerProxy('http://localhost:{}/'.format(XMLRPC_PORT))

    external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    ui_towns = dbc.Col([
        # html.H6('Towns'),
        dbc.Col([
            dcc.Dropdown(
                id='dropdown_towns',
                # options=[
                #     {'label': 'Town01', 'value': 'Town01'},
                #     {'label': 'Town02', 'value': 'Town02'},
                #     {'label': 'Town03', 'value': 'Town03'},
                #     {'label': 'Town04', 'value': 'Town04'},
                #     {'label': 'Town05', 'value': 'Town05'},
                #     {'label': 'Town06', 'value': 'Town06'},
                #     {'label': 'Town07', 'value': 'Town07'},
                #     {'label': 'Town10HD', 'value': 'Town10HD'}
                # ],
                # value='Town06',
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
            value=0,
            color={"gradient": True,
                   "ranges": {"green": [0, 33],
                              "yellow": [33, 66],
                              "red": [66, 100]}},
            showCurrentValue=True,
            units="kph",
        ),
    ])

    app.layout = dbc.Container([
        html.Div(id='hidden-div1', style={'display': 'none'}),
        html.Div(id='hidden-div2', style={'display': 'none'}),
        html.Div(id='hidden-div3', style={'display': 'none'}),
        dcc.Interval(
            id='interval-component',
            interval=1000,  # in milliseconds
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

    def __init__(self):
        self.periodic_task_active = True

        self.app.callback([dash.dependencies.Output('status-area', 'value'),
                           dash.dependencies.Output('client-status', 'value'),
                           dash.dependencies.Output('client-status', 'color'),
                           dash.dependencies.Output('speed-gauge', 'value')],
                          [dash.dependencies.Input('interval-component', 'n_intervals')],
                          [dash.dependencies.State('status-area', 'value')
                           ])(self.periodic_task)

        self.app.callback(dash.dependencies.Output('hidden-div1', 'children'),
                          [dash.dependencies.Input('carla_select_world', 'n_clicks')],
                          [dash.dependencies.State('dropdown_towns', 'value')
                           ])(self.load_world)

        self.app.callback(dash.dependencies.Output('hidden-div2', 'children'),
                          [dash.dependencies.Input('weather_cloudiness', 'value'),
                           dash.dependencies.Input('weather_precipitation', 'value'),
                           dash.dependencies.Input('weather_deposits', 'value'),
                           dash.dependencies.Input('weather_wetness', 'value'),
                           dash.dependencies.Input('sun_azimuth_angle', 'value'),
                           dash.dependencies.Input('sun_altitude_angle', 'value')
                           ])(self.change_weather)

        self.app.callback(dash.dependencies.Output('hidden-div3', 'children'),
                          [dash.dependencies.Input('add_vehicle', 'n_clicks')
                           ])(self.add_vehicle)

        self.periodic_task_active = False

    def periodic_task(self, n, status_buffer):

        # if n<10:
        #     return '', False, '', 30.0

        if self.periodic_task_active:
            # print('skip')
            raise PreventUpdate

        self.periodic_task_active = True

        client_status_color = "#00cc96"
        client_status_value = True

        status_buffer_list = status_buffer.split('\n')
        if len(status_buffer_list) > MAX_STATUS_BUFFER_LEN:
            status_buffer_list.pop(1)

        try:
            self.proxy.load_client()

            self.maps_list = self.proxy.call_obj_method('client', 'get_available_maps')

            try:
                msg = self.proxy.get_status()
            except:
                msg = '-no status available-'
                client_status_color = "#aaaaaa"
                client_status_value = False
        except:
            msg = '-client not available-'
            client_status_color = "#aaaaaa"
            client_status_value = False

        status_buffer_list.append(msg)

        self.periodic_task_active = False

        return '\n'.join(status_buffer_list), client_status_value, client_status_color, self.proxy.get_vehicle_speed()

    def load_world(self, n_clicks, value):
        if n_clicks is not None:
            self.proxy.load_world(value)
        raise PreventUpdate

    def change_weather(self, value_cloudiness, value_precipitation, value_deposits,
                       value_wetness, value_sun_azimuth_angle, value_sun_altitude_angle):
        self.proxy.change_weather(value_cloudiness, value_precipitation,
                                  value_deposits, value_wetness,
                                  value_sun_azimuth_angle, value_sun_altitude_angle)
        raise PreventUpdate

    def add_vehicle(self, n_clicks):
        if n_clicks is not None:
            self.proxy.add_vehicle()
        raise PreventUpdate


if __name__ == '__main__':
    carla_ui = CarlaUI()
    carla_ui.app.run_server(debug=False)
