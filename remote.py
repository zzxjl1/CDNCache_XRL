"""
数据中心
我们的模型中只有一个数据中心，它上面包含了所有的服务。
"""

import random
from alive_progress import alive_bar
from service import Service


class DataCenter():
    def __init__(self, service_count):
        self.services = {}
        self.init_services(service_count)

    def init_services(self, service_count):
        count = int(service_count)
        with alive_bar(count, title=f'生成服务中') as bar:
            for _ in range(count):
                self.add_service()
                bar()
        print(f"{count} services created!")

    def add_service(self) -> Service:
        s = Service()
        # print(s)
        self.services[s.id] = s
        return s

    def get_random_services(self, count) -> list[Service]:
        """随机获取服务"""
        return random.sample(list(self.services.values()), count)
