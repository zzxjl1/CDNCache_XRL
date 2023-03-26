import math
import numpy as np
from simulator.config import LATEST_VERSION

GB2MB = 1000
TB2GB = 1000

SEC2MS = 1000
MIN2SEC = 60
HOUR2MIN = 60
DAY2HOUR = 24


def generate_version():
    """生成满足指数分布的版本号，即大部分用户使用的是最新版本，零星出现旧版本，越旧的版本越稀有"""

    scale = 8   # 尺度参数
    size = 1    # 生成 1 个版本号

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
    distance = math.sqrt((x1-x2)**2+(y1-y2)**2)
    return distance


def add_connection_history(connection_history, conn, max_len=200):
    connection_history.append(conn)
    if len(connection_history) > max_len:  # 保留最近n次连接
        connection_history.pop(0)


def calc_request_frequency(connection_history, num=10):
    if len(connection_history) <= 1:
        return 0
    connection_history = connection_history[-num:]
    total_time = connection_history[-1].birth - \
        connection_history[0].birth
    if total_time == 0:
        return 1e-3  # 防止除0错误
    return len(connection_history)/total_time*SEC2MS


def pop_expired_connection_history(connection_history, env, threshold=10*MIN2SEC*SEC2MS):
    for conn in connection_history:  # 删除超时的连接历史
        if env.now()-conn.birth > threshold:
            connection_history.remove(conn)


def overall_cache_miss_rate(env):
    """计算整体缓存未命中率"""
    t = [es.cache_miss_rate for es in env.edge_servers.values()]
    average = sum(t)/len(t)
    return average


def overall_storage_utilization(env):
    """计算整体存储利用率"""
    used, total = 0, 0
    for es in env.edge_servers.values():
        used += sum(es.storage_used())
        total += sum(es.storage_size)*GB2MB
    return used/total


if __name__ == "__main__":
    t = calc_distance((0, 0), (3, 4))
    print(t)
