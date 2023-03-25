from D3QN import D3QN
import os


class CacheAgent():
    def __init__(self, obs_dim) -> None:
        self.obs_dim = obs_dim
        self.actions = ["IDLE", "L1", "L2", "L3"]
        self.action_dim = len(self.actions)
        self.save_dir = "./models/cache_agent"
        self.agent = D3QN(alpha=0.0003,
                          state_dim=self.obs_dim,
                          action_dim=self.action_dim,
                          fc1_dim=256,
                          fc2_dim=256,
                          ckpt_dir=self.save_dir,
                          gamma=0.99,
                          tau=0.005,
                          epsilon=1.0,
                          eps_end=0.05,
                          eps_dec=5e-4,
                          max_size=1000000,
                          batch_size=128)
        self.count = 0

    def choose_action(self, observation):
        return self.agent.choose_action(observation)

    def remember(self, state, action, reward, state_):
        done = self.count % 100 == 0
        self.agent.remember(state, action, reward, state_, done)
        self.count += 1

    def learn(self):
        self.agent.learn()

    def save(self):
        # create dir if path not exists
        if os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)
        self.agent.save_models()

    def load(self):
        self.agent.load_models()

    def generate_observation(self, env, conn):
        nearby_servers = conn.source.find_nearby_servers(env, 40)
        data = {
            "is_faulty": conn.source.faulty,  # ES服务器是否故障
            "server_stablity": conn.source.stablity,  # ES服务器运行稳定性
            # "cached": conn.cached,  # 是否已被缓存
            # 是否正在被缓存
            "is_being_cached": conn.source.is_caching_service(conn.service),
            "cached_in_L1": conn.cache_level == "L1",  # 是否已被缓存在L1
            "cached_in_L2": conn.cache_level == "L2",  # 是否已被缓存在L2
            "cached_in_L3": conn.cache_level == "L3",  # 是否已被缓存在L3
            "current_load": conn.source.load,  # 当前ES的负载（按连接数计算）
            "estimated_speed": conn.source.estimated_network_speed,  # 当前从ES下载的估计速度
            # 当前ES的L1剩余空间
            "free_storage_size_L1": conn.source.free_storage_size("L1"),
            # 当前ES的L2剩余空间
            "free_storage_size_L2": conn.source.free_storage_size("L2"),
            # 当前ES的L3剩余空间
            "free_storage_size_L3": conn.source.free_storage_size("L3"),
            # L1能放得下
            "can_L1_fit": conn.source.free_storage_size("L1") > conn.service.size,
            # L2能放得下
            "can_L2_fit": conn.source.free_storage_size("L2") > conn.service.size,
            # L3能放得下
            "can_L3_fit": conn.source.free_storage_size("L3") > conn.service.size,
            # 服务大小
            "service_size": conn.service.size,
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
            "nearby_servers_cached": any([s.has_cache(conn.service) for s in nearby_servers]),
            # 该ES服务器被请求的频率
            "ES_request_frequency": conn.source.request_frequency,
        }
        result = list(data.values())
        assert len(result) == self.obs_dim
        return result

    def execute_action(self, env, conn, action_index):
        action = self.actions[action_index]
        if action == "IDLE":
            pass
        else:
            conn.source.add_to_cache(env, conn.service, action)

    def calc_reward(self, env, conn):
        # TODO:设计奖励函数
        if conn.source.faulty:
            return -1000
        if conn.source.is_caching_service(conn.service):
            return 1
        else:
            return -1


class MaintainanceAgent():
    def __init__(self, obs_dim) -> None:
        self.obs_dim = obs_dim
        self.actions = ["PRESERVE", "DELETE"]
        self.action_dim = len(self.actions)
        self.save_dir = "./models/maintainance_agent"
        self.agent = D3QN(alpha=0.0003,
                          state_dim=self.obs_dim,
                          action_dim=self.action_dim,
                          fc1_dim=256,
                          fc2_dim=256,
                          ckpt_dir=self.save_dir,
                          gamma=0.99,
                          tau=0.005,
                          epsilon=1.0,
                          eps_end=0.05,
                          eps_dec=5e-4,
                          max_size=1000000,
                          batch_size=128)
        self.count = 0

    def choose_action(self, observation):
        return self.agent.choose_action(observation)

    def remember(self, state, action, reward, state_):
        done = self.count % 100 == 0
        self.agent.remember(state, action, reward, state_, done)
        self.count += 1

    def learn(self):
        self.agent.learn()

    def save(self):
        # create dir if path not exists
        if os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)
        self.agent.save_models()

    def load(self):
        self.agent.load_models()

    def generate_observation(self, es, service):
        result = {
            # "is_faulty": es.faulty,  # ES服务器是否故障
            # L1剩余空间百分比
            "L1_free_space_ratio": es.free_storage_size("L1")/es.get_storage_size("L1"),
            # L2剩余空间百分比
            "L2_free_space_ratio": es.free_storage_size("L2")/es.get_storage_size("L2"),
            # L3剩余空间百分比
            "L3_free_space_ratio": es.free_storage_size("L3")/es.get_storage_size("L3"),
            # 服务大小与L1总空间的比例
            "service_size_ratio_L1": service.size/es.get_storage_size("L1"),
            # 服务大小与L2总空间的比例
            "service_size_ratio_L2": service.size/es.get_storage_size("L2"),
            # 服务大小与L3总空间的比例
            "service_size_ratio_L3": service.size/es.get_storage_size("L3"),
            "service_charm": service.charm,  # 服务的魅力值
            "service_request_frequency": service.request_frequency,  # 服务的短期被请求频率
        }
        print(result)
        assert len(result) == self.obs_dim
        return list(result.values())

    def execute_action(self, es, service, action_index):
        action = self.actions[action_index]
        if action == "PRESERVE":
            pass
        elif action == "DELETE":
            es.delete_from_cache(service)
            print(f"【淘汰缓存】{service} 从 {es} 被淘汰")

    def calc_reward(self):
        # 奖励函数，考虑 缓存命中率、动作的累计成本代价、存储空间利用率、QOS(下载速度、响应时间、剩余连接数)、负载均衡性、缓存级别
        pass
