from pprint import pprint
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
                                     "can_L1_fit", "can_L2_fit",
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
    obs = cache_agent.generate_observation(env, conn, with_feature_name=True)
    pprint(obs)
    actions = cache_agent.actions
    print(f"【cache agent动作】：{actions}")
    action_index = input("请输入动作序号：")
    if action_index not in ["0", "1", "2"]:
        print("输入错误")
        action_index = "2"
    action_index = int(action_index)
    action, success = cache_agent.execute_action(env, conn, action_index)
    print(f"执行动作：{action}，是否成功：{success}")
    reward = cache_agent.calc_reward(env, conn, action, success)
    print("【reward】: ", reward)

    global cache_df
    obs["action"] = action
    cache_df = cache_df.append(obs, ignore_index=True)
    cache_df.to_csv("cache_df.csv", index=False)


def service_maintainance_callback(es, service, ugent):
    print("service_maintainance_callback called", es, service)
    maintainance_agent = es.maintainance_agent
    obs = maintainance_agent.generate_observation(
        es, service, ugent, with_feature_name=True)
    pprint(obs)
    actions = maintainance_agent.actions
    print(f"【maintainance agent动作】：{actions}")
    action_index = input("请输入动作序号：")
    if action_index not in ["0", "1"]:
        print("输入错误")
        action_index = "0"
    action_index = int(action_index)
    cache_level = es.get_cache_level(service)
    action = maintainance_agent.execute_action(es, service, action_index)
    reward = maintainance_agent.calc_reward(
        env, es, service, action, cache_level)
    print("【reward】: ", reward)

    global maintainance_df
    obs["action"] = action
    maintainance_df = maintainance_df.append(obs, ignore_index=True)
    maintainance_df.to_csv("maintainance_df.csv", index=False)


def cache_event(type):
    print(f"【cache event】:{type}")
    env.statistics.add_cache_event(type)


if __name__ == "__main__":
    if ENABLE_VISUALIZATION:
        apis.start_server()
    env.request_callback = request_callback
    env.cache_miss_callback = cache_miss_callback
    env.cache_hit_callback = cache_hit_callback
    env.cache_event = cache_event
    env.service_maintainance_callback = service_maintainance_callback
    while True:
        if env.pause_flag:
            time.sleep(0.5)
            continue
        env.tick()
        # time.sleep(0.001)  # not full speed
