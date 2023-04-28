from pprint import pprint
import random
import time
import apis
from simulator import env
from simulator.config import ENABLE_VISUALIZATION
import pandas as pd
import os

if not os.path.exists("cache_df.csv"):
    cache_df = pd.DataFrame(columns=["es_load",
                                     "free_storage_size_ratio_L1",
                                     "free_storage_size_ratio_L2",
                                     "free_storage_size_ratio_L3",
                                     "can_L1_fit", "can_L2_fit", "can_L3_fit",
                                     "service_size",
                                     "estimated_fetch_time",
                                     "is_popular", "charm",
                                     "service_request_frequency",
                                     "nearby_servers_count",
                                     "cached_in_nearby_servers",
                                     "es_request_frequency",
                                     "action"])
else:
    cache_df = pd.read_csv("cache_df.csv")

if not os.path.exists("maintainance_df.csv"):
    maintainance_df = pd.DataFrame(columns=["free_space_ratio",
                                            "service_size_ratio",
                                            "cached_in_L1",
                                            "cached_in_L2",
                                            "cached_in_L3",
                                            "service_charm",
                                            "service_request_frequency",
                                            "es_request_frequency",
                                            "es_cache_miss_rate",
                                            "least_freq_index",
                                            "is_ugent",
                                            "action"])
else:
    maintainance_df = pd.read_csv("maintainance_df.csv")


def request_callback(conn):
    #print("request_callback called")
    pass


def cache_hit_callback(conn):
    #print("cache_hit_callback called")
    pass


def cache_miss_callback(conn):
    cache_agent = conn.source.cache_agent
    obs = cache_agent.generate_observation(env, conn)
    pprint(obs)

    action = None
    if obs["es_load"] > 0.9:  # ES_load过高，不缓存
        action = "IDLE"

    if obs["can_L1_fit"]:
        action = "L1"
    elif obs["can_L2_fit"]:
        action = "L2"
    elif obs["can_L3_fit"]:
        action = "L3"
    else:  # 置换
        action = random.choice(["L1", "L2", "L3"])

    actions = cache_agent.actions
    action_index = actions.index(action)
    action, success = cache_agent.execute_action(env, conn, action_index)
    print(f"执行动作：{action}，是否成功：{success}")

    global cache_df
    obs["action"] = action
    cache_df = cache_df.append(obs, ignore_index=True)
    #cache_df.to_csv("cache_df.csv", index=False)


def service_maintainance_callback(es, service, ugent):
    print("service_maintainance_callback called", es, service)
    maintainance_agent = es.maintainance_agent
    obs = maintainance_agent.generate_observation(es, service, ugent)
    pprint(obs)

    """
    打分机制：
    cached_in_L1最容易淘汰，cached_in_L2其次,cached_in_L3最不容易淘汰
    service_charm和service_request_frequency越大越不容易淘汰
    service_size_ratio 越大越容易淘汰
    es_request_frequency和es_cache_miss_rate越大越容易淘汰
    """
    score = 0
    score += obs["cached_in_L1"] * 0.5
    score += obs["cached_in_L2"] * 0.3
    score += obs["cached_in_L3"] * 0.2
    score *= obs["es_cache_miss_rate"]
    score *= 1 - obs["free_space_ratio"]

    def sigmoid(x): return 1 / (1 + 2.71828 ** (-x))
    score *= sigmoid(obs["least_freq_index"])
    print("score:", score)

    # 按概率选动作
    if random.random() < score/2:
        action = "DELETE"
    else:
        action = "PRESERVE"

    print("action:", action)

    # overwrite
    if obs["is_ugent"] and obs["least_freq_index"] <= 1:
        action = "DELETE"
    elif obs["free_space_ratio"] >= 0.2:
        action = "PRESERVE"

    actions = maintainance_agent.actions
    action_index = actions.index(action)
    print(f"执行动作：{action}")
    action = maintainance_agent.execute_action(es, service, action_index)

    global maintainance_df
    obs["action"] = action
    maintainance_df = maintainance_df.append(obs, ignore_index=True)
    #maintainance_df.to_csv("maintainance_df.csv", index=False)


if __name__ == "__main__":
    if ENABLE_VISUALIZATION:
        apis.start_server()
    env.request_callback = request_callback
    env.cache_miss_callback = cache_miss_callback
    env.cache_hit_callback = cache_hit_callback
    env.service_maintainance_callback = service_maintainance_callback
    try:
        while True:
            if env.pause_flag:
                time.sleep(0.5)
                continue
            env.tick()
            # time.sleep(0.001)  # not full speed
    except KeyboardInterrupt:
        cache_df.to_csv("cache_df.csv", index=False)
        maintainance_df.to_csv("maintainance_df.csv", index=False)
