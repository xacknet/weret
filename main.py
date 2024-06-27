import threading
import time
import requests
import random
from flask import Flask, request, jsonify, send_file
import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

# Устанавливаем безголовый режим для Matplotlib
plt.switch_backend('Agg')

# Flask сервер для приема данных
server = Flask(__name__)

sensor_data = {
    'время': [],
    'наклон': [],
    'температура': [],
    'влажность': [],
    'огонь': [],
    'удар': [],
    'вибрация': [],
    'звук': []
}

@server.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    for sensor, value in data.items():
        if sensor in sensor_data:
            sensor_data[sensor].append(value)
    return jsonify({"status": "успех"}), 200

@server.route('/export', methods=['GET'])
def export_data():
    df = pd.DataFrame(sensor_data)
    file_path = 'sensor_data.xlsx'
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

def run_flask():
    server.run(debug=False, use_reloader=False)

# Начальные значения для датчиков
initial_values = {
    'наклон': 45.0,
    'температура': 20.0,
    'влажность': 50.0,
    'огонь': 0,
    'удар': 5.0,
    'вибрация': 5.0,
    'звук': 0.2  # Начальная частота жужжания в ГГц
}

# Генерация данных для датчика звука
def generate_sound_data():
    # Генерация случайной частоты жужжания пчел в пределах 0.1 - 0.3 ГГц
    return random.uniform(0.1, 0.3)

# Скрипт для отправки данных
def send_data():
    url = 'http://localhost:5000/data'
    current_values = initial_values.copy()
    
    while True:
        current_values['время'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_values['температура'] += random.uniform(-0.01, 0.01)  # Маленькие изменения
        current_values['влажность'] += random.uniform(-0.01, 0.01)  # Маленькие изменения
        current_values['вибрация'] += random.uniform(-0.01, 0.01)  # Маленькие изменения

        # Ограничиваем диапазон значений
        current_values['температура'] = max(-20, min(50, current_values['температура']))
        current_values['влажность'] = max(0, min(100, current_values['влажность']))
        current_values['вибрация'] = max(0, min(10, current_values['вибрация']))

        # Генерация данных звука
        current_values['звук'] = generate_sound_data()

        response = requests.post(url, json=current_values)
        print(f"Отправка данных: {current_values}")
        print(f"Ответ сервера: {response.json()}")
        time.sleep(1)

# Dash сервер для визуализации данных
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server, url_base_pathname='/dash/')

def create_figure(data, title, yaxis_title):
    df = pd.DataFrame(sensor_data)
    figure = go.Figure()
    for sensor, values in data.items():
        if sensor != 'звук':
            figure.add_trace(go.Scatter(x=df['время'], y=values, mode='lines+markers', name=sensor))
    figure.update_layout(title=title, xaxis_title='Время', yaxis_title=yaxis_title, margin=dict(l=40, r=0, t=40, b=30))
    return figure

def create_sound_figure():
    figure = go.Figure()
    df = pd.DataFrame(sensor_data)
    figure.add_trace(go.Scatter(x=df['время'], y=df['звук'], mode='lines+markers', name='Звук'))
    figure.update_layout(title='Частота жужжания пчел', xaxis_title='Время', yaxis_title='Частота (ГГц)', margin=dict(l=40, r=0, t=40, b=30))
    return figure

app.layout = html.Div(children=[
    html.H1(children='Дашборд данных с датчиков', style={'textAlign': 'center', 'color': '#4CAF50', 'fontSize': '2.5em'}),
    dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0),
    html.Div([
        html.Div([
            dcc.Graph(id='наклон-graph'),
            html.H4("Данные датчика наклона", style={'textAlign': 'center'})
        ], className="six columns"),
        html.Div([
            dcc.Graph(id='температура-graph'),
            html.H4("Данные датчика температуры", style={'textAlign': 'center'})
        ], className="six columns")
    ], className="row"),
    html.Div([
        html.Div([
            dcc.Graph(id='влажность-graph'),
            html.H4("Данные датчика влажности", style={'textAlign': 'center'})
        ], className="six columns"),
        html.Div([
            dcc.Graph(id='огонь-graph'),
            html.H4("Данные датчика огня", style={'textAlign': 'center'})
        ], className="six columns")
    ], className="row"),
    html.Div([
        html.Div([
            dcc.Graph(id='удар-graph'),
            html.H4("Данные датчика удара", style={'textAlign': 'center'})
        ], className="six columns"),
        html.Div([
            dcc.Graph(id='вибрация-graph'),
            html.H4("Данные датчика вибрации", style={'textAlign': 'center'})
        ], className="six columns")
    ], className="row"),
    html.Div([
        dcc.Graph(id='звук-graph'),
        html.H4("Частота жужжания пчел", style={'textAlign': 'center'})
    ], className="row"),
    html.Div([
        html.A("Экспорт данных в Excel", href="/export", className="button", style={
            'background-color': '#4CAF50',
            'border': 'none',
            'color': 'white',
            'padding': '15px 32px',
            'text-align': 'center',
            'text-decoration': 'none',
            'display': 'inline-block',
            'font-size': '16px',
            'margin': '4px 2px',
            'cursor': 'pointer'
        })
    ], style={'textAlign': 'center', 'marginTop': '20px'})
], className="container")

@app.callback(
    [Output('наклон-graph', 'figure'),
     Output('температура-graph', 'figure'),
     Output('влажность-graph', 'figure'),
     Output('огонь-graph', 'figure'),
     Output('удар-graph', 'figure'),
     Output('вибрация-graph', 'figure'),
     Output('звук-graph', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_graphs(n):
    tilt_fig = create_figure({'наклон': sensor_data['наклон']}, 'Данные датчика наклона', 'Наклон (градусы)')
    temp_fig = create_figure({'температура': sensor_data['температура']}, 'Данные датчика температуры', 'Температура (°C)')
    hum_fig = create_figure({'влажность': sensor_data['влажность']}, 'Данные датчика влажности', 'Влажность (%)')
    fire_fig = create_figure({'огонь': sensor_data['огонь']}, 'Данные датчика огня', 'Огонь обнаружен')
    shock_fig = create_figure({'удар': sensor_data['удар']}, 'Данные датчика удара', 'Удар (g)')
    vibr_fig = create_figure({'вибрация': sensor_data['вибрация']}, 'Данные датчика вибрации', 'Вибрация (g)')
    sound_fig = create_sound_figure()
    
    return tilt_fig, temp_fig, hum_fig, fire_fig, shock_fig, vibr_fig, sound_fig

def run_dash():
    app.run_server(debug=False)

# Запуск всех компонентов
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    data_thread = threading.Thread(target=send_data)
    dash_thread = threading.Thread(target=run_dash)

    flask_thread.start()
    data_thread.start()
    dash_thread.start()

    flask_thread.join()
    data_thread.join()
    dash_thread.join()
