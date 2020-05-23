# -*- coding: utf-8 -*-
import os
import sys
import argparse

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import queue
from threading import Thread

from carla_daemon import client_thread, client_thread_callme


t2 = Thread(target=client_thread_callme, args=())
t2.start()

print('Started')

import xmlrpc.client
import time

count = 1
while True:
    try:
        s = xmlrpc.client.ServerProxy('http://localhost:8000')
        print(s.myfunction(count, 4))
        count += 1
        time.sleep(1)
    except:
        pass
sys.exit()


class CommObj:
    cmd = None
    param = None


# Create the shared queue and launch both threads
q_control = queue.Queue()
q_status = queue.Queue()
t1 = Thread(target=client_thread, args=(q_control, q_status))
t1.start()

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

app.layout = dbc.Container([
    html.Div(id='devnull', children=''),
    html.Div(id='devnull2', children=''),
    dcc.Interval(
        id='interval-component',
        interval=1*1000, # in milliseconds
        n_intervals=0
    ),

    dbc.Row([
        html.H4('CARLA UI'),
    ]),
    dbc.Row([
        html.Button('Connect to CARLA server', id='carla_load_client'),
    ]),
    dbc.Row([
        dbc.Card(dbc.CardBody(ui_ip_adress)),
        dbc.Card(dbc.CardBody(ui_towns)),
    ]),
    dbc.Row([
        html.Button('Submit', id='submit'),
    ]),
    dbc.Row([
        dcc.Textarea(
            id='status-area',
            value='STATUS:\n',
            style={'width': '100%', 'height': 300},
        ),
    ]),
])


@app.callback(dash.dependencies.Output('status-area', 'value'),
              [dash.dependencies.Input('interval-component', 'n_intervals')],
              [dash.dependencies.State('status-area', 'value')])
def update_status(n, status_buffer):
    print('SIZE', q_status.qsize())
    while True:
        try:
            status_msg = q_status.get(block=False)
        except queue.Empty:
            break
        status_buffer += status_msg.value
        status_buffer += '\n'
    print('LEN', len(status_buffer))
    return status_buffer


@app.callback(
    dash.dependencies.Output('devnull', 'children'),
    [dash.dependencies.Input('carla_load_client', 'n_clicks')],
    [])
def load_client(n_clicks):
    if n_clicks is not None:
        print('load_client', n_clicks)
        co = CommObj()
        co.cmd = 'load_client'
        q_control.put(co)
    return ''


@app.callback(
    dash.dependencies.Output('devnull2', 'children'),
    [dash.dependencies.Input('submit', 'n_clicks')],
    [dash.dependencies.State('dropdown_towns', 'value')])
def load_world(n_clicks, value):
    if n_clicks is not None:
        print('load_world', n_clicks, value)
        co = CommObj()
        co.cmd = 'load_world'
        co.param = value
        q_control.put(co)
    return ''


if __name__ == '__main__':

    app.run_server(debug=True)
