from utils import cache_hit_status_to_percentage, calc_action_history
from PPO import PPO
from utils import GB2MB
import os


class CacheAgent():
    def __init__(self, name, es, obs_dim=15) -> None:
        self.obs_dim = obs_dim
        self.es = es
        self.actions = ["IDLE", "L1", "L2", "L3"]
        self.action_dim = len(self.actions)
        self.save_dir = f"./models/cache_agent/{name}"
        self.agent = PPO(alpha=3e-4,
                         state_dim=self.obs_dim,
                         action_dim=self.action_dim,
                         fc1_dim=64,
                         fc2_dim=64,
                         ckpt_dir=self.save_dir,
                         gamma=0.99,
                         gae_lambda=0.95,
                         policy_clip=0.2,
                         n_epochs=10,
                         batch_size=256)
        self.count = 0
        self.last_timestamp = 0
        self.reward_history = []
        self.action_history = []
        self.success_history = []
        self.load()

    def choose_action(self, observation):
        # return 3
        return self.agent.choose_action(observation)

    def remember(self, state, action, probs, vals, reward, timestamp):
        done = timestamp < self.last_timestamp
        self.agent.remember(state, action, probs, vals, reward, done)
        self.count += 1
        self.last_timestamp = timestamp
        if self.count % 100 == 0:
            self.save()

    def learn(self):
        self.agent.learn()

    def save(self):
        # create dir if path not exists
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)
        self.agent.save_models()

    def load(self):
        self.agent.load_models()

    def generate_observation(self, env, conn):
        nearby_servers = conn.source.find_nearby_servers(env, 40)
        data = {
            # 当前ES的负载（按连接数计算）
            "es_load": conn.source.load,
            # 当前ES的L1剩余空间
            "free_storage_size_ratio_L1": conn.source.free_storage_size("L1")/conn.source.get_storage_size("L1"),
            # 当前ES的L2剩余空间
            "free_storage_size_ratio_L2": conn.source.free_storage_size("L2")/conn.source.get_storage_size("L2"),
            # 当前ES的L3剩余空间
            "free_storage_size_ratio_L3": conn.source.free_storage_size("L3")/conn.source.get_storage_size("L3"),
            # L1能放得下
            "can_L1_fit": conn.source.free_storage_size("L1") > conn.service.size,
            # L2能放得下
            "can_L2_fit": conn.source.free_storage_size("L2") > conn.service.size,
            # L3能放得下
            "can_L3_fit": conn.source.free_storage_size("L3") > conn.service.size,
            # 服务大小
            "service_size": conn.service.size/GB2MB,
            # 当前从ES下载的估计速度
            # "estimated_speed": conn.source.estimated_network_speed,
            # 预估回源用时
            "estimated_fetch_time": conn.source.estimated_network_speed/conn.service.size,
            # 是否流行
            "is_popular": env.trend.is_popular(conn.service),
            # 魅力值
            "charm": conn.service.charm,
            # 服务的短期被请求频率
            "service_request_frequency": conn.service.request_frequency,
            # 短距离（N km）内的ES个数
            "nearby_servers_count": len(nearby_servers),
            # 短距离（N km）内是否已有其它ES缓存
            "cached_in_nearby_servers": any([s.has_cache(conn.service) for s in nearby_servers]),
            # 该ES服务器被请求的频率
            "es_request_frequency": conn.source.request_frequency,
        }
        #print("Cache agent observation:", data)
        assert len(data) == self.obs_dim
        return data

    def execute_action(self, env, conn, action_index):
        action = self.actions[action_index]
        self.action_history.append(action)
        success = True
        if action == "IDLE":
            pass
        else:
            success = conn.source.add_to_cache(env, conn.service, action)
            self.success_history.append(success)
        return action, success

    def calc_reward(self, env, conn, action, success):
        es = conn.source

        action_history = self.action_history[-10:]
        action_cost = 1-action_history.count("IDLE") / len(action_history)

        success_history = self.success_history[-10:]
        success_rate = success_history.count(
            True) / len(success_history) if len(success_history) > 0 else 1

        cache_hit_status = cache_hit_status_to_percentage(es.cache_hit_status)
        score = cache_hit_status["L1"]*1 + \
            cache_hit_status["L2"]*0.5 + \
            cache_hit_status["L3"]*0.2

        cache_hit_rate = (1 - es.cache_miss_rate) * 100
        storage_utilization = es.storage_utilization * 100

        reward = cache_hit_rate * storage_utilization * score * action_cost * success_rate
        self.reward_history.append(reward)
        return reward


class MaintainanceAgent():
    def __init__(self, name, es, obs_dim=11) -> None:
        self.obs_dim = obs_dim
        self.es = es
        self.actions = ["PRESERVE", "DELETE"]
        self.action_dim = len(self.actions)
        self.save_dir = f"./models/maintainance_agent/{name}"
        self.agent = PPO(alpha=3e-4,
                         state_dim=self.obs_dim,
                         action_dim=self.action_dim,
                         fc1_dim=64,
                         fc2_dim=64,
                         ckpt_dir=self.save_dir,
                         gamma=0.99,
                         gae_lambda=0.95,
                         policy_clip=0.2,
                         n_epochs=10,
                         batch_size=1024)
        self.count = 0
        self.last_timestamp = 0
        self.reward_history = []
        self.action_history = []
        self.load()

    def choose_action(self, observation):
        # return 0
        return self.agent.choose_action(observation)

    def remember(self, state, action, probs, vals, reward, timestamp):
        done = timestamp < self.last_timestamp
        self.agent.remember(state, action, probs, vals, reward, done)
        self.count += 1
        self.last_timestamp = timestamp
        if self.count % 100 == 0:
            self.save()

    def learn(self):
        self.agent.learn()

    def save(self):
        # create dir if path not exists
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)
        self.agent.save_models()

    def load(self):
        self.agent.load_models()

    def generate_observation(self, es, service, ugent):
        cache_level = es.get_cache_level(service)
        services = es.cache[cache_level]
        services.sort(key=lambda s: s.request_frequency)
        result = {
            # "is_faulty": es.faulty,  # ES服务器是否故障
            # cache剩余空间百分比
            "free_space_ratio": es.free_storage_size(cache_level)/es.get_storage_size(cache_level),
            # 服务大小与总空间的比例
            "service_size_ratio": service.size/es.get_storage_size(cache_level),
            "cached_in_L1": cache_level == "L1",
            "cached_in_L2": cache_level == "L2",
            "cached_in_L3": cache_level == "L3",
            "service_charm": service.charm,  # 服务的魅力值
            "service_request_frequency": service.request_frequency,  # 服务的短期被请求频率
            "es_request_frequency": es.request_frequency,  # 该ES服务器被请求的频率
            "es_cache_miss_rate": es.cache_miss_rate,  # 该ES服务器缓存未命中率
            "least_freq_index": services.index(service),  # 该服务在缓存中按照请求频率的排序
            "is_ugent": ugent,  # 是否为紧急替换
        }
        #print("Maintainance agent observation:", result)
        assert len(result) == self.obs_dim
        return result

    def generate_observation_next(self, cache_level, es):
        services = es.cache[cache_level]
        result = {
            # cache剩余空间百分比
            "free_space_ratio": es.free_storage_size(cache_level)/es.get_storage_size(cache_level),
            # 服务大小与总空间的比例
            "service_size_ratio": 0,
            "cached_in_L1": False,
            "cached_in_L2": False,
            "cached_in_L3": False,
            "service_charm": 0,  # 服务的魅力值
            "service_request_frequency": 0,  # 服务的短期被请求频率
            "es_request_frequency": es.request_frequency,  # 该ES服务器被请求的频率
            # "es_cache_level": es.get_level_index(cache_level),  # 该ES服务器缓存级别
            "es_cache_miss_rate": es.cache_miss_rate,  # 该ES服务器缓存未命中率
            "least_freq_index": len(services),  # 该服务在缓存中按照请求频率的排序
            "is_ugent": False,  # 是否为紧急替换
        }
        print("Maintainance agent observation:", result)
        assert len(result) == self.obs_dim
        result = list(result.values())
        # cast to float
        result = [float(x) for x in result]
        return result

    def execute_action(self, es, service, action_index):
        action = self.actions[action_index]
        self.action_history.append(action)
        if action == "PRESERVE":
            pass
        elif action == "DELETE":
            print(f"【决定淘汰缓存】{service} 将从 {es} 中被淘汰")
            es.delete_from_cache(service)
        return action

    def calc_reward(self, env, es, service, action, cache_level):
        # 奖励函数，考虑 缓存命中率、动作的累计成本代价、存储空间利用率、QOS(下载速度、响应时间、剩余连接数)、负载均衡性、缓存级别
        free_ratio = es.free_storage_size(
            cache_level)/es.get_storage_size(cache_level)  # 剩余空间占比

        action_history = self.action_history[-10:]
        action_cost = action_history.count(
            "PRESERVE") / len(action_history)  # 惩罚淘汰，确保能量消耗最小

        cache_event_history = es.get_cache_event_history(num=10)
        anti_cache_full_rate = 1 - \
            cache_event_history["CACHE_FULL"] / \
            cache_event_history["CACHE_MISS"] if cache_event_history["CACHE_MISS"] != 0 else 1  # 惩罚缓存满，确保必要时能够淘汰

        cache_hit_rate = (1-es.cache_miss_rate)*100  # 缓存命中率
        storage_utilization = es.storage_utilization * 100  # 存储空间利用率

        reward = cache_hit_rate * storage_utilization * \
            (action_cost*free_ratio) * \
            (anti_cache_full_rate*(1-free_ratio))
        self.reward_history.append(reward)
        return reward  # TODO: CACHE_FULL_PENALTY
