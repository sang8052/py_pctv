<!--
 * @Author: SudemQaQ
 * @Date: 2024-03-07 15:34:25
 * @email: mail@szhcloud.cn
 * @Blog: https://blog.szhcloud.cn
 * @github: https://github.com/sang8052
 * @LastEditors: SudemQaQ
 * @LastEditTime: 2024-09-22 23:15:03
 * @Description: 
-->
# 项目简介
这是一个基于 Python 开发的 个人PC端电视项目。目前仅可用于观看五星体育的直播  

环境需求:

1. python >= 3.8
2. ffmpeg 
3. zlmediaserver

V1.2 版本（预发布）
1.本地不再下载切片文件,改为使用 ffmpeg 直接拉流   
2.修复五星体育音画不同步的问题, 使用 ffmpeg 在本地对流进行重编码校正,并推流到 ZLM 进行播放
3.不再使用Flask 作为默认的Web 容器,改为使用 zlm 提供HTTP 访问的能力
4.前端界面优化,完全重构的前端播放界面,考虑接入弹幕平台(寻求赞助)


# 一、在浏览器中观看
项目默认使用 9655 端口，项目启动后你可以打开 http://localhost:9655 观看视频直播。
![image.png](https://cdn.nlark.com/yuque/0/2024/png/2484069/1709796791010-41d62709-a47a-4eb6-823d-ea8fb9ac1e26.png#averageHue=%232b2e2d&clientId=ua7cee7c3-81fa-4&from=paste&height=899&id=u92a7e082&originHeight=899&originWidth=1587&originalType=binary&ratio=1&rotation=0&showTitle=false&size=1648344&status=done&style=none&taskId=u47cfdae5-f7d4-4e57-9ad5-fea59f1d86a&title=&width=1587)

