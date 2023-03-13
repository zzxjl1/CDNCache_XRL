import uuid
import random
from utils import calc_distance, add_connection_history, calc_request_frequency, pop_expired_connection_history, GB2MB, TB2GB, SEC2MS, MIN2SEC
from .config import CANVAS_SIZE_X, CANVAS_SIZE_Y, DEBUG


class EdgeServer():
    id_counter = 0

    def __init__(self,
                 use_uuid=False,
                 max_conn=200,
                 bandwidth=10*GB2MB,
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
        self.service_range = random.randint(10, 50)  # 服务范围

        # 最大存储容量（mB）
        # 三级缓存形如(L1,L2,L3)，其中L1为内存，L2为SSD，L3为HDD
        L1 = random.choice([2, 3, 4, 8])
        L2 = random.choice([64, 128, 256])
        L3 = random.choice([200, 300, 500, 700, 1000])
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
        self.connection_history = []  # 连接历史

        if DEBUG:
            self.bandwidth *= 10

    @property
    def conn_num(self):
        return len(self.conns)+len(self.services_to_fetch)

    @property
    def load(self):
        return self.conn_num/self.max_conn

    @property
    def estimated_network_speed(self):
        if self.conn_num == 0:
            return self.bandwidth
        return self.bandwidth/self.conn_num

    def fetch_from_datacenter(self, service):
        if self.is_caching_service(service):
            print(f"{self} 已经在回源 {service}")
            return
        self.services_to_fetch.append(service)
        print(f"【开始回源】{self} start fetching {service} from remote!")

    def finish_fetch_from_datacenter(self, service):
        if not self.is_caching_service(service):
            return
        self.services_to_fetch.remove(service)
        print(f"【回源完成】{self} done fetching {service}, 接下来开始向用户传输！")

    def is_caching_service(self, service):
        for s in self.services_to_fetch:
            if s.id == service.id:
                return True
        return False

    def get_storage_size(self, level):
        index = list(self.cache.keys()).index(level)
        return self.storage_size[index]

    def storage_used(self, level):
        used = 0
        for service in self.cache[level]:
            used += service.size
        return used

    def free_storage_size(self, level=None):
        if level is None:
            return [self.free_storage_size(level) for level in self.cache.keys()]
        total = self.get_storage_size(level)*GB2MB
        return total-self.storage_used(level)

    def fetch_from_datacenter_speed(self):
        network_speed = self.estimated_network_speed
        return network_speed  # 每秒的速度

    def exceed_size_limit_with_service_added(self, service, level):
        return self.storage_used(level)+service.size > self.get_storage_size(level)*GB2MB

    def pop_least_frequently_requested(self, level):
        if len(self.cache[level]) == 0:
            return
        self.cache[level].sort(key=lambda s: s.request_frequency)
        self.cache[level].pop(0)
        print(f"【缓存警告】{self} 的 {level} CACHE 已满，正在删除最不常请求的服务！")

    def add_to_cache(self, env, service, level, overwrite=False):

        if service.size > self.get_storage_size(level)*GB2MB:
            env.reward_event("CACHE_FULL")
            print(f"【容量警告】{service} 超出 {self} 的 {level} CACHE 最大容量")
            return

        if self.exceed_size_limit_with_service_added(service, level):
            print(f"【容量警告】{self} 的 {level} CACHE 已满，无法添加 {service}")
            if overwrite:
                self.pop_least_frequently_requested(level)
                self.add_to_cache(env, service, level, overwrite)
            else:
                env.reward_event("CACHE_FULL")
                return

        if self.has_cache(service):  # 如果已经在缓存中
            already_in_cache_level = self.get_cache_level(service)
            if already_in_cache_level == level:  # 如果已经在缓存中的位置和要添加的位置一样
                print(f"{service}已经在 {self} 的 {level} CACHE 中了，无需重复添加")
                env.reward_event("CACHE_DUPLICATE")

            else:  # 如果已经在缓存中的位置和要添加的位置不一样
                print(
                    f"{service}已经在 {self} 的 {already_in_cache_level} CACHE 中，正在将其移动到 {level} CACHE")
                self.delete_from_cache_level(
                    service, already_in_cache_level)  # 先删除

        self.cache[level].append(service)
        print(f"【添加缓存】 {self} 存储 {service} 到 {level} CACHE")

    def delete_from_cache(self, service):
        for level in self.cache.keys():
            self.delete_from_cache_level(service, level)

    def delete_from_cache_level(self, service, level):
        if service in self.cache[level]:
            self.cache[level].remove(service)
            print(f"【删除缓存】 {self} 删除 {level} CACHE 中的 {service}")

    def count_conn_by_cache_level(self, level):
        count = 0
        for conn in self.conns:
            if conn.cache_level == level:
                count += 1
        return count

    def get_cache_speed(self, level):
        index = list(self.cache.keys()).index(level)
        return self.storage_speed[index]

    def get_estimated_cache_speed(self, level):
        return self.get_cache_speed(level)/(self.count_conn_by_cache_level(level)+1)

    def get_estimated_download_speed_with_cache(self, level):  # 有缓存情况下的速度
        network_speed = self.estimated_network_speed
        cache_speed = self.get_estimated_cache_speed(level)
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

    def add_history(self, conn):
        add_connection_history(self.connection_history, conn)

    @property
    def request_frequency(self):
        return calc_request_frequency(self.connection_history)

    def tick(self, env):
        pop_expired_connection_history(self.connection_history, env)

        # if random.random() < 1e-8:
        #    self.faulty = True

        if random.random() < 1e-5:
            print(f"【ES状态】{self}: {self.conn_num}/{self.max_conn} connections, {self.load*100:.2f}% load, {self.request_frequency:.2f} req/s, estimated network speed {self.estimated_network_speed:.2f} mB/s, {self.free_storage_size('L1'):.2f} mB free in L1, {self.free_storage_size('L2'):.2f} mB free in L2, {self.free_storage_size('L3'):.2f} mB free in L3, {len(self.services_to_fetch)} 个服务正在回源")

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
        self.add_history(conn)
        return True

    def disconnect(self, conn) -> bool:
        if conn not in self.conns:
            print(f"failed to close, {self} does not have this connection!")
            return False
        self.conns.remove(conn)
        return True

    def find_nearby_servers(self, env, max_distance):
        nearby_servers = []
        for server in env.edge_servers:
            if server.id == self.id:
                continue
            if calc_distance(server.location, self.location) <= max_distance:
                nearby_servers.append(server)
        return nearby_servers

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
