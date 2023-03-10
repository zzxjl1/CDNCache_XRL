from trend import Trend
from remote import DataCenter
from edge import EdgeServer
from user import User
from faker import Faker
from config import SERVICE_COUNT, EDGE_SERVER_COUNT, USER_COUNT
import random

fake = Faker()


class Environment():

    def __init__(self):
        self.timestamp = 0  # 时间戳(ms)

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
        for _ in range(USER_COUNT):
            self.users.append(User())
        print(f"{USER_COUNT} users created!")

    def make_trend(self, n=None):
        """人为造势"""
        possibility = 1e-2
        if random.random() > possibility:
            return

        if not n:
            new_hot_service_num = random.randint(0, 10)
        new_hot_services = self.data_center.get_random_services(
            new_hot_service_num)
        for service in new_hot_services:
            click_count = random.randint(100, 1000)
            self.trend.update(self.timestamp, service, click_count)
        print(f"{new_hot_service_num} 个服务因为人工造势火了!")

    def tick(self):
        """时钟滴答"""
        print(f"Time: {self.timestamp}")

        if random.random() < 0.2:  # 一定概率有新服务上传
            new_upload_num = random.randint(0, 100)
            for _ in range(new_upload_num):
                self.data_center.add_service()  # 新服务诞生
            print(f"{new_upload_num} new services uploaded!")

        for user in self.users:  # 刷新用户的状态
            user.tick(self)

        for service in self.data_center.services.values():  # 刷新服务的状态
            service.tick(self)

        self.make_trend()
        self.trend.tick(self)

        self.timestamp += 1

    def now(self):
        return self.timestamp


env = Environment()

if __name__ == "__main__":
    import time
    while True:
        env.tick()
        # time.sleep(1)
