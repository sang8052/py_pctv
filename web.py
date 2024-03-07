'''
Author: SudemQaQ
Date: 2024-03-07 11:18:05
email: mail@szhcloud.cn
Blog: https://blog.szhcloud.cn
github: https://github.com/sang8052
LastEditors: SudemQaQ
LastEditTime: 2024-03-07 15:08:19
Description: 
'''
import json,traceback,copy
import tools
from flask import Flask,request,current_app,g,make_response,redirect
app = Flask(__name__,static_url_path="/",static_folder=tools.get_local_path() + "/static")


# 初始化 HTTP 请求的 HEADER 
def __http_request_header():
    g.request_headers = {}
    g.content_type = ""
    g.user_agent = ""
    g.authorization = ""
    g.client_ip = request.remote_addr
    request_headers = dict(request.headers)
    for key in request_headers.keys():
        g.request_headers[key.lower()] = request_headers[key]
    if "authorization" in g.request_headers.keys():
        g.authorization = g.request_headers["authorization"]
    if "user-agent" in g.request_headers.keys():
        g.user_agent = g.request_headers["user-agent"]
    if "content-type" in g.request_headers.keys():
        g.content_type = g.request_headers["content-type"]


# 初始化 HTTP 请求的 QUERY / PAYLOAD
def __http_request_payload():
    g.query = request.args.to_dict()
    g.payload = {}
    if "application/form-data" in g.content_type or "application/x-www-form-urlencode" in g.content_type:
        try:
            g.payload = request.form.to_dict()
        except:
            g.payaload = {}
    if "application/json" in g.content_type:
        try:
            g.payload = json.loads(request.get_data(as_text=True))
        except:
            g.payload = {}


def json_response(payload,code=200):
    response = make_response(json.dumps(payload,ensure_ascii=False),code)
    response.headers["Content-Type"] = "application/json"
    return response


@app.before_request
def app_before_request():
    g.request_id = tools.get_uuid()
    g.request_time = tools.get_ms_time()
    __http_request_header()
    __http_request_payload()

@app.after_request
def app_after_response(response):
    response.headers["X-Request-Id"] = g.request_id
    response.headers["X-Use-Time"] = str (tools.get_ms_time() - g.request_time ) + " ms"
    if request.method == "OPTIONS":
        response.status_code = 200 
    return response

@app.errorhandler(404)
def http_response_nofound(err):
    return json_response({"code":404,"msg":"request page not found","data":{"path":request.path}},404)

@app.errorhandler(Exception)
def http_response_error(err):
    error_msg = str(err)
    error_response = {"code":500,"msg":"unknow error","data":{"error":error_msg,"debug":traceback.format_exc(),"payload":g.payload,"url":request.url}}
    tools.console_log("[WARNING]发生未知异常,ERROR:" + json.dumps(error_response["data"],ensure_ascii=False))
    return json_response(error_response,500)

# 列出当前支持播放的tv 结构列表
@app.route("/tvs",methods=['GET'])
def http_list_tvs():
    tvs = copy.deepcopy(current_app.tvs)
    for tv in tvs :
        if current_app.cache._has(tv["live_heart"]):
            tv_heart = current_app.cache._get_value(tv["live_heart"])
            tv["is_live"] = True
            tv["update_time"] = tv_heart["download_time"]
        else:
            tv["is_live"] = False
    return json_response({"code":0,"msg":"操作成功","data":tvs})

@app.route("/",methods=['GET'])
def http_request_index():
    return redirect("/index.html",301)
        
    

