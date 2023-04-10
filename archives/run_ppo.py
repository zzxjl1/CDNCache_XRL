import time
import apis
from simulator import env
from simulator.config import ENABLE_VISUALIZATION


def request_callback(conn):
    #print("request_callback called")
    pass


def cache_hit_callback(conn):
    #print("cache_hit_callback called")
    pass


def cache_miss_callback(conn):
    cache_agent = conn.source.cache_agent
    obs = cache_agent.generate_observation(env, conn)
    action_index, prob, val = cache_agent.choose_action(obs)
    print("【cache action】: ", cache_agent.actions[action_index])
    action, success = cache_agent.execute_action(env, conn, action_index)
    reward = cache_agent.calc_reward(env, conn, action, success)
    print("【reward】: ", reward)
    cache_agent.remember(obs, action_index, prob, val, reward)
    cache_agent.learn()


def service_maintainance_callback(es, service, ugent):
    maintainance_agent = es.maintainance_agent
    obs = maintainance_agent.generate_observation(es, service, ugent)
    action_index, prob, val = maintainance_agent.choose_action(obs)
    print("【maintainance action】: ",
          maintainance_agent.actions[action_index])
    cache_level = es.get_cache_level(service)
    action = maintainance_agent.execute_action(es, service, action_index)
    reward = maintainance_agent.calc_reward(
        env, es, service, action, cache_level)
    print("【reward】: ", reward)
    maintainance_agent.remember(obs, action_index, prob, val, reward)
    maintainance_agent.learn()


if __name__ == "__main__":
    if ENABLE_VISUALIZATION:
        apis.start_server()
    env.request_callback = request_callback
    env.cache_miss_callback = cache_miss_callback
    env.cache_hit_callback = cache_hit_callback
    env.service_maintainance_callback = service_maintainance_callback
    while True:
        if env.pause_flag:
            time.sleep(0.5)
            continue
        env.tick()
        # time.sleep(0.001)  # not full speed
