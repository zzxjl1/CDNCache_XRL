import numpy as np

from utils import SEC2MS, MIN2SEC, HOUR2MIN, DAY2HOUR


class Trend():
    def __init__(self) -> None:
        self.expire = 1*MIN2SEC*SEC2MS  # 1min
        self.click_history_ids = []
        self.index2time = []
        self.top = []

    def update(self, timestamp, service, click_count=1):
        for _ in range(click_count):
            self.index2time.append(timestamp)
            self.click_history_ids.append(service.id)

    def statistics(self):

        result = np.unique(self.click_history_ids, return_counts=True)
        return zip(result[0], result[1])

    def calc_top(self, env, n=50):
        result = self.statistics()
        result = sorted(result, key=lambda x: x[1], reverse=True)[:n]
        ids = [x[0] for x in result]
        final_result = [env.get_service_by_id(id) for id in ids]
        #print(f"Most popular services: {final_result}")
        return final_result

    def is_popular(self, service):
        return service.id in self.top

    def mantain(self, env):
        while len(self.index2time) > 0:
            time = self.index2time[0]
            if env.now() - time > self.expire:
                self.index2time.pop(0)
                self.click_history_ids.pop(0)
            else:
                break

    def tick(self, env):
        self.mantain(env)
        self.top = self.calc_top(env)
