from service import Service
from alive_progress import alive_bar

SERVICE_COUNT = 1e4  # 服务数量
TIMESTAMP = 0  # 时间戳

SERVICES = {}


def init_services():
    count = int(SERVICE_COUNT)
    with alive_bar(count, title=f'生成服务中') as bar:
        for _ in range(count):
            s = Service()
            print(s)
            SERVICES[s.id] = s
            bar()
    print(f"{count} services created!")


if __name__ == "__main__":
    init_services()
