import math
import random
from faker import Faker
import numpy as np
from config import FEATURE_VECTOR_SIZE
from connection import Connection
from utils import SEC2MS

faker = Faker()


class User():
    id_counter = 0

    def __init__(self):
        self.id = User.id_counter
        User.id_counter += 1
        self.name = faker.name()
        self.is_idle = True  # 是否处于空闲（不在下载）状态
        x = random.randint(0, 3e3)
        y = random.randint(0, 1e3)
        self.location = (x, y)  # 用户位置
        self.bandwidth = round(random.uniform(1, 50), 2)  # 用户带宽（mB/s）
        self.sleep_remaining = 0  # 睡眠剩余时间
        self.favor_vector = np.random.rand(FEATURE_VECTOR_SIZE)  # 描述偏好
        self.change_favor_posssibility = 1e-3  # 用户改变偏好的概率

        self.history = []  # 已经看过的 [IDS]
        self.connection = None  # 建立的连接

    def find_source(self, env, service):
        """找到从哪台服务器下载"""
        print(f"User {self.id} is downloading {service.name} {service.size} MB")
        self.is_idle = False

        # 请求边缘服务器
        nearby_servers = []
        for edge_server in env.edge_servers:
            x1, y1 = self.location
            x2, y2 = edge_server.location
            distance = math.sqrt((x1-x2)**2+(y1-y2)**2)
            if distance > edge_server.service_range:  # 超出边缘服务器覆盖范围
                continue
            nearby_servers.append((edge_server, distance))
        # 按距离排序
        nearby_servers.sort(key=lambda x: x[1])

        for edge_server, _ in nearby_servers:
            if edge_server.has_cache(service):
                flag = True
                return edge_server

        print(f"nearby edge servers cache miss!")
        return env.data_center  # 缓存击穿，请求数据中心

    def download(self, env, service):
        """开始下载"""
        source = self.find_source(env, service)
        # 建立连接
        self.connection = Connection(self, source, service)
        self.add_history(service)
        env.trend.update(env.timestamp, service)

    def download_progress_update(self, env):
        self.connection.tick(env)

    def download_finished(self, env):
        """用户下载完成"""
        print(
            f"User {self.id} finished downloading!")
        self.is_idle = True
        self.sleep_remaining = random.randint(1, 10)*SEC2MS  # 下载完成后休息一段时间

    def change_favor(self):
        """模拟一点点改变偏好"""
        if random.random() > self.change_favor_posssibility:  # 概率
            return

        self.favor_vector += np.random.standard_normal(
            FEATURE_VECTOR_SIZE) * 1e-2

    def find_favorite_service(self, services):
        """找到最符合用户偏好的服务"""
        fav_service = None
        best_score = -1
        for service in services:
            if service.charm > 5:  # 存在超高魅力值，直接选中
                return service
            # 依据喜好和服务魅力打分
            score = abs(np.sum(self.favor_vector -
                               service.feature_vector))*service.charm
            if service.id in self.history:
                #score = float("-inf")
                score /= 2
            if score > best_score:
                best_score = score
                # print(best_score)
                fav_service = service
        return fav_service

    def choose_service(self, env):
        ramdom_services = env.data_center.get_random_services(
            200)  # 用户会自己翻200个服务
        top_services = env.trend.top  # 从趋势中找到最热门的服务
        services = ramdom_services + top_services
        # 从中找到最符合自己偏好的
        service = self.find_favorite_service(services)

        return service

    def add_history(self, service):
        if len(self.history) > 10:
            self.history.pop(0)
        self.history.append(service.id)  # 标记为已看过的

    def tick(self, env):
        """时钟滴答"""
        if self.sleep_remaining > 0:  # 休息中
            self.sleep_remaining -= 1
            return
        self.change_favor()  # 偏好随时间一点点改变
        if self.is_idle:  # 空闲状态
            service = self.choose_service(env)
            self.download(env, service)
        else:  # 下载中
            self.download_progress_update(env)

    def __str__(self) -> str:
        res = f"User id: {self.id}\n"
        res += f"Name: {self.name}\n"
        res += f"Bandwidth: {self.bandwidth} MB/s\n"
        res += f"Location: {self.location}\n"
        res += f"Is idle: {self.is_idle}\n"
        return res


if __name__ == "__main__":
    u = User()
    print(u)
