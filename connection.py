from utils import calc_distance
from enum import Enum


class ConnectionStatus(Enum):
    PENDING = 0
    ESTABLISHED = 1
    CLOSED = 2


class Connection():
    def __init__(self, user, source, service, now) -> None:
        self.status = ConnectionStatus.PENDING

        self.birth = now  # 连接开始时间
        self.download_start = 0  # 下载开始时间

        self.downloaded = 0  # 已经下载的大小（MB）
        self.user = user  # 创建连接的用户
        self.service = service  # 正在下载的服务
        self.source = source  # 正在下载的服务的源服务器
        self.distance = calc_distance(
            self.user.location, self.source.location)  # 距离（10km）
        self.delays = {
            "propagation_delay": 0,  # 传播延迟
        }

        self.calc_latency()

    def start(self):
        flag = self.source.connect(self)
        if flag:
            print(
                f"connection from {self.user.id} to {self.source.id} ESTABLISHED!")
        return flag

    def calc_latency(self):
        """计算各种延迟"""
        speed_of_light = 3e8  # 光速（m/s）
        self.delays["propagation_delay"] = self.distance * \
            10 * 1e3 / speed_of_light * 1e3  # ms

    def tick(self, env):
        """时钟滴答"""
        now = env.now()
        if self.status == ConnectionStatus.PENDING:
            if now - self.birth < self.delays["propagation_delay"]:
                return
            self.download_start = env.now()
            self.status = ConnectionStatus.ESTABLISHED
        elif self.status == ConnectionStatus.ESTABLISHED:
            self.downloaded += self.source.download_speed
            if self.downloaded >= self.service.size:
                self.status = ConnectionStatus.CLOSED
                self.user.finish_download(self)
        elif self.status == ConnectionStatus.CLOSED:
            pass
