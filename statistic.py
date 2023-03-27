class Statistics():
    def __init__(self) -> None:
        self.cache_event_history = []

    def add_cache_event(self, event, num=100):
        if len(self.cache_event_history) > num:
            self.cache_event_history.pop(0)
        self.cache_event_history.append(event)

    def get_cache_event_history(self, num=20):
        result = {
            "CACHE_HIT": 0,
            "CACHE_MISS": 0,
            "CACHE_SWITCH": 0,
            "CACHE_FULL": 0,
            "CACHE_DUPLICATE": 0,
            "FAILED_TO_CONNECT": 0,
        }
        for event in self.cache_event_history[-num:]:
            if event in result:
                result[event] += 1
            else:
                result[event] = 1
        return result
