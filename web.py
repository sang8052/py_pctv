import copy
import json
import os
import re
import time
import traceback

import requests
import tools
from flask import Flask, current_app, g, make_response, redirect, request

app = Flask(__name__, static_url_path="/", static_folder=tools.get_local_path() + "/static")


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


def __http_request_payload():
    g.query = request.args.to_dict()
    g.payload = {}
    if "multipart/form-data" in g.content_type or "application/x-www-form-urlencoded" in g.content_type:
        try:
            g.payload = request.form.to_dict()
        except Exception:
            g.payload = {}
    if "application/json" in g.content_type:
        try:
            g.payload = json.loads(request.get_data(as_text=True))
        except Exception:
            g.payload = {}


def json_response(payload, code=200):
    response = make_response(json.dumps(payload, ensure_ascii=False), code)
    response.headers["Content-Type"] = "application/json"
    return response


def _config_path():
    return os.path.join(tools.get_local_path(), "config.json")


def _normalize_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("1", "true", "yes", "on")
    return bool(val)


def _normalize_int(val, default):
    try:
        return int(val)
    except Exception:
        return default


def _version_tuple(text):
    parts = re.findall(r"\d+", str(text or ""))
    if not parts:
        return ()
    return tuple(int(item) for item in parts[:4])


def _is_newer_version(latest, current):
    latest_v = _version_tuple(latest)
    current_v = _version_tuple(current)
    if not latest_v:
        return False
    if not current_v:
        return str(latest).strip() != str(current).strip()
    size = max(len(latest_v), len(current_v))
    latest_v = latest_v + (0,) * (size - len(latest_v))
    current_v = current_v + (0,) * (size - len(current_v))
    return latest_v > current_v


def _get_runtime_config():
    config = copy.deepcopy(getattr(current_app, "_config", {}))
    if not isinstance(config, dict):
        config = {}

    if "app" not in config or not isinstance(config["app"], dict):
        config["app"] = {}
    app_cfg = config["app"]
    app_cfg.setdefault("address", "0.0.0.0")
    app_cfg.setdefault("port", 56765)
    app_cfg.setdefault("thread_log", True)
    app_cfg.setdefault("auto_open_dashboard", True)

    config["video_expire_time"] = _normalize_int(config.get("video_expire_time", 3600), 3600)

    if "update" not in config or not isinstance(config["update"], dict):
        config["update"] = {}
    default_repo = getattr(current_app, "default_github_repo", "matthewlu070111/py_pctv")
    config["update"].setdefault("github_repo", default_repo)

    return config


def _check_5xtv_thread():
    tv_threads = getattr(current_app, "tv_threads", {})
    if not isinstance(tv_threads, dict):
        return False, "线程容器未初始化"
    thread = tv_threads.get("5xtv")
    if thread is None:
        return False, "直播线程未注册"
    if not thread.is_alive():
        return False, "直播线程已停止"
    return True, "直播线程运行中"


def _check_5xtv_m3u8():
    m3u8_path = os.path.join(tools.get_local_path(), "static", "5xtv.m3u8")
    if not os.path.exists(m3u8_path):
        return False, "m3u8 文件不存在"
    file_size = os.path.getsize(m3u8_path)
    if file_size <= 0:
        return False, "m3u8 文件为空"
    age_seconds = time.time() - os.path.getmtime(m3u8_path)
    if age_seconds > 25:
        return False, "m3u8 超过 %.1f 秒未更新" % age_seconds
    return True, "m3u8 正常，最近更新 %.1f 秒前" % age_seconds


@app.before_request
def app_before_request():
    g.request_id = tools.get_uuid()
    g.request_time = tools.get_ms_time()
    __http_request_header()
    __http_request_payload()


@app.after_request
def app_after_response(response):
    response.headers["X-Request-Id"] = g.request_id
    response.headers["X-Use-Time"] = str(tools.get_ms_time() - g.request_time) + " ms"
    if request.method == "OPTIONS":
        response.status_code = 200
    return response


@app.errorhandler(404)
def http_response_nofound(err):
    return json_response({"code": 404, "msg": "request page not found", "data": {"path": request.path}}, 404)


@app.errorhandler(Exception)
def http_response_error(err):
    error_msg = str(err)
    error_response = {
        "code": 500,
        "msg": "unknown error",
        "data": {
            "error": error_msg,
            "debug": traceback.format_exc(),
            "payload": getattr(g, "payload", {}),
            "url": request.url,
        },
    }
    tools.console_log("[WARNING]unexpected error: " + json.dumps(error_response["data"], ensure_ascii=False))
    return json_response(error_response, 500)


@app.route("/tvs", methods=["GET"])
def http_list_tvs():
    tvs = copy.deepcopy(current_app.tvs)
    for tv in tvs:
        tv["is_live"] = True
    return json_response({"code": 0, "msg": "success", "data": tvs})


@app.route("/api/config", methods=["GET"])
def http_get_config():
    config = _get_runtime_config()
    return json_response(
        {
            "code": 0,
            "msg": "success",
            "data": {
                "config": config,
                "app_version": getattr(current_app, "app_version", "unknown"),
                "player_path": "/index.html",
            },
        }
    )


@app.route("/api/config", methods=["POST"])
def http_save_config():
    incoming = g.payload.get("config", g.payload) if isinstance(g.payload, dict) else {}
    if not isinstance(incoming, dict):
        return json_response({"code": 400, "msg": "invalid payload", "data": {}}, 400)

    config = _get_runtime_config()

    app_in = incoming.get("app", {})
    if isinstance(app_in, dict):
        if "address" in app_in:
            config["app"]["address"] = str(app_in["address"]).strip() or "0.0.0.0"
        if "port" in app_in:
            port = _normalize_int(app_in["port"], config["app"]["port"])
            if port <= 0 or port > 65535:
                return json_response({"code": 400, "msg": "port out of range", "data": {}}, 400)
            config["app"]["port"] = port
        if "thread_log" in app_in:
            config["app"]["thread_log"] = _normalize_bool(app_in["thread_log"])

    if "video_expire_time" in incoming:
        config["video_expire_time"] = max(_normalize_int(incoming["video_expire_time"], 3600), 60)

    update_in = incoming.get("update", {})
    if isinstance(update_in, dict) and "github_repo" in update_in:
        config["update"]["github_repo"] = str(update_in["github_repo"]).strip()

    tools.write_file(_config_path(), config)
    current_app._config = config
    return json_response(
        {
            "code": 0,
            "msg": "配置已保存，重启服务后可完全生效",
            "data": {"config": config},
        }
    )


@app.route("/api/status", methods=["GET"])
def http_service_status():
    checks = []
    ok_thread, msg_thread = _check_5xtv_thread()
    checks.append({"name": "5xtv-thread", "ok": ok_thread, "detail": msg_thread})

    ok_m3u8, msg_m3u8 = _check_5xtv_m3u8()
    checks.append({"name": "5xtv-m3u8", "ok": ok_m3u8, "detail": msg_m3u8})

    status = "正常"
    if not all(item["ok"] for item in checks):
        status = "异常"

    return json_response(
        {
            "code": 0,
            "msg": "success",
            "data": {
                "status": status,
                "checks": checks,
                "server_time": tools.format_date("%Y-%m-%d %H:%M:%S"),
            },
        }
    )


@app.route("/api/update/latest", methods=["GET"])
def http_latest_release():
    repo = str(g.query.get("repo", "")).strip()
    if repo == "":
        repo = _get_runtime_config()["update"].get("github_repo", "").strip()
    if not re.match(r"^[^/\s]+/[^/\s]+$", repo):
        return json_response({"code": 400, "msg": "invalid github repo, expected owner/repo", "data": {}}, 400)

    release_url = "https://api.github.com/repos/%s/releases/latest" % repo
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "py_pctv-update-checker"}
    try:
        resp = requests.get(release_url, headers=headers, timeout=10)
    except Exception as err:
        return json_response({"code": 502, "msg": "request github failed: %s" % err, "data": {}}, 502)

    if resp.status_code == 404:
        repo_check_url = "https://api.github.com/repos/%s" % repo
        try:
            repo_resp = requests.get(repo_check_url, headers=headers, timeout=10)
        except Exception as err:
            return json_response({"code": 502, "msg": "request github failed: %s" % err, "data": {}}, 502)
        if repo_resp.status_code == 200:
            current_version = getattr(current_app, "app_version", "")
            return json_response(
                {
                    "code": 0,
                    "msg": "no release published",
                    "data": {
                        "repo": repo,
                        "current_version": current_version,
                        "latest_version": "",
                        "has_update": False,
                        "name": "",
                        "html_url": "https://github.com/%s/releases" % repo,
                        "published_at": "",
                        "prerelease": False,
                        "no_release": True,
                    },
                }
            )

    if resp.status_code != 200:
        msg = "github api error status=%d" % resp.status_code
        try:
            data = resp.json()
            if "message" in data:
                msg = data["message"]
        except Exception:
            pass
        return json_response({"code": 502, "msg": msg, "data": {"repo": repo}}, 502)

    release = resp.json()
    latest_version = release.get("tag_name") or release.get("name") or ""
    current_version = getattr(current_app, "app_version", "")
    has_update = _is_newer_version(latest_version, current_version)
    return json_response(
        {
            "code": 0,
            "msg": "success",
            "data": {
                "repo": repo,
                "current_version": current_version,
                "latest_version": latest_version,
                "has_update": has_update,
                "name": release.get("name", ""),
                "html_url": release.get("html_url", ""),
                "published_at": release.get("published_at", ""),
                "prerelease": bool(release.get("prerelease", False)),
            },
        }
    )


@app.route("/", methods=["GET"])
def http_request_index():
    return redirect("/dashboard.html", 301)

