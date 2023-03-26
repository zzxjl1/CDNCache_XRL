import time
import apis
from simulator import env
from agents import MaintainanceAgent, CacheAgent
from simulator.config import ENABLE_VISUALIZATION


def request_callback(conn):
    #print("request_callback called")
    pass


def cache_miss_callback(conn):
    obs = env.cache_agent.generate_observation(env, conn)
    action_index = env.cache_agent.choose_action(obs)
    print("【cache action】: ", env.cache_agent.actions[action_index])
    action, success = env.cache_agent.execute_action(env, conn, action_index)
    reward = env.cache_agent.calc_reward(env, conn, action, success)
    print("【reward】: ", reward)
    obs_next = env.cache_agent.generate_observation(env, conn)
    env.cache_agent.remember(obs, action_index, reward, obs_next)
    env.cache_agent.learn()


def service_maintainance_callback(es, service):
    print("service_maintainance_callback called", es, service)
    obs = env.maintainance_agent.generate_observation(es, service)
    action_index = env.maintainance_agent.choose_action(obs)
    print("【maintainance action】: ",
          env.maintainance_agent.actions[action_index])
    cache_level = es.get_cache_level(service)
    action = env.maintainance_agent.execute_action(es, service, action_index)
    reward = env.maintainance_agent.calc_reward(
        env, es, service, action, cache_level)
    print("【reward】: ", reward)
    if action == "PRESERVE":
        obs_next = obs
    elif action == "DELETE":
        obs_next = env.maintainance_agent.generate_observation_next(
            cache_level, es)
    env.maintainance_agent.remember(obs, action_index, reward, obs_next)
    env.maintainance_agent.learn()


def cache_event(type):
    print(f"【cache event】 : {type}")


if __name__ == "__main__":
    if ENABLE_VISUALIZATION:
        apis.start_server()
    env.request_callback = request_callback
    env.cache_miss_callback = cache_miss_callback
    env.cache_event = cache_event
    env.service_maintainance_callback = service_maintainance_callback
    while True:
        if env.pause_flag:
            time.sleep(0.5)
            continue
        env.tick()
        # time.sleep(0.001)  # not full speed
