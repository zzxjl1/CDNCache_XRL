from utils import calc_distance
import random
from faker import Faker
import numpy as np
from .config import FEATURE_VECTOR_SIZE, CANVAS_SIZE_X, CANVAS_SIZE_Y, DEBUG
from .connection import Connection
from utils import SEC2MS

faker = Faker()


class User():
    id_counter = 0

    def __init__(self):
        self.id = User.id_counter
        User.id_counter += 1
        self.name = faker.name()
        self.is_idle = True  # 是否处于空闲（不在下载）状态
        x = random.uniform(0, CANVAS_SIZE_X)
        y = random.uniform(0, CANVAS_SIZE_Y)
        self.location = (x, y)  # 用户位置
        self.bandwidth = round(random.uniform(20, 100), 2)  # 用户带宽（mB/s）
        self.sleep_remaining = 0  # 睡眠剩余时间
        self.favor_vector = np.random.rand(FEATURE_VECTOR_SIZE)  # 描述偏好
        self.change_favor_posssibility = 1e-5  # 用户改变偏好的概率

        self.history = []  # 已经看过的 [IDS]
        self.connection = None  # 建立的连接

        self.sleep()

        if DEBUG:
            self.bandwidth *= 1000

    def find_nearby_servers(self, env):

        nearby_servers = []
        for edge_server in env.edge_servers:
            distance = calc_distance(self.location, edge_server.location)
            if distance > edge_server.service_range:  # 超出边缘服务器覆盖范围
                continue
            nearby_servers.append((edge_server, distance))
        # 按距离排序
        nearby_servers.sort(key=lambda x: x[1])

        return nearby_servers  # 缓存击穿，通过最近的边缘服务器请求数据中心

    def download(self, env, service):
        """开始下载"""
        print(f"{self} is downloading {service} ({service.size} MB)")
        self.is_idle = False
        nearby_servers = self.find_nearby_servers(env)

        text = f"{self} 在 {len(nearby_servers)} 个边缘服务器的覆盖范围内\n"
        text += f"距离由进到远依次为：{nearby_servers}"
        print(text)

        sources_with_cache = [
            source for source, _ in nearby_servers if source.has_cache(service)]
        print(
            f"{self} 在以下 {len(sources_with_cache)} 个边缘服务器的缓存中找到了 {service}：\n{sources_with_cache}")
        flag = False
        for source in sources_with_cache:  # 优先从缓存下载
            flag = self.create_connection(env, source, service)
            if flag:
                print(f"{self} 开始从缓存下载 {service}")
                break
        if not flag:  # 回源
            for source, distance in nearby_servers:
                print(f"{self} 击穿缓存，尝试从 {source} 回源")
                flag = self.create_connection(env, source, service)
                if flag:
                    break
                else:
                    print(f"{self}从 {source} 回源失败，尝试下一个ES")
        if not flag:  # 回源也全部失败
            self.is_idle = True
            print(f"No edge server available to {self}, fatal error!")

    def create_connection(self, env, source, service):
        """建立连接"""
        print(f"【创建连接】{self} is creating connection to {source}")
        self.connection = Connection(self, source, service, env.now())
        self.add_history(service)
        env.trend.update(env.timestamp, service)
        return self.connection.start(env)

    def download_progress_update(self, env):
        self.connection.tick(env)

    def sleep(self):
        if DEBUG:  # 为了方便DEBUG
            return
        self.sleep_remaining = int(random.uniform(0, 5)*SEC2MS)
        print(
            f"【用户休眠了】{self} went to sleep for {self.sleep_remaining} Milliseconds")

    def download_finished(self):
        """用户下载完成"""
        print(f"【下载完成】{self} finished downloading {self.connection.service}!")
        self.is_idle = True
        self.sleep()  # 下载完成后休息一段时间

    def change_favor(self):
        """模拟一点点改变偏好"""
        if random.random() > self.change_favor_posssibility:  # 概率
            return

        self.favor_vector += np.random.uniform(
            FEATURE_VECTOR_SIZE) * 1e-2

    def have_seen(self, service):
        return service.id in self.history

    def find_favorite_service(self, services):
        """找到最符合用户偏好的服务"""
        fav_service = None
        best_score = -1
        print(f"有 {len(services)} 个服务可供 {self} 选择")
        for service in services:
            already_seen = self.have_seen(service)
            if service.charm > 10 and not already_seen:  # 存在超高魅力值，直接选中
                print(
                    f"【服务被选择】{service} with super high charm {service.charm} got selected by {self}!")
                return service
            # 依据喜好和服务魅力打分
            score = np.sum(np.absolute(self.favor_vector -
                                       service.feature_vector))*service.charm
           # if already_seen:
           #     #score = float("-inf")
           #     print(f"{self} 已经看过 {service}了，因此兴趣减半")
           #     score /= 2
            if score > best_score:
                best_score = score
                #print(best_score, service)
                fav_service = service
        print(
            f"【服务被选择】{fav_service} got selected by {self} with favor score {best_score}")
        return fav_service

    def choose_service(self, env):
        # return env.data_center.get_random_services(1)[0] # 随机选择一个服务
        ramdom_services = env.data_center.get_random_services(
            100)  # 用户会自己翻n个服务
        top_services = env.trend.top  # 从趋势中找到最热门的服务
        services = ramdom_services + top_services
        # 从中找到最符合自己偏好的
        service = self.find_favorite_service(services)

        return service

    def add_history(self, service):
        if len(self.history) > 10:
            self.history.pop(0)
        self.history.append(service.id)  # 标记为已看过的
        print(f"{self} 将 {service} 标记为已看过")

    def tick(self, env):
        """时钟滴答"""
        if self.sleep_remaining > 0:  # 休息中
            self.sleep_remaining -= 1
            return
        self.change_favor()  # 偏好随时间一点点改变
        if self.is_idle:  # 空闲状态
            service = self.choose_service(env)
            self.download(env, service)
            print(f"【用户开始请求】{self} is downloading {self.connection.service}")
        else:  # 下载中
            self.download_progress_update(env)

    def show(self) -> str:
        res = f"User id: {self.id}\n"
        res += f"Name: {self.name}\n"
        res += f"Bandwidth: {self.bandwidth} MB/s\n"
        res += f"Location: {self.location}\n"
        res += f"Is idle: {self.is_idle}\n"
        return res


if __name__ == "__main__":
    u = User()
    print(u)
