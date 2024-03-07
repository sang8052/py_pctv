'''
Author: SudemQaQ
Date: 2024-01-10 21:57:15
email: mail@szhcloud.cn
Blog: https://blog.szhcloud.cn
github: https://github.com/sang8052
LastEditors: SudemQaQ
LastEditTime: 2024-01-15 14:47:31
Description: 对 REDIS 二次封装
'''
import json, sys, os, time
import redis
import tools


class xcache:
    client = None
    config = {}
    app_cache_key = "py_ai_video"
    app_token = ""

    def __init__(self, config) -> None:
        self.config = config
        self.__connect_server()
        self.pid = os.getpid()

    def __connect_server(self):
        try:
            self.client = redis.Redis(host=self.config["host"], port=self.config["port"],
                                      password=self.config["password"], db=self.config["index"], decode_responses=True)
            self.client.ping()
            tools.console_log("[INFO]连接REDIS[" + self.config["host"] + ":" + str(self.config["port"]) + "-" + str(
                self.config["index"]) + "]成功")
        except Exception as err:
            tools.console_log("[ERROR]连接REDIS[" + self.config["host"] + ":" + str(self.config["port"]) + "-" + str(
                self.config["index"]) + "]失败!")
            tools.console_log("[ERROR]" + str(err))
            sys.exit()

    def _get_value(self, key):
        value = self.client.get(key)
        if tools.is_json(value):
            return json.loads(value)
        return value

    def _set_value(self, key, value, ttl=-1):
        if tools.is_object(value):
            value = json.dumps(value, ensure_ascii=True)
        if ttl != -1:
            self.client.set(key, value, ttl)
        else:
            # print(key,value)
            self.client.set(key, value)

    def _delete(self, key):
        self.client.delete(key)

    def _has(self, key):
        if self.client.exists(key):
            return True
        else:
            return False

    def _ttl(self, key, ttl):
        self.client.expire(key, ttl)





