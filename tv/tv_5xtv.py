
import threading,json,time,os
import requests,oss2
import tools
import gconfig as gc 

class tv_5xtv(threading.Thread):

    show_console = False

    def __init__(self, config,cache,thread_id)-> None:
        super().__init__()
        self.config = config 
        self.cache = cache
        self.thread_id = thread_id
        self.show_console = config["app"]["thread_log"]

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
    

    
    def request_cvmart_auth(self):
        if self.cache._has(gc.CACHE_CVMART_AUTHORIZATION):
            return self.cache._get_value(gc.CACHE_CVMART_AUTHORIZATION)
        else:
            payload = {"username":self.config["cvmart"]["username"],"password":self.config["cvmart"]["password"]}
            resp = requests.post(gc.REQUEST_CVMART_LOGIN,data=json.dumps(payload),headers={"content-type":"application/json","user_agent":gc.REQUEST_USER_AGENT})
            auth = json.loads(resp.text)["data"]
            self.cache._set_value(gc.CACHE_CVMART_AUTHORIZATION,auth,auth["expires_in"] - int(time.time()))
            return auth
    
    def upload_oss_file(self,local_path,local_name):
        if self.cache._has(gc.CACHE_CVMART_OSS_STS):
            sts = self.cache._get_value(gc.CACHE_CVMART_OSS_STS)
        else:
            self.console_log("[LOG]请求OSS 文件上传授权")
            auth = self.request_cvmart_auth()
            resp = requests.get(gc.REQUEST_CVMART_STS,headers={"content-type":"application/json","user_agent":gc.REQUEST_USER_AGENT,"authorization":"Bearer " + auth["access_token"]})
            sts = json.loads(resp.text)["data"]
            expire_time = tools.format_date(times=int(time.time()) + 3540)
            self.console_log("[INFO]获取OSS 文件上传授权成功,AccessId:%s,过期时间:%s" % (sts["accessKeyId"],expire_time))
            self.cache._set_value(gc.CACHE_CVMART_OSS_STS,sts,3540)
        oss_auth = oss2.StsAuth(sts["accessKeyId"],sts["accessKeySecret"],sts["securityToken"])
        oss_bucket = oss2.Bucket(oss_auth,gc.CVMART_OSS_ENDPOINT,gc.CVMART_OSS_BUCKET)
        object_key =  sts["uploadPath"]  + "/" + self.config["cvmart"]["upload_uuid"] + "/" + local_name
        with open(local_path,"rb") as fileobj:
            oss_bucket.put_object(object_key,fileobj)
        self.console_log("[INFO]上传本地文件[%s]到OSS[%s]成功" % (local_path,object_key))
        return object_key

    def run(self):
        self.config["cvmart"]["upload_uuid"] = tools.get_uuid()
        if self.config["upload_cvmart_oss"]:
            file_save_type = "oss"
        else:
            file_save_type = "local"

        if not self.cache._has(gc.CACHE_5XTV_LIVE_URL):
            self.console_log("[INFO]请求直播间播放地址")
            live_info = self.request_live_address()
            live_address = tools.crypto_decrypt(gc.APP_5XTV_DES_KEY[0:8].encode(),live_info["live_address"])
            self.cache._set_value(gc.CACHE_5XTV_LIVE_URL, live_address, 3600 )

        else:
            live_address = self.cache._get_value(gc.CACHE_5XTV_LIVE_URL)
        self.console_log("[INFO]直播流播放地址:" + live_address)

        if os.path.exists(gc.APP_5XTV_M3U8_FILE):
            os.remove(gc.APP_5XTV_M3U8_FILE)
        if not os.path.exists("./static/data"):
            os.mkdir("./static/data")
        while True:
            self.console_log("[LOG]请求刷新M3U8分片信息")
            resp = requests.get(live_address,headers={"user-agent": gc.REQUEST_USER_AGENT, "referer": gc.REQUEST_5XTV_SRC_REFERER})
            m3u8_content = resp.text
            download_heart = {"cache_keys":[],"download_time":"","cache_length":""}
            for content in m3u8_content.split("\n"):
                if not content.startswith("#") and content:
                    url = {"filename": content.split("?")[0],"filesrc": gc.REQUEST_5XTV_SRC + content}
                    url["time"] = url["filename"].split("-")[-1].split(".")[0]
                    file_cache_key = gc.CACHE_5XTV_FILE + ":" + file_save_type +":" + url["time"]
                    if not self.cache._has(file_cache_key):
                        local_name = tools.get_uuid() + ".ts"
                        download_header = {
                            "user-agent":  gc.REQUEST_USER_AGENT ,
                            "origin":gc.REQUEST_5XTV_SRC_REFERER,
                             "referer": gc.REQUEST_5XTV_SRC_REFERER
                        }
                        if self.show_console:
                            thread_id = self.thread_id
                        else:
                            thread_id = -1
                        if tools.download_file(url["filesrc"], "./static/data/" + local_name, download_header, "视频切片[%s]" % (url["time"]),thread_id):
                            # 上传到 oss ,可以外网播放
                            if self.config["upload_cvmart_oss"]:
                                url["oss_object"] =  self.upload_oss_file("./static/data/" + local_name,local_name)
                                url["oss_url"] = gc.CVMART_OSS_DOMAIN   +  url["oss_object"] 
                            url["local_file"] = "data/" + local_name
                            self.cache._set_value(file_cache_key, url, 3600)
                    else:
                        url = self.cache._get_value(file_cache_key)
                    download_heart["cache_keys"].append(file_cache_key)
                    if not self.config["upload_cvmart_oss"]: 
                        m3u8_content = m3u8_content.replace(content, url["local_file"] )
                    else:
                        m3u8_content = m3u8_content.replace(content, url["oss_url"] )
            self.console_log("[INFO]更新5xtv.m3u8")
            tools.write_file(gc.APP_5XTV_M3U8_FILE,m3u8_content)
            download_heart["download_time"] = int(time.time())
            self.cache._set_value(gc.CACHE_5XTV_LIVE_HEART,download_heart,60)
            files = os.listdir("./static/data")
            cache_files_keys = self.cache.client.keys(gc.CACHE_5XTV_FILE + ":*")
            cache_files = []
            for key in cache_files_keys:
                cache_file = self.cache._get_value(key)
                if cache_file:
                    cache_files.append(cache_file["local_file"])
            for file in files:
                if "data/" + file not in cache_files:
                    os.remove("./static/data/" + file)
                    self.console_log("[WARNING]删除文件[%s]" %( "./static/data/" + file))
            time.sleep(1)


            
