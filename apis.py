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


@app.route('/pie_chart')
def pie_chart():
    return render_template('pie_chart.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/storage_gauge')
def storage_gauge():
    return render_template('storage_gauge.html')


@app.route('/storage_tree')
def storage_tree():
    return render_template('storage_tree.html')


@app.route('/server_details')
def server_details(id=0):
    return render_template('server_details.html')


@app.route('/get_canvas_size')
def get_canvas_size():
    return jsonify({
        'width': CANVAS_SIZE_X,
        'height': CANVAS_SIZE_Y
    })


@app.route('/get_users')
def get_users():
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
    for edge_server in env.edge_servers.values():
        result[edge_server.id] = {
            'id': edge_server.id,
            'location': edge_server.location,
            'service_range': edge_server.service_range,
        }

    return jsonify(result)


@app.route('/get_connections')
def get_connections():
    result = []
    for server in env.edge_servers.values():
        for connection in server.conns:
            result.append({
                'user': connection.user.id,
                'source': connection.source.id,
                'cached_initally': connection.cached_initally,
            })

    return jsonify(result)


@app.route('/get_cache_agent_reward')
def get_cache_agent_reward():
    reward_history = env.cache_agent.reward_history
    result = reward_history[-1] if reward_history else 0
    return jsonify(result)


@app.route('/get_maintainance_agent_reward')
def get_maintainance_agent_action():
    reward_history = env.maintainance_agent.reward_history
    result = reward_history[-1] if reward_history else 0
    return jsonify(result)


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


@app.route('/get_cache_agent_action_history')
def get_cache_agent_action_history(num=20):
    temp = env.cache_agent.action_history[-num:]
    # 统计每个action的次数
    result = {}
    for action in env.cache_agent.actions:
        result[action] = 0
    for action in temp:
        result[action] += 1
    return jsonify(result)


@app.route('/get_maintainance_agent_action_history')
def get_maintainance_agent_action_history(num=20):
    temp = env.maintainance_agent.action_history[-num:]
    # 统计每个action的次数
    result = {}
    for action in env.maintainance_agent.actions:
        result[action] = 0
    for action in temp:
        result[action] += 1
    return jsonify(result)


@app.route('/get_top_freq_visited_service')
def get_top_freq_visited_service(num=10):
    services = list(env.data_center.services.values())
    services.sort(key=lambda x: x.request_frequency)
    result = []
    for service in services[-num:]:
        result.append({
            'id': service.id,
            'name': service.name,
            'request_frequency': service.request_frequency,
        })
    return jsonify(result)


@app.route('/get_top_charming_service')
def get_top_charming_service(num=10):
    pass


@app.route('/get_top_popular_service')
def get_top_popular_service(num=10):
    pass


@app.route('/get_storage_utilization')
def get_storage_utilization(id=0):
    server = env.edge_servers[id]
    result = {}
    for level in server.cache.keys():
        result[level] = {
            'total': server.get_storage_size(level),
            "used": server.storage_used(level),
            "percent": round(server.storage_used(level) / server.get_storage_size(level) * 100),
        }
    return jsonify(result)


@app.route('/get_storage_tree')
def get_storage_tree(id=0):
    def parse_service(service):
        return {
            "name": service.name,
            "value": service.size,
        }
    server = env.edge_servers[id]
    storage = server.cache
    result = []
    for level in storage.keys():
        result.append({
            "name": level,
            "value": server.get_storage_size(level),
            "children": [parse_service(service) for service in storage[level]]
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
    env.resume()
    return jsonify({'paused': env.paused})


def start_server():
    global server_thread
    server_thread.start()
    import webbrowser
    webbrowser.open('http://localhost:5000')
    webbrowser.open('http://localhost:5000/dashboard')


def stop_server():
    global server_thread
    server_thread.join()


if __name__ == '__main__':
    start_server()
