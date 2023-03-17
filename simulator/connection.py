import random
from .edge import EdgeServer
from .service import Service
from utils import SEC2MS, calc_distance
from .config import DEBUG
from enum import Enum


class ConnectionStatus(Enum):
    PENDING = 0
    ESTABLISHED = 1
    FAILED = 2
    FINISHED = 3


class Connection():
    def __init__(self, user, source: EdgeServer, service: Service, now) -> None:
        self.status = None

        self.birth = now  # 连接开始时间
        self.download_start = 0  # 下载开始时间

        self.downloaded = 0  # 已经下载的大小（MB）
        self.user = user  # 创建连接的用户
        self.service = service  # 正在下载的服务
        self.source = source  # 正在下载的服务的源服务器
        self.distance = calc_distance(
            self.user.location, self.source.location)  # 距离
        self.delays = {
            "propagation_delay": 0,  # 传播延迟
        }
        self.cached = self.source.has_cache(self.service)  # 是否有缓存
        self.cache_level = self.source.get_cache_level(
            self.service) if self.cached else None
        self.es_fetch_remaining_size = 0  # ES从远程下载，还剩多少数据
        self.es_fetching_from_remote = False  # ES是否正在从远程下载

        self.calc_latency()
        self.cached_initally = self.cached

    def set_status(self, status):
        self.status = status
        print(
            f"connection from {self.user} to {self.source} {status}!")

    def send_reward(self, env):
        t = "CACHE_HIT" if self.cached else "CACHE_MISS"
        d = self.cache_level
        env.reward_event(t, d)

    def start(self, env) -> bool:
        self.set_status(ConnectionStatus.PENDING)
        flag = self.source.connect(self)
        self.service.add_history(self)
        env.request_callback(self)
        self.send_reward(env)
        if not flag:
            self.set_status(ConnectionStatus.FAILED)
            env.reward_event("FAILED_TO_CONNECT")
        return flag

    def close(self):
        self.source.disconnect(self)

    def calc_latency(self):
        """计算各种延迟"""
        self.delays["propagation_delay"] = random.uniform(1, 10)  # ms

    def print_download_percentage(self, master, file, now, total, speed, str=""):
        if DEBUG:
            return
        percentage = round(now/total*100)
        if random.random() < 5e-4:
            print(
                f"{str}{master} downloading {file}, [{now:.2f}MB/{total}MB],{speed:.2f}MB/S, {percentage}%")

    def calc_download_speed(self) -> float:
        """计算下载速度"""

        # 如果没有缓存，需要先等待下载到ES
        if not self.cached:
            if not self.es_fetching_from_remote:
                self.es_fetching_from_remote = True
                self.es_fetch_remaining_size = self.service.size
                self.source.fetch_from_datacenter(self.service)

            speed = self.source.fetch_from_datacenter_speed()
            # 加入随机因素
            speed *= random.uniform(0.8, 1.2)
            self.es_fetch_remaining_size -= speed/SEC2MS
            self.print_download_percentage(master=self.source,
                                           file=self.service,
                                           now=self.service.size -
                                           self.es_fetch_remaining_size,
                                           total=self.service.size,
                                           speed=speed,
                                           str="【ES回源中】")
            if self.es_fetch_remaining_size <= 0:
                self.cached = True
                self.cache_level = "L1"
                self.es_fetching_from_remote = False
                self.es_fetch_remaining_size = 0
                self.source.finish_fetch_from_datacenter(self.service)

            return 0

        else:
            # 如果有缓存，速度取决于缓存的位置、ES负载、ES带宽、用户带宽、ES限速、距离
            speed = self.source.get_estimated_download_speed_with_cache(
                self.cache_level)
            # 距离越远，速度越慢
            speed *= 1 - self.distance / 200
            if speed > self.user.bandwidth:  # 速度不能超过用户带宽
                speed = self.user.bandwidth
            # 加入随机因素
            speed *= random.uniform(0.8, 1.2)
            return speed

    def tick(self, env):
        """时钟滴答"""
        now = env.now()
        if self.status == ConnectionStatus.PENDING:
            if now - self.birth < self.delays["propagation_delay"]:  # 等待传播延迟
                return
            self.download_start = env.now()
            self.set_status(ConnectionStatus.ESTABLISHED)

        elif self.status == ConnectionStatus.ESTABLISHED:
            download_speed = self.calc_download_speed()  # mB/s 上一个时间片下载了多大
            if self.es_fetching_from_remote:
                return
            self.downloaded += download_speed/SEC2MS
            self.print_download_percentage(master=self.user,
                                           file=self.service,
                                           now=self.downloaded,
                                           total=self.service.size,
                                           speed=download_speed,
                                           str="【用户从ES下载】")
            if self.downloaded >= self.service.size:
                self.status = ConnectionStatus.FINISHED
                self.user.download_finished()
                self.close()
