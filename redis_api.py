import json
import datetime

import redis


class RedisApi:
    def __init__(self):
        self.redis_session = redis.StrictRedis(host='localhost', port=6379, db=0)

    def clear_db(self):
        self.redis_session.flushdb()
        return True

    def add_time_parsing(self, date_time: str):
        return self.redis_session.set(date_time, "1")

    def check_time_parsing(self):
        date_time = datetime.datetime.now().strftime("%H:%M")
        check_time = self.redis_session.get(date_time)
        if check_time and check_time.decode() == "1":
            self.redis_session.set(date_time, 0)
            return True
        return False

    def refresh_status_time_keys_parsing(self):
        all_keys = self.redis_session.keys()
        for key in all_keys:
            if len(key.decode()) == 5:
                self.redis_session.set(key.decode(), "1")
        return True

    def delete_time_keys_parsing(self):
        all_keys = self.redis_session.keys()
        for key in all_keys:
            if len(key.decode()) == 5:
                self.redis_session.delete(key.decode())
        return True





now = datetime.datetime.now().strftime("%H:%M")
print(now)

redis_api = RedisApi()
# print(redis_api.add_time_parsing(datetime.datetime.now()))

# redis_api.delete_time_keys_parsing()
# print(redis_api.check_time_parsing("12:04"))





