"""
简易Flask服务器，用于UI可视化
"""

import os
from environment import env
from flask import Flask, render_template, request, jsonify
from threading import Thread

app = Flask(__name__,
            template_folder="ui",
            static_folder="ui",
            static_url_path=""
            )
server_thread = Thread(target=app.run, kwargs={
    'host': 'localhost',
    'port': 5000,
    'debug': False
})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_canvas_size')
def get_canvas_size():
    from config import CANVAS_SIZE_X, CANVAS_SIZE_Y
    return jsonify({
        'width': CANVAS_SIZE_X,
        'height': CANVAS_SIZE_Y
    })


@app.route('/get_users')
def get_user_location():
    from environment import env
    result = {}
    for user in env.users:
        result[user.id] = {
            'id': user.id,
            'name': user.name,
            'location': user.location,
            'is_idle': user.is_idle,
            'sleep_remaining': user.sleep_remaining
        }

    return jsonify(result)


@app.route('/get_edge_servers')
def get_edge_servers():
    result = {}
    for edge_server in env.edge_servers:
        result[edge_server.id] = {
            'id': edge_server.id,
            'location': edge_server.location,
            'service_range': edge_server.service_range,
        }

    return jsonify(result)


@app.route('/get_connections')
def get_connections():
    result = []
    for server in env.edge_servers:
        for connection in server.conns:
            result.append({
                'user': connection.user.id,
                'source': connection.source.id,
                'fetching_from_remote': connection.es_fetching_from_remote,
            })

    return jsonify(result)


@app.route('/get_timestamp')
def get_timestamp():
    return str(env.now())


@app.route('/pause')
def pause():
    env.pause()
    return jsonify({'paused': env.paused})


@app.route('/resume')
def resume():
    from environment import env
    env.resume()
    return jsonify({'paused': env.paused})


def start_server():
    global server_thread
    server_thread.start()
    import webbrowser
    webbrowser.open('http://localhost:5000')


def stop_server():
    global server_thread
    server_thread.join()


if __name__ == '__main__':
    start_server()
