import os,sys,time,uuid,json,threading,hashlib
import requests
from Crypto.Cipher import DES
import gconfig as gc  


console_lock = threading.Lock()


def mkdir_ex(path):
    if not os.path.exists(path):
        os.mkdir(path)

def get_uuid():
    return str(uuid.uuid4())

def get_ms_time():
    return int(time.time() * 1000)

def kill_pid(pid):
    shell = ""
    if sys.platform.startswith('win'):
        shell = "taskkill /PID %d /F" % (pid)
    if sys.platform.startswith('linux'):
        shell = "kill -9 %d" % (pid)
    if shell != "":
        os.system(shell)


def get_local_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def download_file(url, local_path,headers = {}, name="",thread_id = 0):
    from tqdm import tqdm
    if name != "":
        console_log("[LOG]开始从[%s]下载文件[%s]" % (url, name),thread_id)
    else:
        console_log("[LOG]开始从[%s]下载文件" % (url),thread_id)
    status = False
    try:
        
        requests.packages.urllib3.disable_warnings()
        resp = requests.get(url, stream=True, allow_redirects=True, headers=headers, verify=False, timeout=5)
        file_size = int(resp.headers['Content-Length']) if 'Content-Length' in resp.headers else None
        if thread_id < 0:
            file_size = None
        if file_size:
            p = tqdm(total=file_size, unit="B", unit_scale=True, unit_divisor=1024, leave=True)
            if thread_id != 0:
                 thread_text = "{THREAD-%d}" % (thread_id)
                 p.set_description("%s下载文件" % (thread_text))
            else:
                p.set_description("下载文件")
        fp = open(local_path, "wb")
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                fp.write(chunk)
                if file_size:
                    p.update(len(chunk))
        if file_size:
            p.close()
        status = True
    except Exception as err:
        console_log("[ERROR]从[%s]下载文件是遇到错误,文件下载失败!err:" + str(err),thread_id)

    console_log("[INFO]从[%s]下载文件到[%s]成功" % (url, local_path),thread_id)
    return status


def get_file_size(path):
    return os.path.getsize(path)

def file_hash(path):
    with open(path, 'rb') as fp:
        md5 = hashlib.md5(fp.read()).hexdigest()
    return md5

def format_date(format="%Y-%m-%d %H:%M:%S", times=None):
    if not times: times = int(time.time())
    time_local = time.localtime(times)
    return time.strftime(format, time_local)
    

def console_log(content,thread_id = 0):
    console_lock.acquire()
    if thread_id > 0:
        thread_text = "{THREAD-%d}" % (thread_id)
    else:
        thread_text = ""
    console = "%s[%s]%s" % (thread_text,format_date(), content)
    color_id = 37
    if str_include(console, '[INFO]') != -1:
        color_id = 32
    if str_include(console, '[WARNING]') != -1:
        color_id = 33
    if str_include(console, '[SQL]') != -1:
        color_id = 34
    if str_include(console, '[DEBUG]') != -1:
        color_id = 35
    if str_include(console, '[ERROR]') != -1:
        color_id = 31
    log = "\033[%dm%s\033[0m" % (color_id, console)
    if thread_id >= 0:
        print(log,flush=True)
        sys.stdout.flush()
    console_lock.release()

def str_include(str, include):
    try:
        index = str.index(include)
        return index
    except:
        return -1

def size_to_byte(size):
    size = size.upper()
    if str_include(size,"KB") != -1:
        size = int(float(size.replace("KB","").strip()) * 1024)
    if str_include(size,"MB") != -1:
        size = int(float(size.replace("MB","").strip()) * 1024 * 1024)
    if str_include(size,"GB") != -1:
        size = int(float(size.replace("GB","").strip()) * 1024 * 1024 * 1024)
    if str_include(size,"TB") != -1:
        size = int(float(size.replace("TB","").strip()) * 1024 * 1024 * 1024 * 1024)
    return size



def read_json(filename):
    content = read_file(filename)
    try:
        return json.loads(content)
    except Exception as err:
        console_log("[ERROR]读取JSON文件[%s]失败" % (filename))
        return {}

def read_file(filename):
    try:
        fp = open(filename,"r",encoding='utf-8')
    except:
        fp = open(filename,"r",encoding='gbk')
    content = fp.read()
    fp.close()
    return content

def write_file(filename,content):
    fp = open(filename,'w',encoding='utf-8')
    if type(content) == type({}):
        content = json.dumps(content)
    fp.write(content)
    fp.close()

def is_integer(s):
    return s.isdigit() and int(s) == float(s)





def text_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()



def is_json(text):
    if type(text) != type("str"):
        return False
    if text == "":
        return False
    try:
        json.loads(text)
        return True
    except Exception as err:
        return False
    
def is_object(val):
    if type(val) == type([]):
        return True
    if type(val) == type({}):
        return True
    return False


def crypto_decrypt(des_key,data):
    cryptor = DES.new(des_key, DES.MODE_ECB)
    decode_bytes = cryptor.decrypt(bytes.fromhex(data)).replace(b"\x05", b"")
    return decode_bytes.decode()


