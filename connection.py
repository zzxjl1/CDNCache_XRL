from enum import Enum


class ConnectionStatus(Enum):
    PENDING = 0
    ESTABLISHED = 1
    CLOSED = 2


class Connection():
    def __init__(self, user, source, service) -> None:
        self.status = ConnectionStatus.PENDING

        self.start = 0  # 连接开始时间
        self.downloaded = 0  # 已经下载的大小（MB）
        self.user = user  # 创建连接的用户
        self.service = service  # 正在下载的服务
        self.source = source  # 正在下载的服务的源服务器

    def tick(self, env):
        """时钟滴答"""
        if self.status == ConnectionStatus.PENDING:
            self.start = env.now()
            self.status = ConnectionStatus.ESTABLISHED
        elif self.status == ConnectionStatus.ESTABLISHED:
            self.downloaded += self.source.download_speed
            if self.downloaded >= self.service.size:
                self.status = ConnectionStatus.CLOSED
                self.user.finish_download(self)
        elif self.status == ConnectionStatus.CLOSED:
            pass
