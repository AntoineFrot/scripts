# -*- coding: utf-8 -*-
import os
import sys
import argparse
import time

import dash
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

# Dash UI components
import dash_uis

# disable Dash HTTP log messages / see also SimpleXMLRPCServer: logRequests=False
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

from threading import Thread
import xmlrpc.client

from carla_daemon import xmlrpc_serving_CarlaDaemon
from carla_daemon import XMLRPC_PORT

MAX_STATUS_BUFFER_LEN = 8


class CarlaUI:

    proxy = xmlrpc.client.ServerProxy('http://localhost:{}/'.format(XMLRPC_PORT))

    external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    def __init__(self):
        self.proxy_is_active = False
        self.towns_infos = None

        # Prevent execution of periodic task before __init__ has completed
        self.periodic_task_active = True

        self.app.layout = dash_uis.ui_main

        # self.app.callback([dash.dependencies.Output('status-area', 'value'),
        #                    dash.dependencies.Output('client-status', 'value'),
        #                    dash.dependencies.Output('client-status', 'color'),
        #                    ],
        #                   [dash.dependencies.Input('interval-component', 'n_intervals')],
        #                   [dash.dependencies.State('status-area', 'value')
        #                    ])(self.periodic_task)

        self.app.callback(dash.dependencies.Output('status-area', 'value'),
                          [dash.dependencies.Input('interval-component-slow', 'n_intervals')],
                          [dash.dependencies.State('status-area', 'value')
                           ])(self.update_client_status)

        self.app.callback(dash.dependencies.Output('speed-gauge', 'value'),
                          [dash.dependencies.Input('interval-component-fast', 'n_intervals')])(self.update_speed)

        self.app.callback(dash.dependencies.Output('hidden-div1', 'children'),
                          [dash.dependencies.Input('carla_select_world', 'n_clicks')],
                          [dash.dependencies.State('dropdown-towns', 'value')
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

        self.app.callback(dash.dependencies.Output('dropdown-towns-div', 'children'),
                          [dash.dependencies.Input('interval-component-slow', 'n_intervals')]
        )(self.update_dropdown_towns)

        # Enables execution of periodic task
        self.periodic_task_active = False

    def update_client_status(self, n, status_buffer):

        if self.periodic_task_active:
            raise PreventUpdate

        self.periodic_task_active = True

        if not self.proxy_is_active:
            try:
                self.proxy.load_client()
                self.proxy_is_active = True
                msg = '-client loaded-'

                self.towns_infos = self.proxy.get_maps_infos()
            except:
                msg = '-client cannot be loaded-'
        else:
            try:
                msg = self.proxy.get_status()
            except:
                msg = '-error on client status update-'

        status_buffer_list = status_buffer.split('\n')
        if len(status_buffer_list) > MAX_STATUS_BUFFER_LEN:
            status_buffer_list.pop(1)
        status_buffer_list.append(msg)

        self.periodic_task_active = False

        return '\n'.join(status_buffer_list)

    def update_speed(self, n):
        try:
            return self.proxy.get_vehicle_speed()
        except:
            return 0.0

    def update_dropdown_towns(self, n):
        if self.towns_infos is not None:
            selected_town, list_towns = self.towns_infos
            self.towns_infos = None
            return dash_uis.get_dropdown_towns(selected_town, list_towns)
        raise PreventUpdate

    # def periodic_task(self, n, status_buffer):
    #
    #     # if n<10:
    #     #     return '', False, '', 30.0
    #
    #     if self.periodic_task_active:
    #         # print('skip')
    #         raise PreventUpdate
    #
    #     self.periodic_task_active = True
    #
    #     client_status_color = "#00cc96"
    #     client_status_value = True
    #
    #     status_buffer_list = status_buffer.split('\n')
    #     if len(status_buffer_list) > MAX_STATUS_BUFFER_LEN:
    #         status_buffer_list.pop(1)
    #
    #     try:
    #         self.proxy.load_client()
    #
    #
    #
    #         try:
    #             msg = self.proxy.get_status()
    #         except:
    #             msg = '-no status available-'
    #             client_status_color = "#aaaaaa"
    #             client_status_value = False
    #     except:
    #         msg = '-client not available-'
    #         client_status_color = "#aaaaaa"
    #         client_status_value = False
    #
    #     status_buffer_list.append(msg)
    #
    #     self.periodic_task_active = False
    #
    #     return '\n'.join(status_buffer_list), client_status_value, client_status_color, self.proxy.get_vehicle_speed()

    def load_world(self, n_clicks, value):
        if self.proxy_is_active and n_clicks is not None:
            self.proxy.load_world(value)
        raise PreventUpdate

    def change_weather(self, value_cloudiness, value_precipitation, value_deposits,
                       value_wetness, value_sun_azimuth_angle, value_sun_altitude_angle):
        if self.proxy_is_active:
            self.proxy.change_weather(value_cloudiness, value_precipitation,
                                      value_deposits, value_wetness,
                                      value_sun_azimuth_angle, value_sun_altitude_angle)
        raise PreventUpdate

    def add_vehicle(self, n_clicks):
        if self.proxy_is_active and n_clicks is not None:
            self.proxy.add_vehicle()
        raise PreventUpdate


if __name__ == '__main__':

    # Starting xmlrpc server, serving CarlaDaemon
    Thread(target=xmlrpc_serving_CarlaDaemon, args=()).start()

    carla_ui = CarlaUI()
    carla_ui.app.run_server(debug=False)
