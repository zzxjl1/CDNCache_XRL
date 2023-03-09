from remote import DataCenter

LATEST_VERSION = 5.0  # 最新版本号
SERVICE_COUNT = 1e5  # 服务数量
TIMESTAMP = 0  # 时间戳

if __name__ == "__main__":
    data_center = DataCenter(SERVICE_COUNT)
