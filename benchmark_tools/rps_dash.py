from multiprocessing import Process, Queue
from typing import Union
import dash
from dash.dependencies import Input, Output, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
import queue
import webbrowser
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

X = list()
X.append(0)
Y = list()
Y.append(0)
dash_process: Union[None, Process] = None
msg_queue: Union[None, Queue] = None
app = dash.Dash(__name__)
browser_opened = False
layout = go.Layout(title='RPS DashBoard')
layout.yaxis.rangemode = "tozero"

app.layout = html.Div(
    [
        dcc.Graph(id='live-graph', animate=False),
        dcc.Interval(
            id='graph-update',
            interval=1000,
            n_intervals=0
        ),
    ]
)


@app.callback(
    Output('live-graph', 'figure'),
    [Input('graph-update', 'n_intervals')]
)
def update_graph_scatter(n):
    global browser_opened
    if browser_opened is False:
        browser_opened = True
        webbrowser.open('http://127.0.0.1:8050/')
    while True:
        try:
            x, y = msg_queue.get(block=False)
            X.append(x)
            Y.append(y)
        except queue.Empty:
            break
    data = plotly.graph_objs.Scatter(
        x=X,
        y=Y,
        name='Scatter',
        mode='lines+markers'
    )
    # xaxis = dict(range=[min(X), max(X)]),
    # yaxis = dict(range=[min(Y), max(Y)])
    return {'data': [data],
            'layout': layout
            }


def __run_app_server(q):
    global msg_queue
    msg_queue = q
    app.run_server()


def run_dash_server(q):
    global dash_process
    assert dash_process is None
    dash_process = Process(target=__run_app_server, args=(q,))
    dash_process.start()


def stop_dash_server():
    global dash_process
    if dash_process is not None:
        dash_process.terminate()
        dash_process = None
