import os 
import logging
import colorlog


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handle = logging.StreamHandler()
console_handle.setLevel(logging.DEBUG)
file_handle = logging.FileHandler('run.log')
file_handle.setLevel(logging.DEBUG)

formatter = colorlog.ColoredFormatter(
   "%(log_color)s%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

console_handle.setFormatter(formatter)
file_handle.setFormatter(formatter)

logger.addHandler(console_handle)
logger.addHandler(file_handle)

if __name__ == "__main__":

    current_path =os.getcwd()
    logger.info("当前文件目录:" + current_path)

    fp = open("ffmpeg_filelist.txt","w")
    for root,dirs,files in os.walk(current_path):
        for file in files:
            if file.endswith(".ts") and file.startswith("5xtv_"):
                fp.write("file \'%s\'\n" % (root + os.sep + file))
    fp.close()
    logger.info("生成需要合并的分片目录")
    logger.critical("开始合并视频分片")
    shell = "ffmpeg.exe -f concat -safe 0 -i ffmpeg_filelist.txt -vcodec copy -acodec copy 5xtv.mp4"
    os.system(shell)
    logger.info("合并结束")