import numpy as np

GB2MB = 1000
TB2GB = 1000


def generate_version(latest_version=5.0):
    scale = 8   # 尺度参数
    size = 1    # 生成 1 个版本号

    min_version = latest_version - 3  # 最小版本号
    if min_version < 0:
        min_version = 0
    # 使用 numpy 库中的指数分布函数生成版本号
    versions = np.random.exponential(scale, size) + min_version
    # 将版本号四舍五入到整数
    versions = np.round(versions, 1)
    # 所有大于 5 的版本号都设置为 5.0
    versions[versions > latest_version] = latest_version

    # print(versions)
    # 统计每个版本号出现的次数
    #print(np.unique(versions, return_counts=True))
    return versions[0]
