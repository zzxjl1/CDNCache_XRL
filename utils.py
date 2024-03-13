import math
import random
import numpy as np
from scipy.stats import truncnorm

GB2MB = 1000
TB2GB = 1000

SEC2MS = 1000
MIN2SEC = 60
HOUR2MIN = 60
DAY2HOUR = 24


def generate_size():
    """生成满足zipf分布的服务大小，即大部分服务很小，零星出现大服务"""
    t = np.random.zipf(a=2, size=1)[0]
    return t * 100 * random.random() + 1


def generate_version():
    """生成满足指数分布的版本号，即大部分用户使用的是最新版本，零星出现旧版本，越旧的版本越稀有"""
    from simulator.config import LATEST_VERSION

    scale = 8  # 尺度参数
    size = 1  # 生成 1 个版本号

    min_version = LATEST_VERSION - 3  # 最小版本号
    if min_version < 0:
        min_version = 0
    # 使用 numpy 库中的指数分布函数生成版本号
    versions = np.random.exponential(scale, size) + min_version
    # 将版本号四舍五入到整数
    versions = np.round(versions, 1)
    # 所有大于 5 的版本号都设置为 5.0
    versions[versions > LATEST_VERSION] = LATEST_VERSION

    # print(versions)
    # 统计每个版本号出现的次数
    # print(np.unique(versions, return_counts=True))
    return versions[0]


def calc_distance(a, b):
    x1, y1 = a
    x2, y2 = b
    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    return distance


def add_connection_history(connection_history, conn, max_len=200):
    connection_history.append(conn)
    if len(connection_history) > max_len:  # 保留最近n次连接
        connection_history.pop(0)


def calc_request_frequency(connection_history, num=10):
    if len(connection_history) <= 1:
        return 0
    connection_history = connection_history[-num:]
    total_time = connection_history[-1].birth - connection_history[0].birth
    if total_time == 0:
        return 1e-3  # 防止除0错误
    return len(connection_history) / total_time * SEC2MS


def pop_expired_connection_history(
    connection_history, env, threshold=10 * MIN2SEC * SEC2MS
):
    for conn in connection_history:  # 删除超时的连接历史
        if env.now() - conn.birth > threshold:
            connection_history.remove(conn)


def overall_cache_miss_rate(env):
    """计算整体缓存未命中率"""
    t = [es.cache_miss_rate for es in env.edge_servers.values()]
    average = sum(t) / len(t)
    return average


def overall_storage_utilization(env):
    """计算整体存储利用率"""
    used, total = 0, 0
    for es in env.edge_servers.values():
        used += sum(es.storage_used())
        total += sum(es.storage_size) * GB2MB
    return used / total


def overall_cache_hit_status(env):
    """计算整体缓存命中情况"""
    result = {"L1": 0, "L2": 0, "L3": 0}
    for es in env.edge_servers.values():
        result = es.cache_hit_status  # {"L1": 0, "L2": 0, "L3": 0}
        for level, hit in result.items():
            result[level] += hit
    return result


def calc_action_history(agent, num=20):
    temp = agent.action_history[-num:]
    result = {}
    for action in agent.actions:
        result[action] = 0
    for action in temp:
        result[action] += 1
    return result


def calc_overall_cache_agent_action_history(env, num=5):
    result = {}
    agents = [es.cache_agent for es in env.edge_servers.values()]
    for agent in agents:
        t = calc_action_history(agent, num)
        for action, count in t.items():
            if action not in result:
                result[action] = 0
            result[action] += count
    return result


def calc_overall_maintainance_agent_action_history(env, num=5):
    result = {}
    agents = [es.maintainance_agent for es in env.edge_servers.values()]
    for agent in agents:
        t = calc_action_history(agent, num)
        for action, count in t.items():
            if action not in result:
                result[action] = 0
            result[action] += count
    return result


def calc_overall_cache_event_history(env, num=20):
    result = {}
    ess = env.edge_servers.values()
    for es in ess:
        t = es.get_cache_event_history(num)
        for event, count in t.items():
            if event not in result:
                result[event] = 0
            result[event] += count
    return result


def calc_overall_maintainance_agent_reward(env):
    result = []
    for es in env.edge_servers.values():
        reward_history = es.maintainance_agent.reward_history
        reward = reward_history[-1] if reward_history else 0
        result.append(reward)
    avg = sum(result) / len(result)
    return avg


def calc_overall_cache_agent_reward(env):
    result = []
    for es in env.edge_servers.values():
        reward_history = es.cache_agent.reward_history
        reward = reward_history[-1] if reward_history else 0
        result.append(reward)
    avg = sum(result) / len(result)
    return avg


def cache_hit_status_to_percentage(status):
    summ = sum(status.values())
    for name, count in status.items():
        status[name] = count / (summ if summ else 1)
    return status


def obs2vector(obs):
    result = list(obs.values())
    # cast to float
    result = [float(x) for x in result]
    return result


if __name__ == "__main__":
    t = calc_distance((0, 0), (3, 4))
    print(t)

    import matplotlib.pyplot as plt

    result = []
    for _ in range(100):
        size = generate_size(0.1, 10)
        print(size)
        result.append(size)
    # 直方图
    plt.hist(result, bins=20)
    plt.show()
