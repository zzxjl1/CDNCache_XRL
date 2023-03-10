import uuid
import random
from utils import generate_version, GB2MB, TB2GB


class EdgeServer():
    id_counter = 0

    def __init__(self,
                 use_uuid=False,
                 max_conn=200,
                 bandwidth=100,
                 speed_limit=-1,
                 stablity=0.99
                 ) -> None:
        if use_uuid:
            self.id = uuid.uuid4()
        else:
            self.id = EdgeServer.id_counter
            EdgeServer.id_counter += 1

        self.version = generate_version()  # 版本号（只能向下兼容）
        self.max_conn = max_conn  # 最大连接数
        self.conn_num = 0  # 当前连接数
        self.conns = []  # 当前连接列表

        # 随机生成地理位置
        x = random.uniform(0, 3e3)
        y = random.uniform(0, 1e3)
        self.location = (x, y)  # （10km）

        self.faulty = False  # 是否故障
        self.service_range = random.uniform(0.1, 1)  # 服务范围（10km）
        # 最大存储容量（mB）
        # 三级缓存形如(L1,L2,L3)，其中L1为内存，L2为SSD，L3为HDD
        L1 = random.choice([2, 3, 4, 8, 16, 24, 32])
        L2 = random.randint(128, 2*TB2GB)
        L3 = random.randint(2, 8)*TB2GB
        self.storage_size = (L1, L2, L3)
        L1_speed = random.randint(8, 40)*GB2MB
        L2_speed = random.randint(500, 2*GB2MB)
        L3_speed = random.randint(50, 300)
        self.storage_speed = (L1_speed, L2_speed, L3_speed)  # 磁盘读写速度（mB/s）

        self.bandwidth = bandwidth  # 最大吞吐量（mB/s）
        # 对每个用户的限速（mB/s）-1表示不限速
        self.speed_limit = speed_limit
        self.stablity = stablity  # 稳定性(模拟随机出错，拒绝服务)

        self.cache = {}  # 缓存

    def has_cache(self, service):
        return service.id in self.cache

    def add_to_cache(self, service):
        self.cache[service.id] = service

    def connect(self, conn):
        if self.conn_num >= self.max_conn:
            print(f"EdgeServer {self.id} reach max connections!")
            return False
        if self.faulty:
            print(f"EdgeServer {self.id} is faulty!")
            return False
        if random.random() > self.stablity:
            print(
                f"EdgeServer {self.id} is unstable and refused the connection！")
            return False
        self.conns.append(conn)
        self.conn_num += 1
        return True

    def simulate_speed_in_ms(self):
        pass

    def __str__(self) -> str:
        res = f"EdgeServer id：{self.id}\n"
        res += f"Version: {self.version}\n"
        res += f"Max connections: {self.max_conn}\n"
        res += f"Current connections: {self.conn_num}\n"
        res += f"Location: {self.location}\n"
        res += f"Faulty: {self.faulty}\n"
        res += f"Service range: {self.service_range} km\n"
        res += f"Storage (memory, SSD, HDD): {self.storage_size} GB\n"
        res += f"Storage speed (memory, SSD, HDD): {self.storage_speed} mB/s\n"
        res += f"Bandwidth: {self.bandwidth} mB/s\n"
        res += f"Speed limit: {self.speed_limit} mB/s\n"
        res += f"Stablity: {self.stablity}\n"

        return res


if __name__ == "__main__":
    edge = EdgeServer()
    print(edge)
