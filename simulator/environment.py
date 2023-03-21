from alive_progress import alive_bar
from faker import Faker
from .trend import Trend
from .remote import DataCenter
from .edge import EdgeServer
from .user import User
from .config import SERVICE_COUNT, EDGE_SERVER_COUNT, USER_COUNT, NEW_SERVICE_UPLOAD_PROBABILITY, MAKE_TREND_PROBABILITY
import random

fake = Faker()


class Environment():
    def reward_event(self, t, d=None):  # 奖励事件回调函数
        pass

    def cache_miss_callback(self, connection):  # 缓存未命中回调函数
        pass

    def request_callback(self, connection):  # 请求回调函数
        pass

    def service_maintainance_callback(self, es, service):  # 服务维护回调函数
        pass

    def __init__(self):
        self.timestamp = 0  # 时间戳(ms)
        self.pause_flag = False  # 暂停标志
        self.edge_servers = []  # 边缘服务器集
        self.users = []  # 用户集
        self.trend = Trend()  # 时下流行

        self.init_edge_servers()
        self.init_users()

        self.data_center = DataCenter(SERVICE_COUNT)  # 数据中心

    def init_edge_servers(self):
        for _ in range(EDGE_SERVER_COUNT):
            self.edge_servers.append(EdgeServer())
        print(f"{EDGE_SERVER_COUNT} edge servers created!")

    def init_users(self):
        with alive_bar(USER_COUNT, title=f'生成用户中') as bar:
            while True:
                if len(self.users) == USER_COUNT:  # 生成了足够的用户数量
                    break
                user = User()
                nearby_servers = user.find_nearby_servers(self)
                if len(nearby_servers) > 0:  # 确保都有边缘服务器覆盖
                    self.users.append(user)
                    bar()
        print(f"{USER_COUNT} users created!")

    def make_trend(self, n=None):
        """人为造势"""
        possibility = MAKE_TREND_PROBABILITY
        if random.random() > possibility:
            return

        if not n:
            new_hot_service_num = random.randint(0, 10)
        new_hot_services = self.data_center.get_random_services(
            new_hot_service_num)
        for service in new_hot_services:
            click_count = random.randint(100, 1000)
            self.trend.update(self.timestamp, service, click_count)
            service.become_charming()
        print(f"以下{new_hot_service_num} 个服务因为人工造势火了:{new_hot_services}")

    def tick(self):
        """时钟滴答"""
        if self.timestamp % 100 == 0:
            print(f"Timestamp: {self.timestamp} Millisecond")

        if random.random() < NEW_SERVICE_UPLOAD_PROBABILITY:  # 一定概率有新服务上传
            new_upload_num = random.randint(0, 10)
            for _ in range(new_upload_num):
                self.data_center.add_service()  # 新服务诞生
            print(f"{new_upload_num} new services uploaded!")

        for user in self.users:  # 刷新用户的状态
            user.tick(self)

        for service in self.data_center.services.values():  # 刷新服务的状态
            service.tick(self)

        for edge_server in self.edge_servers:  # 刷新边缘服务器的状态
            edge_server.tick(self)

        self.make_trend()
        self.trend.tick(self)

        self.timestamp += 1

    def now(self):
        return self.timestamp

    def get_service_by_id(self, service_id):
        return self.data_center.services[service_id]

    def pause(self):
        self.pause_flag = True

    def resume(self):
        self.pause_flag = False


env = Environment()
