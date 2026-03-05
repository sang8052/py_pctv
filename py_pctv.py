"""
Author: SudemQaQ, imxiaoanag
Date: 2026-03-05
Blog: https://www.imxiaoanag.com
github: https://github.com/matthewlu070111/py_pctv
LastEditors: imxiaoanag
Description:
"""

import os
import shutil
import signal
import sys
import threading
import time
import webbrowser

import colorama
from werkzeug.serving import make_server

import gconfig as gc
import tools
import web
from tv import tv_5xtv

try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    pystray = None
    Image = None
    ImageDraw = None

try:
    import rumps
except Exception:
    rumps = None

app_version = "2.0.0"
DEFAULT_REPO = "matthewlu070111/py_pctv"
_runtime = None


def normalize_config(config):
    if not isinstance(config, dict):
        config = {}

    app_cfg = config.setdefault("app", {})
    if not isinstance(app_cfg, dict):
        app_cfg = {}
        config["app"] = app_cfg
    app_cfg.setdefault("address", "0.0.0.0")
    app_cfg.setdefault("port", 56765)
    app_cfg.setdefault("thread_log", True)
    app_cfg.setdefault("auto_open_dashboard", True)
    if sys.stdout is None:
        app_cfg["thread_log"] = False

    update_cfg = config.setdefault("update", {})
    if not isinstance(update_cfg, dict):
        update_cfg = {}
        config["update"] = update_cfg
    update_cfg.setdefault("github_repo", DEFAULT_REPO)

    config.setdefault("video_expire_time", 3600)
    return config


def get_bind_host(config):
    host = str(config.get("app", {}).get("address", "0.0.0.0")).strip()
    return host or "0.0.0.0"


def get_access_host(config):
    host = get_bind_host(config)
    if host in ("0.0.0.0", "::"):
        return "127.0.0.1"
    return host


def get_port(config):
    try:
        port = int(config.get("app", {}).get("port", 56765))
        if port <= 0 or port > 65535:
            return 56765
        return port
    except Exception:
        return 56765


def build_url(config, path):
    return "http://%s:%d%s" % (get_access_host(config), get_port(config), path)


def open_dashboard(config):
    webbrowser.open(build_url(config, "/dashboard.html"))


def open_player(config):
    webbrowser.open(build_url(config, "/index.html"))


def ensure_runtime_files():
    local_root = tools.get_local_path()
    bundle_root = getattr(sys, "_MEIPASS", local_root)
    if bundle_root == local_root:
        return

    src_config = os.path.join(bundle_root, "config.json")
    dst_config = os.path.join(local_root, "config.json")
    if os.path.exists(src_config) and not os.path.exists(dst_config):
        shutil.copy2(src_config, dst_config)

    src_static = os.path.join(bundle_root, "static")
    dst_static = os.path.join(local_root, "static")
    if os.path.isdir(src_static) and not os.path.isdir(dst_static):
        shutil.copytree(src_static, dst_static)

    src_icon = os.path.join(bundle_root, "icon.ico")
    dst_icon = os.path.join(local_root, "icon.ico")
    if os.path.exists(src_icon) and not os.path.exists(dst_icon):
        shutil.copy2(src_icon, dst_icon)

    src_icns = os.path.join(bundle_root, "icon.icns")
    dst_icns = os.path.join(local_root, "icon.icns")
    if os.path.exists(src_icns) and not os.path.exists(dst_icns):
        shutil.copy2(src_icns, dst_icns)

    src_template = os.path.join(bundle_root, "icon_template.png")
    dst_template = os.path.join(local_root, "icon_template.png")
    if os.path.exists(src_template) and not os.path.exists(dst_template):
        shutil.copy2(src_template, dst_template)


def get_runtime_icon_path():
    if sys.platform == "darwin":
        local_icns = os.path.join(tools.get_local_path(), "icon.icns")
        if os.path.exists(local_icns):
            return local_icns
        bundle_root = getattr(sys, "_MEIPASS", "")
        if bundle_root:
            bundle_icns = os.path.join(bundle_root, "icon.icns")
            if os.path.exists(bundle_icns):
                return bundle_icns

    local_icon = os.path.join(tools.get_local_path(), "icon.ico")
    if os.path.exists(local_icon):
        return local_icon

    bundle_root = getattr(sys, "_MEIPASS", "")
    if bundle_root:
        bundle_icon = os.path.join(bundle_root, "icon.ico")
        if os.path.exists(bundle_icon):
            return bundle_icon

    return ""


def get_runtime_menu_icon_path():
    if sys.platform == "darwin":
        local_template = os.path.join(tools.get_local_path(), "icon_template.png")
        if os.path.exists(local_template):
            return local_template
        bundle_root = getattr(sys, "_MEIPASS", "")
        if bundle_root:
            bundle_template = os.path.join(bundle_root, "icon_template.png")
            if os.path.exists(bundle_template):
                return bundle_template
    return get_runtime_icon_path()


class AppRuntime:
    def __init__(self, config):
        self.config = config
        self.server = None
        self.server_thread = None
        self.live_thread = None
        self.running = False
        self.server_error = None

    def _serve_forever(self):
        try:
            self.server.serve_forever()
        except Exception as err:
            self.server_error = str(err)
            self.running = False
            tools.console_log("[ERROR]Web服务启动失败: %s" % err)

    def start(self):
        if self.running:
            return
        tools.console_log("[INFO]运行路径: " + tools.get_local_path())

        web.app.tvs = []
        web.app._config = self.config
        web.app.app_version = app_version
        web.app.default_github_repo = self.config.get("update", {}).get("github_repo", DEFAULT_REPO)

        bind_host = get_bind_host(self.config)
        bind_port = get_port(self.config)
        try:
            self.server = make_server(bind_host, bind_port, web.app, threaded=True)
        except Exception as err:
            self.server_error = str(err)
            tools.console_log("[ERROR]Web服务启动失败: %s" % err)
            self.running = False
            return

        self.live_thread = tv_5xtv.tv_5xtv(self.config, 1)
        self.live_thread.start()
        web.app.tv_threads = {"5xtv": self.live_thread}
        tools.console_log("[INFO]线程[五星体育直播]启动成功")

        web.app.tvs.append(
            {
                "name": "五星体育",
                "thread_id": 1,
                "live": gc.APP_5XTV_M3U8_FILE.replace("./static/", ""),
            }
        )
        self.server_thread = threading.Thread(target=self._serve_forever, daemon=True)
        self.server_thread.start()
        self.running = True
        tools.console_log("[INFO]WSGI Listen %s:%d" % (bind_host, bind_port))

    def stop(self):
        if not self.running:
            return
        self.running = False
        tools.console_log("[WARNING]正在退出服务...")

        if self.live_thread:
            try:
                self.live_thread.stop()
                self.live_thread.join(timeout=3)
            except Exception:
                pass

        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass

        tools.console_log("[INFO]服务已退出")


def create_tray_image():
    if Image is None:
        return None

    icon_path = get_runtime_icon_path()
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path)
        except Exception:
            pass

    image = Image.new("RGB", (64, 64), (16, 52, 80))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 56, 56), radius=10, fill=(24, 122, 185))
    draw.text((20, 22), "TV", fill=(255, 255, 255))
    return image


def run_without_tray(runtime):
    tools.console_log("[WARNING]当前环境不可用系统托盘，进入前台常驻模式")
    if runtime.config.get("app", {}).get("auto_open_dashboard", True):
        threading.Timer(1.2, lambda: open_dashboard(runtime.config)).start()
    try:
        while runtime.running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        runtime.stop()


def _tray_supported():
    if pystray is None or Image is None:
        if sys.platform == "darwin" and rumps is not None:
            return True
        return False
    if os.name == "nt":
        return True
    if sys.platform == "darwin":
        return True
    return False


def run_tray(runtime):
    if not _tray_supported():
        run_without_tray(runtime)
        return

    if sys.platform == "darwin" and rumps is not None:
        class MacTrayApp(rumps.App):
            def __init__(self):
                icon_path = get_runtime_menu_icon_path()
                super().__init__(
                    "PCTV",
                    icon=icon_path if icon_path else None,
                    template=True,
                    quit_button=None,
                )
                self.menu = [
                    rumps.MenuItem("打开控制台", self.on_open_dashboard),
                    rumps.MenuItem("打开播放页", self.on_open_player),
                    None,
                    rumps.MenuItem("退出", self.on_exit),
                ]

            def on_open_dashboard(self, _):
                open_dashboard(runtime.config)

            def on_open_player(self, _):
                open_player(runtime.config)

            def on_exit(self, _):
                runtime.stop()
                rumps.quit_application()

        if runtime.config.get("app", {}).get("auto_open_dashboard", True):
            threading.Timer(1.2, lambda: open_dashboard(runtime.config)).start()
        MacTrayApp().run()
        return

    def on_open_dashboard(icon, item):
        open_dashboard(runtime.config)

    def on_open_player(icon, item):
        open_player(runtime.config)

    def on_exit(icon, item):
        runtime.stop()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("打开控制台", on_open_dashboard),
        pystray.MenuItem("打开播放页", on_open_player),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", on_exit),
    )
    tray = pystray.Icon("py_pctv", create_tray_image(), "PCTV", menu)
    if runtime.config.get("app", {}).get("auto_open_dashboard", True):
        threading.Timer(1.2, lambda: open_dashboard(runtime.config)).start()
    tray.run()


def signal_handler(sig, frame):
    del frame
    if sig == signal.SIGINT:
        tools.console_log("[WARNING]收到退出信号")
        if _runtime:
            _runtime.stop()
        raise SystemExit(0)


if __name__ == "__main__":
    colorama.init()
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)

    print("========================================")
    print("PCTV流媒体播放")
    print("Author:  SudemQaQ, imxiaoanag")
    print("Version: " + app_version)
    print("========================================")

    ensure_runtime_files()
    os.chdir(tools.get_local_path())
    config = normalize_config(tools.read_json("config.json"))
    tools.write_file("config.json", config)

    _runtime = AppRuntime(config)
    _runtime.start()
    if not _runtime.running:
        tools.console_log("[ERROR]服务未启动，程序退出")
        raise SystemExit(1)
    run_tray(_runtime)
