import numpy as np
from config import LATEST_VERSION

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
    #print(np.unique(versions, return_counts=True))
    return versions[0]
