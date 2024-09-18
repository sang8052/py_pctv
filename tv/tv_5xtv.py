'''
Author: SudemQaQ
Date: 2024-09-09 10:03:55
email: mail@szhcloud.cn
Blog: https://blog.szhcloud.cn
github: https://github.com/sang8052
LastEditors: SudemQaQ
LastEditTime: 2024-09-18 12:13:47
Description: 
'''

import threading,json,time,os
import requests
import tools
import gconfig as gc 

class tv_5xtv(threading.Thread):

    show_console = False
    oss = False

    def __init__(self, config,thread_id,oss)-> None:
        super().__init__()
        self.config = config 
        self.thread_id = thread_id
        self.show_console = config["app"]["thread_log"]
        self.oss = oss 

    def console_log(self,content):
        if self.show_console:
            tools.console_log(content,self.thread_id)

    # 请求视频流播放地址
    def request_live_address(self):
        sign_content = "appId=%s&nonceStr=%s&time=%d" % (gc.APP_5XTV_APPID, gc.APP_5XTV_NONCESTR, int(time.time()))
        sign = tools.text_md5(sign_content + gc.APP_5XTV_MD5_KEY)
        query = sign_content + "&sign=" + sign
        resp = requests.get(gc.REQUEST_5XTV_CHANNEL_LIST + "?" + query,headers={"user-agent": gc.REQUEST_USER_AGENT})
        response = json.loads(resp.text)
        return response["data"][0]
    



    def run(self):
        self.console_log("[INFO]请求直播间播放地址")
        live_info = self.request_live_address()
        live_address = tools.crypto_decrypt(gc.APP_5XTV_DES_KEY[0:8].encode(),live_info["live_address"])
        self.console_log("[INFO]直播流播放地址:" + live_address)
        if os.path.exists(gc.APP_5XTV_M3U8_FILE):
            os.remove(gc.APP_5XTV_M3U8_FILE)
        if not os.path.exists("./static/data"):
            os.mkdir("./static/data")

        while True:
            self.console_log("[LOG]请求刷新M3U8分片信息")
            m3u8_content = ""
            while m3u8_content == "":
                try:
                    resp = requests.get(live_address,headers={"user-agent": gc.REQUEST_USER_AGENT, "referer": gc.REQUEST_5XTV_SRC_REFERER},timeout=3)
                    if resp.status_code == 200:
                        m3u8_content = resp.text
                        m3u8_vip_content = resp.text
                    else:
                        tools.console_log("[WARNING]直播流会话过期,重新刷新直播流地址!")
                        live_info = self.request_live_address()
                        live_address = tools.crypto_decrypt(gc.APP_5XTV_DES_KEY[0:8].encode(),live_info["live_address"])
                        self.console_log("[INFO]直播流播放地址:" + live_address)
                except:
                    tools.console_log("[WARNING]尝试拉取直播流地址失败,网络异常,1秒后重试...")
                    time.sleep(1)
            # 下载切片的文件 
            for content in m3u8_content.split("\n"):
                if not content.startswith("#") and content:
                    url = {"filename": content.split("?")[0],"filesrc": gc.REQUEST_5XTV_SRC + content}
                    url["time"] = url["filename"].split("-")[-1].split(".")[0]
                    file_cache_path = "./static/data/5xtv_" + url["time"] + ".ts"
                    if not os.path.exists(file_cache_path):
                        download_header = {
                            "user-agent":  gc.REQUEST_USER_AGENT ,
                            "origin":gc.REQUEST_5XTV_SRC_REFERER,
                             "referer": gc.REQUEST_5XTV_SRC_REFERER
                        }
                        if self.show_console:
                            thread_id = self.thread_id
                        else:
                            thread_id = -1
                        tools.download_file(url["filesrc"], file_cache_path, download_header, "视频切片[%s]" % (url["time"]),thread_id)
                
                    url["local_file"] = "data/5xtv_" + url["time"] + ".ts"
                    m3u8_content = m3u8_content.replace(content, url["local_file"])
                    if self.oss:
                        oss_url = self.oss.upload_file("./static/" +   url["local_file"])
                        m3u8_vip_content = m3u8_vip_content.replace(content,oss_url)
            self.console_log("[INFO]更新5xtv.m3u8")
            tools.write_file(gc.APP_5XTV_M3U8_FILE,m3u8_content)
            if self.oss:
                tools.write_file(gc.APP_5XTV_M3U8_VIP_FILE,m3u8_vip_content)
            # 删除切片的文件
            files = os.listdir("./static/data")
            for file in files:
                file_timestamp = file.replace("5xtv_","").replace(".ts","")[0:10]
                # 删除和当前时间误差超过 300s 秒的文件
                if abs(int(time.time()) - int(file_timestamp,10)) > 300:
                    try:
                        os.remove("./static/data/" + file)
                        self.console_log("[WARNING]删除文件[%s]" %( "./static/data/" + file))
                    except:
                        pass 

            time.sleep(1)
