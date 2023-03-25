import time
import apis
from simulator import env
from agents import MaintainanceAgent, CacheAgent
from simulator.config import ENABLE_VISUALIZATION

cache_agent = CacheAgent(obs_dim=22)
maintainance_agent = MaintainanceAgent(obs_dim=8)


def request_callback(conn):
    print("request_callback called")


def cache_miss_callback(conn):
    obs = cache_agent.generate_observation(env, conn)
    action_index = cache_agent.choose_action(obs)
    print("【cache action】: ", cache_agent.actions[action_index])
    cache_agent.execute_action(env, conn, action_index)
    reward = cache_agent.calc_reward(env, conn)
    obs_next = cache_agent.generate_observation(env, conn)
    cache_agent.remember(obs, action_index, reward, obs_next)
    cache_agent.learn()


def service_maintainance_callback(es, service):
    #print("service_maintainance_callback called", es, service)
    obs = maintainance_agent.generate_observation(es, service)
    action_index = maintainance_agent.choose_action(obs)
    print("【maintainance action】: ", maintainance_agent.actions[action_index])
    maintainance_agent.execute_action(es, service, action_index)
    reward = maintainance_agent.calc_reward()
    obs_next = maintainance_agent.generate_observation(es, service)
    maintainance_agent.remember(obs, action_index, reward, obs_next)
    maintainance_agent.learn()


def cache_event(type, data=None):
    print(f"【cache event】 : {type}, data:{data}")


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
