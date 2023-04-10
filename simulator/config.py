LATEST_VERSION = 5.0  # 最新版本号
SERVICE_COUNT = 1e4  # 服务数量
EDGE_SERVER_COUNT = 7  # 边缘服务器数量
USER_COUNT = 100  # 用户数量
FEATURE_VECTOR_SIZE = 256  # 特征向量维度
CANVAS_SIZE_X = 150  # 画布大小X轴(KM)
CANVAS_SIZE_Y = 50  # 画布大小Y轴(KM)
ENABLE_SLEEP = False  # 是否允许用户睡眠

ENABLE_NEW_SERVICE_UPLOAD = False  # 是否允许新服务上传
NEW_SERVICE_UPLOAD_PROBABILITY = 1e-3  # 一定概率有新服务上传
ENABLE_CHARM_CHANGE = True  # 是否允许服务魅力值变化
SERVICE_CHARM_CAUSAL_CHANGE_PROBABILITY = 1e-3
SERVICE_CHARM_ABRUPT_CHANGE_PROBABILITY = 1e-5

ENABLE_USER_CHANGE_FAVOR = True  # 是否允许用户偏好变化
USER_CHANGE_FAVOR_PROBABILITY = 1e-5
ENABLE_MAKE_TREND = True  # 是否允许人为造势
MAKE_TREND_PROBABILITY = 1e-4

DEBUG = True  # 是否开启调试模式(提高带宽)
ENABLE_VISUALIZATION = True  # 是否启动可视化
PRINT_DOWNLOAD_PERCENTAGE = False  # 打印下载进度
PRINT_CONN_STATUS = False  # 打印连接状态
PRINT_ES_STATUS = False  # 打印ES状态
PRINT_AGENT_STATUS = False  # 打印Agent状态
PRINT_USER_FETCH_PROCESS = False  # 打印用户获取服务过程

STEPPING = 1  # 步进

SAVE_MODEL = True  # 是否保存模型
LOAD_MODEL_FROM_FILE = True  # 是否从文件加载模型
