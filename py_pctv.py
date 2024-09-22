'''
Author: SudemQaQ
Date: 2024-03-07 10:48:56
email: mail@szhcloud.cn
Blog: https://blog.szhcloud.cn
github: https://github.com/sang8052
LastEditors: SudemQaQ
LastEditTime: 2024-09-22 22:38:19
Description: 
'''
from gevent import pywsgi
from gevent import monkey
monkey.patch_all()

import colorama
import signal,os
import tools,web
import gconfig as gc 
from tv import tv_5xtv
import cv_oss
import time,threading

app_version = "1.0.2.debug"

def signal_handler(signal, handle):
    if signal == 2:
        tools.console_log("[ERROR]收到程序终止信号")
        pid = os.getpid()
        tools.console_log("[WARNING]关闭进程[pid:" + str(pid) + "]")
        tools.kill_pid(pid)

if __name__ == "__main__":


    colorama.init()
    signal.signal(signal.SIGINT, signal_handler)

    print("========================================")
    print("PY_PCTV 流媒体客户端")
    print("Author:  mail@szhcloud.cn")
    print("Version: " + app_version)
    print("========================================")


    config = tools.read_json("config.json")
    tools.console_log("[INFO]运行路径:" + tools.get_local_path())

    web.app.tvs = []
    web.app._config = config 
 
    th_5xtv = tv_5xtv.tv_5xtv(config,1)
    th_5xtv.start()
    tools.console_log("[INFO]线程[五星体育直播]启动成功")
    tv_info = {"name":"五星体育","thread_id":1,"live":gc.APP_5XTV_M3U8_FILE.replace("./static/","")}
    web.app.tvs.append(tv_info)

    server = pywsgi.WSGIServer((config["app"]["address"],config["app"]["port"]),web.app)
    server.multithread = True
    tools.console_log("[INFO]WSGIServer Listen %s:%d" % (config["app"]["address"],config["app"]["port"]))
    server.serve_forever()


    