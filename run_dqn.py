import time
import apis
from simulator import env
from simulator.config import ENABLE_VISUALIZATION, PRINT_AGENT_STATUS
from utils import overall_cache_miss_rate, obs2vector


def request_callback(conn):
    #print("request_callback called")
    pass


def cache_hit_callback(conn):
    #print("cache_hit_callback called")
    pass


def cache_miss_callback(conn):
    cache_agent = conn.source.cache_agent
    obs = cache_agent.generate_observation(env, conn)
    action_index = cache_agent.choose_action(obs2vector(obs))
    action, success = cache_agent.execute_action(env, conn, action_index)
    reward = cache_agent.calc_reward(env, conn, action, success)
    obs_next = cache_agent.generate_observation(env, conn)
    cache_agent.remember(obs2vector(obs), action_index, reward,
                         obs2vector(obs_next), env.now())
    cache_agent.learn()

    if PRINT_AGENT_STATUS:
        print("【Cache agent observation】", obs)
        print("【cache action】: ", cache_agent.actions[action_index])
        print("【reward】: ", reward)


def service_maintainance_callback(es, service, ugent):
    maintainance_agent = es.maintainance_agent
    obs = maintainance_agent.generate_observation(es, service, ugent)
    action_index = maintainance_agent.choose_action(obs2vector(obs))
    cache_level = es.get_cache_level(service)
    action = maintainance_agent.execute_action(es, service, action_index)
    reward = maintainance_agent.calc_reward(
        env, es, service, action, cache_level)
    if action == "PRESERVE":
        obs_next = obs
    elif action == "DELETE":
        obs_next = maintainance_agent.generate_observation_next(
            cache_level, es)
    maintainance_agent.remember(
        obs2vector(obs), action_index, reward, obs2vector(obs_next), env.now())
    maintainance_agent.learn()

    if PRINT_AGENT_STATUS:
        print("【Maintainance agent observation】", obs)
        print("【maintainance action】: ",
              maintainance_agent.actions[action_index])
        print("【reward】: ", reward)


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
        if env.now() > 2000 and overall_cache_miss_rate(env) > 0.8:
            print(f"【环境失去作用了，正在重启！】")
            env.reset()

        try:
            env.tick()
        except Exception as e:
            print("failed to tick env：")
            import traceback
            traceback.print_exc()

        # time.sleep(0.001)  # not full speed
