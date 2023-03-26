"""
简易Flask服务器，用于UI可视化
"""
import logging
from simulator import env
from simulator.config import CANVAS_SIZE_X, CANVAS_SIZE_Y
from flask import Flask, render_template, jsonify
from utils import overall_cache_miss_rate, overall_storage_utilization
from threading import Thread

app = Flask(__name__,
            template_folder="ui",
            static_folder="ui",
            static_url_path=""
            )

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

server_thread = Thread(target=app.run, kwargs={
    'host': 'localhost',
    'port': 5000,
    'debug': False
})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/curve_chart')
def charts():
    return render_template('curve_chart.html')


@app.route('/statistics')
def statistics():
    return render_template('statistics.html')


@app.route('/get_canvas_size')
def get_canvas_size():
    return jsonify({
        'width': CANVAS_SIZE_X,
        'height': CANVAS_SIZE_Y
    })


@app.route('/get_users')
def get_user_location():
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
                'fetching_from_remote': not connection.cached_initally,
            })

    return jsonify(result)


@app.route('/get_cache_agent_reward')
def get_cache_agent_reward():
    return jsonify(
        env.cache_agent.reward_history[-1],
    )


@app.route('/get_maintainance_agent_reward')
def get_maintainance_agent_action():
    return jsonify(
        env.maintainance_agent.reward_history[-1],
    )


@app.route('/get_overall_cache_hit_rate')
def get_overall_cache_hit_rate():
    return jsonify(
        1-overall_cache_miss_rate(env),
    )


@app.route('/get_overall_storage_utilization')
def get_overall_storage_utilization():
    return jsonify(
        overall_storage_utilization(env),
    )


@app.route('/get_timestamp')
def get_timestamp():
    return str(env.now())


@app.route('/pause')
def pause():
    env.pause()
    return jsonify({'paused': env.paused})


@app.route('/resume')
def resume():
    env.resume()
    return jsonify({'paused': env.paused})


def start_server():
    global server_thread
    server_thread.start()
    import webbrowser
    webbrowser.open('http://localhost:5000')
    webbrowser.open('http://localhost:5000/statistics')


def stop_server():
    global server_thread
    server_thread.join()


if __name__ == '__main__':
    start_server()
