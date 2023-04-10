from utils import calc_distance
import random
from faker import Faker
import numpy as np
from .config import FEATURE_VECTOR_SIZE, CANVAS_SIZE_X, CANVAS_SIZE_Y, DEBUG, USER_CHANGE_FAVOR_PROBABILITY, ENABLE_SLEEP, ENABLE_USER_CHANGE_FAVOR, PRINT_USER_FETCH_PROCESS
from .connection import Connection
from utils import SEC2MS

faker = Faker()


def mutable_print(text):
    if not PRINT_USER_FETCH_PROCESS:
        return
    print(text)


class User():
    id_counter = 0

    def __init__(self, env):
        self.id = User.id_counter
        User.id_counter += 1
        self.name = hex(id(self))
        self.reset(env)

    def reset(self, env):
        self.is_idle = True  # 是否处于空闲（不在下载）状态
        self.generate_loc(env)  # 生成用户位置
        self.bandwidth = round(random.uniform(20, 100), 2)  # 用户带宽（mB/s）
        self.sleep_remaining = 0  # 睡眠剩余时间
        self.favor_vector = np.random.rand(FEATURE_VECTOR_SIZE)  # 描述偏好

        self.history = []  # 已经看过的 [IDS]
        self.connection = None  # 建立的连接

        self.sleep()

    def generate_loc(self, env):
        while True:
            x = random.uniform(0, CANVAS_SIZE_X)
            y = random.uniform(0, CANVAS_SIZE_Y)
            self.location = (x, y)  # 用户位置
            nearby_servers = self.find_nearby_servers(env)
            if len(nearby_servers) > 0:  # 确保都有边缘服务器覆盖
                break

    def find_nearby_servers(self, env):
        nearby_servers = []
        for edge_server in env.edge_servers.values():
            distance = calc_distance(self.location, edge_server.location)
            if distance > edge_server.service_range:  # 超出边缘服务器覆盖范围
                continue
            nearby_servers.append((edge_server, distance))
        # 按距离排序
        nearby_servers.sort(key=lambda x: x[1])

        return nearby_servers  # 缓存击穿，通过最近的边缘服务器请求数据中心

    def download(self, env, service):
        """开始下载"""
        mutable_print(f"{self} is downloading {service} ({service.size} MB)")
        self.is_idle = False
        nearby_servers = self.find_nearby_servers(env)

        text = f"{self} 在 {len(nearby_servers)} 个边缘服务器的覆盖范围内\n"
        text += f"距离由进到远依次为：{nearby_servers}"
        mutable_print(text)

        sources_with_cache = [
            source for source, _ in nearby_servers if source.has_cache(service)]
        mutable_print(
            f"{self} 在以下 {len(sources_with_cache)} 个边缘服务器的缓存中找到了 {service}：\n{sources_with_cache}")
        flag = False
        for source in sources_with_cache:  # 优先从缓存下载
            flag = self.create_connection(env, source, service)
            if flag:
                mutable_print(f"{self} 开始从缓存下载 {service}")
                break
        if not flag:  # 回源
            for source, distance in nearby_servers:
                mutable_print(f"{self} 击穿缓存，尝试从 {source} 回源")
                flag = self.create_connection(env, source, service)
                if flag:
                    break
                else:
                    mutable_print(f"{self}从 {source} 回源失败，尝试下一个ES")
        if not flag:  # 回源也全部失败
            self.is_idle = True
            mutable_print(f"No edge server available to {self}, fatal error!")

    def create_connection(self, env, source, service):
        """建立连接"""
        mutable_print(f"【创建连接】{self} is creating connection to {source}")
        self.connection = Connection(self, source, service, env.now())
        self.add_history(service)
        env.trend.update(env.timestamp, service)
        return self.connection.start(env)

    def download_progress_update(self, env):
        self.connection.tick(env)

    def sleep(self):
        if not ENABLE_SLEEP:  # 为了方便DEBUG
            return
        self.sleep_remaining = int(random.uniform(0, 5)*SEC2MS)
        mutable_print(
            f"【用户休眠了】{self} went to sleep for {self.sleep_remaining} Milliseconds")

    def download_finished(self):
        """用户下载完成"""
        mutable_print(
            f"【下载完成】{self} finished downloading {self.connection.service}!")
        self.is_idle = True
        self.sleep()  # 下载完成后休息一段时间

    def change_favor(self):
        """模拟一点点改变偏好"""
        if not ENABLE_USER_CHANGE_FAVOR:
            return
        if random.random() > USER_CHANGE_FAVOR_PROBABILITY:  # 概率
            return

        self.favor_vector += np.random.uniform(
            FEATURE_VECTOR_SIZE) * 1e-2

    def have_seen(self, service):
        return service.id in self.history

    def find_favorite_service(self, services):
        """找到最符合用户偏好的服务"""
        fav_service = None
        best_score = -1
        mutable_print(f"有 {len(services)} 个服务可供 {self} 选择")
        for service in services:
            already_seen = self.have_seen(service)
            if service.charm > 10 and not already_seen:  # 存在超高魅力值，直接选中
                mutable_print(
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
        mutable_print(
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
        mutable_print(f"{self} 将 {service} 标记为已看过")

    def tick(self, env):
        """时钟滴答"""
        if self.sleep_remaining > 0:  # 休息中
            self.sleep_remaining -= 1
            return
        self.change_favor()  # 偏好随时间一点点改变
        if self.is_idle:  # 空闲状态
            service = self.choose_service(env)
            self.download(env, service)
            mutable_print(
                f"【用户开始请求】{self} is downloading {self.connection.service}")
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
