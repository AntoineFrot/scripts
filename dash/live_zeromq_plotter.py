import datetime

import random

import zmq
import json
import time
import threading

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dash.dependencies import Input, Output

data_reception_active = True
plotting_active = False
last_fig = None

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    html.Div([
        html.H4('CARLA live monitor'),
        html.Div(id='live-update-text'),
        dcc.Graph(id='live-update-graph'),
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )
    ])
)

# @app.callback(Output('live-update-text', 'children'),
#               [Input('interval-component', 'n_intervals')])
# def update_metrics(n):
#     lon = random.random()
#     lat = random.random()
#     alt = random.random()
#     style = {'padding': '5px', 'fontSize': '16px'}
#     return [
#         html.Span('Longitude: {0:.2f}'.format(lon), style=style),
#         html.Span('Latitude: {0:.2f}'.format(lat), style=style),
#         html.Span('Altitude: {0:0.2f}'.format(alt), style=style)
#     ]


@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    global plotting_active, last_fig

    # Prevent cyclic triggering blocking the script
    if last_fig is not None and plotting_active:
        # print('skip')
        return last_fig

    plotting_active = True

    data = {
        'time': app.list_t,
        'x': app.list_x,
        'y': app.list_y
    }

    # print(data['x'], data['y'])

    # Create the graph with subplots
    fig = plotly.subplots.make_subplots(rows=2,
                                        cols=2,
                                        vertical_spacing=0.05,
                                        specs=[[{}, {}],
                                               [{"colspan": 2}, None]],
                                        row_heights=[1, 3])
    fig['layout']['margin'] = {
        'l': 30, 'r': 10, 'b': 30, 't': 10
    }
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
    fig['layout']['height'] = 800  # px

    fig.append_trace({
        'x': data['time'],
        'y': data['x'],
        'name': 'x = f(t)',
        'mode': 'lines',
        'type': 'scatter'
    }, 1, 1)
    fig.append_trace({
        'x': data['time'],
        'y': data['y'],
        'name': 'y = f(t)',
        'mode': 'lines',
        'type': 'scatter'
    }, 1, 2)
    fig.append_trace({
        'x': data['x'],
        'y': data['y'],
        'text': 'real',
        'name': 'xy',
        'mode': 'lines',
        'type': 'scatter'
    }, 2, 1)

    # fig.print_grid()
    last_fig = fig
    plotting_active = False

    return fig


def receive_data():
    while data_reception_active:
        app.socket.send(b"req")

        message = app.socket.recv_string()

        # print("Received request: %s" % message)

        # o = VehicleData(**json.loads(message))
        o = json.loads(message)
        # print(o)

        # print(o.x, o.y)

        app.list_t.append(o['i'])  # o.i
        app.list_x.append(o['x'])  # o.x
        app.list_y.append(o['y'])  # o.y

        time.sleep(.01)


if __name__ == '__main__':

    app.context = zmq.Context()
    app.socket = app.context.socket(zmq.REQ)
    app.socket.connect("tcp://localhost:%s" % 5555)

    app.list_t = []
    app.list_x = []
    app.list_y = []

    try:
        timerThread = threading.Thread(target=receive_data)
        timerThread.start()

        app.run_server(debug=True, use_reloader=False)
    finally:
        data_reception_active = False
