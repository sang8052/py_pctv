import requests,oss2
import tools,uuid,json 
import time,os 
import gconfig as gc 

class cv_oss():

    def __init__(self,config) -> None:

        self.username = config["username"]
        self.password = config["password"]
        self.access_expire = 0
        self.access_token = ""
        self.oss_expire = 0
        self.oss_token = {}





    def get_access_token(self):
        if self.access_expire <= int(time.time()):
            tools.console_log("[WARNING]刷新 cvmart.net 的AccessToken")
            payload = {"username": self.username,"password":self.password}
            resp = requests.post("https://www.cvmart.net/cvmart-user/api/ft/auth/login",data=json.dumps(payload),headers={"content-type":"application/json","user_agent":gc.REQUEST_USER_AGENT})
            data = resp.json()["data"]
            self.access_expire = data["expires_in"] - 120
            self.access_token = "Bearer " + data["access_token"]
            return self.access_token
        return self.access_token
    
    def get_oss_sts(self):
        if self.oss_expire <= int(time.time()):
            resp = requests.get("https://www.cvmart.net/cvmart-user/api/ft/user/file/userFileSTS",headers={"content-type":"application/json","user_agent":gc.REQUEST_USER_AGENT,"authorization":self.get_access_token()})
            self.oss_token = json.loads(resp.text)["data"]
            self.oss_expire = int(time.time()) + 3540
            tools.console_log("[INFO]获取OSS 文件上传授权成功,AccessId:%s,过期时间:%s" % (self.oss_token["accessKeyId"],self.oss_expire))
            return self.oss_token

        return self.oss_token
        
         

    # 上传本地文件
    def upload_file(self,file_path,file_ext='.ts'):
        file_size = os.path.getsize(file_path)

        # 生成上传密钥
        payload = {"fileName":"pytv_" + str(uuid.uuid4())+ file_ext,"fileSize":file_size}
        resp = requests.post("https://www.cvmart.net/cvmart-user/api/ft/user/file/userFile/uploadUrl",data=json.dumps(payload),headers={"content-type":"application/json","user_agent":gc.REQUEST_USER_AGENT,"authorization":self.get_access_token()})
        upload = resp.json()["data"]
        tools.console_log("[LOG]获取OSS 上传签名地址成功,URL:" + upload["url"])

        sts = self.get_oss_sts()
        
        oss_auth = oss2.StsAuth(sts["accessKeyId"],sts["accessKeySecret"],sts["securityToken"])
        oss_bucket = oss2.Bucket(oss_auth,gc.CVMART_OSS_ENDPOINT,gc.CVMART_OSS_BUCKET)
        object_key =  upload["objectName"]

        with open(file_path,"rb") as fileobj:
            oss_bucket.put_object(object_key,fileobj)
        tools.console_log("[INFO]上传本地文件[%s]到OSS[%s]成功" % (file_path,object_key))


        # 请求上传成功的接口 
        payload["objectName"] = upload["objectName"]
        payload["uuidKey"] = upload["uuidKey"]
        resp = requests.post("https://www.cvmart.net/cvmart-user/api/ft/user/file/userFile/uploadCallback",data=json.dumps(payload),headers={"content-type":"application/json","user_agent":gc.REQUEST_USER_AGENT,"authorization":self.get_access_token()})
        tools.console_log("[INFO]文件上传成功!ObjectKey:" + payload["objectName"] )
        return "https://extremevision-js-userfile.oss-cn-hangzhou.aliyuncs.com/"  +  payload["objectName"] 
    
    # 列出oss 上的文件
    def list_oss_file(self):
        resp = requests.get("https://www.cvmart.net/cvmart-user/api/ft/user/file/paginate?current=1&size=100000",headers={"content-type":"application/json","user_agent":gc.REQUEST_USER_AGENT,"authorization":self.get_access_token()})
        return resp.json()["data"]["data"]

    
    # 删除oss 的文件
    def delete_oss_file(self,file_id):
        resp = requests.delete("https://www.cvmart.net/cvmart-user/api/ft/user/file/deleteFile?fileId=" + str(file_id),headers={"content-type":"application/json","authorization":self.get_access_token()})

    def auto_handle_delete(self):
        while True:
            files = self.list_oss_file()
            for file in files:
                file_create_at = int(time.mktime(time.strptime(file["createdAt"], "%Y-%m-%d %H:%M:%S")))
                # 缓存最近 15 分钟的文件
                if file_create_at <= int(time.time()) - 15 * 60 and file["originalName"].starswith("pytv_"):
                    tools.console_log("[WARNGING]删除 OSS 系统上的文件:" + file["originalName"] )
                    self.delete_oss_file(file["id"])
            time.sleep(1) 





