# -*- coding: utf-8 -*-
import os
import sys
import argparse
import time

import dash
from dash.dependencies import Output, Input, State
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
DELAY_GET_MAP_LIST = 2  # s
DELAY_GET_VEHICLE_LIST = 2  # s


class CarlaUI:

    proxy = xmlrpc.client.ServerProxy('http://localhost:{}/'.format(XMLRPC_PORT))

    external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    def __init__(self):
        self.proxy_is_active = False
        self.towns_infos = None
        self.vehicles_list = []

        # Prevent execution of periodic task before __init__ has completed
        self.periodic_task_active = True

        self.app.layout = dash_uis.ui_main

        self.app.callback(Output('status-area', 'value'),
                          [Input('interval-component-slow', 'n_intervals')],
                          [State('status-area', 'value')])(self.update_client_status)

        self.app.callback(Output('speed-gauge', 'value'),
                          [Input('interval-component-fast', 'n_intervals')])(self.update_speed)

        self.app.callback(Output('hidden-div1', 'children'),
                          [Input('carla_select_world', 'n_clicks')],
                          [State('dropdown-towns', 'value')])(self.load_world)

        self.app.callback(Output('hidden-div2', 'children'),
                          [Input('weather_cloudiness', 'value'),
                           Input('weather_precipitation', 'value'),
                           Input('weather_deposits', 'value'),
                           Input('weather_wetness', 'value'),
                           Input('sun_azimuth_angle', 'value'),
                           Input('sun_altitude_angle', 'value')])(self.change_weather)

        self.app.callback(Output('hidden-div3', 'children'),
                          [Input('add_vehicle', 'n_clicks')
                           ])(self.add_vehicle)

        self.app.callback(Output('dropdown-towns-div', 'children'),
                          [Input('interval-component-slow', 'n_intervals')])(self.update_dropdown_towns)

        self.app.callback(Output('dropdown-vehicles-div', 'children'),
                          [Input('interval-component-slow', 'n_intervals')])(self.update_dropdown_vehicles)

        self.app.callback(Output('hidden-div4', 'children'),
                          [Input('dropdown-vehicles', 'value')])(self.select_vehicle)

        #     client_status_color = "#00cc96"
        #     client_status_value = True

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

                Thread(target=self.update_infos_async, args=()).start()

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

    def update_infos_async(self):
        time.sleep(DELAY_GET_MAP_LIST)
        self.towns_infos = self.proxy.get_maps_infos()
        time.sleep(DELAY_GET_VEHICLE_LIST)
        self.vehicles_list = self.proxy.get_vehicles()

    def update_dropdown_towns(self, n):
        if self.towns_infos is not None:
            selected_town, list_towns = self.towns_infos
            self.towns_infos = None
            return dash_uis.get_dropdown_towns(selected_town, list_towns)
        raise PreventUpdate

    def update_dropdown_vehicles(self, n):
        if self.vehicles_list is not None:
            list_vehicles = self.vehicles_list
            self.vehicles_list = None
            return dash_uis.get_dropdown_vehicles('', list_vehicles)
        raise PreventUpdate

    def load_world(self, n_clicks, value):
        if self.proxy_is_active and n_clicks is not None:
            Thread(target=self.load_world_async, args=(value,)).start()
        raise PreventUpdate

    def load_world_async(self, value):
        print('load_world_async', value)
        self.proxy.load_world(value)

    def change_weather(self, value_cloudiness, value_precipitation, value_deposits,
                       value_wetness, value_sun_azimuth_angle, value_sun_altitude_angle):
        if self.proxy_is_active:
            self.proxy.change_weather(value_cloudiness, value_precipitation,
                                      value_deposits, value_wetness,
                                      value_sun_azimuth_angle, value_sun_altitude_angle)
        raise PreventUpdate

    def add_vehicle(self, n_clicks):
        if self.proxy_is_active and n_clicks is not None:
            Thread(target=self.add_vehicle_async, args=()).start()
        raise PreventUpdate

    def add_vehicle_async(self):
        try:
            self.proxy.add_vehicle()
        except:
            pass
        time.sleep(DELAY_GET_VEHICLE_LIST)
        self.vehicles_list = self.proxy.get_vehicles()

    def select_vehicle(self, veh_id):
        if self.proxy_is_active and veh_id != '':
            print('select_vehicle', veh_id)
            self.proxy.select_vehicle(veh_id)
        raise PreventUpdate


if __name__ == '__main__':

    # Starting xmlrpc server, serving CarlaDaemon
    Thread(target=xmlrpc_serving_CarlaDaemon, args=()).start()

    carla_ui = CarlaUI()
    carla_ui.app.run_server(debug=False)
