import time
import apis
from simulator import env
#from d3qn import Agent
from D3QN import D3QN

ACTIONS = ["IDLE", "L1", "L2", "L3"]


def generate_observation(env, conn):
    nearby_servers = conn.source.find_nearby_servers(env, 40)
    return {
        # "is_faulty": conn.source.faulty,  # ES服务器是否故障
        "server_stablity": conn.source.stablity,  # ES服务器运行稳定性
        "cached": conn.cached,  # 是否已被缓存
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


obs = None
obs_dim = 22
# agent = Agent(gamma=0.99, n_actions=len(ACTIONS), epsilon=1.0,
#              batch_size=64, input_dims=[obs_dim])
agent = D3QN(alpha=0.0003, state_dim=obs_dim, action_dim=len(ACTIONS),
             fc1_dim=256, fc2_dim=256, ckpt_dir="/models", gamma=0.99, tau=0.005, epsilon=1.0,
             eps_end=0.05, eps_dec=5e-4, max_size=1000000, batch_size=256)

count = 0
env.reward = 0


def request_callback(conn):
    global obs
    global count
    print("request_callback called")

    obs_ = generate_observation(env, conn)
    print(obs_)
    obs_ = list(obs_.values())
    done = 1
    if obs is not None:
        action_index = agent.choose_action(obs)
        action = ACTIONS[action_index]
        print("【action】: ", action)
        if action == "IDLE":
            pass
        else:
            conn.source.add_to_cache(env, conn.service, action)
        agent.remember(obs, action_index, env.reward, obs_, int(done))
        env.reward = 0  # reset reward
    obs = obs_
    agent.learn()
    count += 1
    # if count % 100 == 0:
    #    agent.save_models(count)


def reward_event(type, data=None):
    print(f"reward_event called: {type}, data:{data}")
    if type == "CACHE_HIT":
        levels = ["L1", "L2", "L3"]  # L1 is the best
        index = levels.index(data)
        t = len(levels) - index
    elif type == "CACHE_MISS":
        t = -1
    elif type == "CACHE_FULL":
        t = -1
    elif type == "CACHE_DUPLICATE":
        t = -1
    elif type == "FAILED_TO_CONNECT":
        t = -1

    env.reward += t
    #env.reward = t
    print(f"【reward】:change by {t}, total reward:{env.reward}")

# TODO: 淘汰策略 + 写入缓存需要时间


env.request_callback = request_callback
env.reward_event = reward_event

if __name__ == "__main__":
    apis.start_server()

    while True:
        if env.pause_flag:
            time.sleep(0.5)
            continue
        env.tick()
        # time.sleep(0.001)  # not full speed
