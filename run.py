import random
import time
import apis
from environment import env

if __name__ == "__main__":
    apis.start_server()

    while True:
        if env.pause_flag:
            time.sleep(0.1)
            continue
        env.tick()
        # time.sleep(0.01)  # not full speed
