from utils import cache_hit_status_to_percentage
from D3QN import D3QN
from utils import overall_cache_miss_rate, overall_storage_utilization
import os


class CacheAgent():
    def __init__(self, name, obs_dim=16) -> None:
        self.obs_dim = obs_dim
        self.actions = ["IDLE", "L1", "L2", "L3"]
        self.action_dim = len(self.actions)
        self.save_dir = f"./models/cache_agent/{name}"
        self.agent = D3QN(alpha=1e-4,
                          state_dim=self.obs_dim,
                          action_dim=self.action_dim,
                          fc1_dim=64,
                          fc2_dim=32,
                          ckpt_dir=self.save_dir,
                          gamma=0.99,
                          tau=0.005,
                          epsilon=1.0,
                          eps_end=0.05,
                          eps_dec=1e-3,
                          max_size=1000000,
                          batch_size=256)
        self.count = 0
        self.reward_history = []
        self.action_history = []
        self.load()

    def choose_action(self, observation):
        # return 3
        return self.agent.choose_action(observation)

    def remember(self, state, action, reward, state_):
        done = self.count % 100 == 0
        self.agent.remember(state, action, reward, state_, done)
        self.count += 1
        if done:
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

    def generate_observation(self, env, conn, with_feature_name=False):
        nearby_servers = conn.source.find_nearby_servers(env, 40)
        data = {
            # "is_faulty": conn.source.faulty,  # ES服务器是否故障
            # "server_stablity": conn.source.stablity,  # ES服务器运行稳定性
            # "cached": conn.cached,  # 是否已被缓存
            # 是否正在被缓存
            # "is_being_cached": conn.source.is_caching_service(conn.service),
            "cached_in_L1": conn.cache_level == "L1",  # 是否已被缓存在L1
            "cached_in_L2": conn.cache_level == "L2",  # 是否已被缓存在L2
            "cached_in_L3": conn.cache_level == "L3",  # 是否已被缓存在L3
            "current_load": conn.source.load,  # 当前ES的负载（按连接数计算）
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
            # "service_size": conn.service.size,
            # "estimated_speed": conn.source.estimated_network_speed,  # 当前从ES下载的估计速度
            # 预估回源用时
            # "estimated_fetch_time": conn.source.estimated_network_speed/conn.service.size,
            # 是否流行
            "is_popular": env.trend.is_popular(conn.service),
            # 魅力值
            "charm": conn.service.charm,
            # 服务的短期被请求频率
            "service_request_frequency": conn.service.request_frequency,
            # 短距离（N km）内的ES个数
            "nearby_servers_count": len(nearby_servers),
            # 短距离（N km）内是否已有其它ES缓存
            "nearby_servers_cached": any([s.has_cache(conn.service) for s in nearby_servers]),
            # 该ES服务器被请求的频率
            "ES_request_frequency": conn.source.request_frequency,
        }
        print("Cache agent observation:", data)
        assert len(data) == self.obs_dim
        if with_feature_name:
            return data
        else:
            result = list(data.values())
            # cast to float
            result = [float(x) for x in result]
            return result

    def execute_action(self, env, conn, action_index):
        action = self.actions[action_index]
        self.action_history.append(action)
        success = True
        if action == "IDLE":
            pass
        else:
            success = conn.source.add_to_cache(env, conn.service, action)
        return action, success

    def calc_reward(self, env, conn, action, success):
        es = conn.source
        cache_hit_status = cache_hit_status_to_percentage(es.cache_hit_status)
        score = cache_hit_status["L1"]*1 + \
            cache_hit_status["L2"]*0.5 + cache_hit_status["L3"]*0.25
        cache_hit_rate = (1 - es.cache_miss_rate) * 100
        storage_utilization = es.storage_utilization * 100
        if not success:
            return -100
        print(
            f"【奖励函数】缓存命中率：{cache_hit_rate}，存储利用率：{storage_utilization}")
        reward = cache_hit_rate * storage_utilization * score
        self.reward_history.append(reward)
        return reward


class MaintainanceAgent():
    def __init__(self, name, obs_dim=11) -> None:
        self.obs_dim = obs_dim
        self.actions = ["PRESERVE", "DELETE"]
        self.action_dim = len(self.actions)
        self.save_dir = f"./models/maintainance_agent/{name}"
        self.agent = D3QN(alpha=1e-4,
                          state_dim=self.obs_dim,
                          action_dim=self.action_dim,
                          fc1_dim=32,
                          fc2_dim=16,
                          ckpt_dir=self.save_dir,
                          gamma=0.99,
                          tau=0.005,
                          epsilon=1.0,
                          eps_end=0.05,
                          eps_dec=1e-3,
                          max_size=1000000,
                          batch_size=128)
        self.count = 0
        self.reward_history = []
        self.action_history = []
        self.load()

    def choose_action(self, observation):
        # return 0
        return self.agent.choose_action(observation)

    def remember(self, state, action, reward, state_):
        done = self.count % 100 == 0
        self.agent.remember(state, action, reward, state_, done)
        self.count += 1
        if done:
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
        print("Maintainance agent observation:", result)
        assert len(result) == self.obs_dim
        result = list(result.values())
        # cast to float
        result = [float(x) for x in result]
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
        cost = 0.8 if action == "DELETE" else 0
        cache_hit_rate = (1-es.cache_miss_rate)*100
        # 利用率
        storage_utilization = es.storage_utilization * 100
        reward = cache_hit_rate * storage_utilization
        self.reward_history.append(reward)
        return reward  # TODO: CACHE_FULL_PENALTY
