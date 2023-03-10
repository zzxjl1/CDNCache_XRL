import numpy as np

from utils import SEC2MS, MIN2SEC, HOUR2MIN, DAY2HOUR


class Trend():
    def __init__(self) -> None:
        self.expire = 10*MIN2SEC*SEC2MS  # 10min
        self.click_history = []
        self.index2time = []
        self.top = []

    def update(self, timestamp, service, click_count=1):
        for _ in range(click_count):
            self.index2time.append(timestamp)
            self.click_history.append(service.id)

    def statistics(self):
        result = np.unique(self.click_history, return_counts=True)
        return zip(result[0], result[1])

    def get_top(self, n=50):
        result = self.statistics()
        result = sorted(result, key=lambda x: x[1], reverse=True)
        return result[:n]

    def is_popular(self, service):
        return service.id in self.top

    def mantain(self, env):
        while len(self.index2time) > 0:
            time = self.index2time[0]
            if env.now() - time > self.expire:
                self.index2time.pop(0)
                self.click_history.pop(0)
            else:
                break

    def tick(self, env):
        self.mantain(env)
        self.top = self.get_top()
