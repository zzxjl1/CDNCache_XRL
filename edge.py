import uuid
import random
from utils import SEC2MS, generate_version, GB2MB, TB2GB
from config import CANVAS_SIZE_X, CANVAS_SIZE_Y


class EdgeServer():
    id_counter = 0

    def __init__(self,
                 use_uuid=False,
                 max_conn=200,
                 bandwidth=1000,
                 speed_limit=-1,
                 stablity=0.99
                 ) -> None:
        if use_uuid:
            self.id = uuid.uuid4()
        else:
            self.id = EdgeServer.id_counter
            EdgeServer.id_counter += 1

        # self.version = generate_version()  # 版本号（只能向下兼容）
        self.max_conn = max_conn  # 最大连接数
        self.conns = []  # 提供服务的连接

        # 随机生成地理位置
        x = random.uniform(0, CANVAS_SIZE_X)
        y = random.uniform(0, CANVAS_SIZE_Y)
        self.location = (x, y)

        self.faulty = False  # 是否故障
        self.service_range = random.randint(1, 100)  # 服务范围
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

        self.cache = {
            "L1": [],  # 内存
            "L2": [],  # SSD
            "L3": [],  # HDD
        }  # 缓存
        self.services_to_fetch = []  # 等待从数据中心获取的服务

    @property
    def conn_num(self):
        return len(self.conns)+len(self.services_to_fetch)

    def fetch_from_datacenter_speed(self):
        network_speed = self.bandwidth/self.conn_num  # 带宽/连接数
        return network_speed  # 每秒的速度

    def add_to_cache(self, service, level):
        pass

    def delete_from_cache(self, service):
        pass

    def get_free_space(self):
        pass

    def count_conn_by_cache_level(self, level):
        count = 0
        for conn in self.conns:
            if conn.cache_level == level:
                count += 1
        return count

    def get_cache_speed(self, level):
        mapping = {
            "L1": 0,
            "L2": 1,
            "L3": 2,
        }
        return self.storage_speed[mapping[level]]

    def get_available_speed_with_cache(self, conn):  # 有缓存情况下的速度
        network_speed = self.bandwidth/self.conn_num  # 带宽/连接数
        cache_level = conn.cache_level
        cache_speed = self.get_cache_speed(cache_level)/self.count_conn_by_cache_level(
            cache_level)
        speed = min(network_speed, cache_speed)

        if self.speed_limit != -1:  # 速度不能超过ES限速
            speed = min(speed, self.speed_limit)

        return speed

    def has_cache(self, service) -> bool:
        for _, data in self.cache.items():
            if service in data:
                return True
        return False

    def get_cache_level(self, service) -> str:
        for level, data in self.cache.items():
            if service in data:
                return level

    def add_to_cache(self, service):
        self.cache[service.id] = service

    def connect(self, conn) -> bool:
        if self.conn_num >= self.max_conn:
            print(f"{self} reach max connections!")
            return False
        if self.faulty:
            print(f"{self} is faulty!")
            return False
        if random.random() > self.stablity:
            print(
                f"{self} is unstable and refused the connection！")
            return False
        self.conns.append(conn)
        return True

    def disconnect(self, conn) -> bool:
        if conn not in self.conns:
            print(f"failed to close, {self} does not have this connection!")
            return False
        self.conns.remove(conn)
        return True

    def show(self) -> str:
        res = f"EdgeServer id：{self.id}\n"
        #res += f"Version: {self.version}\n"
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
