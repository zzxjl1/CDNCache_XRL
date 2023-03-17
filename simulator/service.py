from faker import Faker
from utils import add_connection_history, calc_request_frequency, pop_expired_connection_history, GB2MB
import random
import numpy as np
from .config import FEATURE_VECTOR_SIZE

fake = Faker()


class Service():
    id_counter = 0

    def __init__(self,
                 name=None,
                 ) -> None:
        self.id = Service.id_counter
        Service.id_counter += 1
        self.name = name if name else fake.url()
        #self.version = generate_version()

        self.size = round(random.uniform(0.5, 10)*GB2MB)
        self.feature_vector = np.random.rand(FEATURE_VECTOR_SIZE)  # 描述服务的特征
        # 服务的魅力值(标准正态分布)
        self.charm = round(abs(np.random.standard_normal(1)[0]), 2)
        self.request_history = []  # 请求历史

    def add_history(self, history):
        self.request_history.append(history)
        if len(self.request_history) > 20:  # 保留最近20次连接
            self.request_history.pop(0)

    def causal_change(self):
        change_possibility = 1e-3
        if random.random() > change_possibility:
            return
        bias = random.uniform(-0.2, 0.2)
        self.charm += bias

    def abrupt_change(self):
        change_possibility = 1e-5
        if random.random() > change_possibility:
            return
        bias = random.uniform(1, 10) * random.choice([1, -1])
        self.charm += bias

    def become_charming(self):
        self.charm = random.uniform(3, 6)

    def add_history(self, conn):
        add_connection_history(self.request_history, conn)

    @property
    def request_frequency(self):
        return calc_request_frequency(self.request_history)

    def tick(self, env):
        self.causal_change()
        self.abrupt_change()
        pop_expired_connection_history(self.request_history, env)

    def show(self) -> str:
        res = f"Service id: {self.id}\n"
        res += f"Name: {self.name}\n"
        #res += f"Version: {self.version}\n"
        res += f"Size: {self.size} MB\n"
        res += f"Charm: {self.charm}\n"
        #res += f"Feature vector: {self.feature_vector}\n"
        return res


if __name__ == "__main__":
    s = Service()
    print(s.show())
