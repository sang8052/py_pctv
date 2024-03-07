<!--
 * @Author: SudemQaQ
 * @Date: 2024-03-07 15:34:25
 * @email: mail@szhcloud.cn
 * @Blog: https://blog.szhcloud.cn
 * @github: https://github.com/sang8052
 * @LastEditors: SudemQaQ
 * @LastEditTime: 2024-03-07 15:47:24
 * @Description: 
-->
# 项目简介
这是一个基于 Python 开发的 个人PC端电视项目。项目的宗旨是解决因 电视家等APP 被关闭后个人用户观看TV 困难的问题。
环境需求:

1. python >= 3.8
2. redis  >= 5.0 

![image.png](https://cdn.nlark.com/yuque/0/2024/png/2484069/1709796812720-6ba12a6e-de31-4507-a050-3c4929a3c35b.png#averageHue=%23272727&clientId=ua7cee7c3-81fa-4&from=paste&height=491&id=uf1268078&originHeight=491&originWidth=970&originalType=binary&ratio=1&rotation=0&showTitle=false&size=75096&status=done&style=none&taskId=uefd62279-557e-4142-8f26-aa1ef75639c&title=&width=970)
# 一、快速开始
## 安装redis 数据库
下载 windows 版本的 redis 安装包 (5.0.14.1)
下载地址[ 奶牛快传](https://cowtransfer.com/s/14328537805f46)
按照默认配置,正常安装
![image.png](https://cdn.nlark.com/yuque/0/2024/png/2484069/1709792159103-f8154e31-81eb-43e1-b300-78f97f72364d.png#averageHue=%23eeeceb&clientId=u19b91260-0f48-4&from=paste&height=389&id=uec48f2e1&originHeight=389&originWidth=499&originalType=binary&ratio=1&rotation=0&showTitle=false&size=31460&status=done&style=none&taskId=u72475ab3-b785-4536-8e2c-4d7096864e3&title=&width=499)

安装完成后,修改安装目录下的 redis.windows-service.conf 文件
![image.png](https://cdn.nlark.com/yuque/0/2024/png/2484069/1709792564955-e1c2fcc9-56ce-415d-ae95-f01d6ba2a873.png#averageHue=%23f8f7f5&clientId=u19b91260-0f48-4&from=paste&height=377&id=ua78bfe15&originHeight=377&originWidth=676&originalType=binary&ratio=1&rotation=0&showTitle=false&size=41962&status=done&style=none&taskId=uafc710be-71b7-4879-89a3-e862c414363&title=&width=676)

1.修改文件的第 64 行, 将redis 的监听地址改成 0.0.0.0 

![image.png](https://cdn.nlark.com/yuque/0/2024/png/2484069/1709792552422-c1a55177-06ef-4234-aa87-85e022fa19f6.png#averageHue=%23f3eeec&clientId=u19b91260-0f48-4&from=paste&height=239&id=ucbf7bbf7&originHeight=239&originWidth=396&originalType=binary&ratio=1&rotation=0&showTitle=false&size=14727&status=done&style=none&taskId=ua990e10f-123f-4dac-b99b-61fe32225fe&title=&width=396)

2.修改文件的第 503 行 ，取消注释，并给redis 加上密码 

![image.png](https://cdn.nlark.com/yuque/0/2024/png/2484069/1709792482965-3446e2ae-d660-44ed-93a3-ed4ca4d30f49.png#averageHue=%23f3efed&clientId=u19b91260-0f48-4&from=paste&height=280&id=ue4f2fd5f&originHeight=280&originWidth=663&originalType=binary&ratio=1&rotation=0&showTitle=false&size=29980&status=done&style=none&taskId=u7c07a332-a41a-48c5-a6ff-39c03829376&title=&width=663)

保存修改的文件，然后打开任务管理器
在服务选项卡中下拉找到Redis 服务，右击重启启动该服务

![image.png](https://cdn.nlark.com/yuque/0/2024/png/2484069/1709792638781-19a1f244-857e-4045-a4e1-36e69294adba.png#averageHue=%23f5f1ef&clientId=u19b91260-0f48-4&from=paste&height=604&id=u57bd8e9a&originHeight=604&originWidth=683&originalType=binary&ratio=1&rotation=0&showTitle=false&size=82309&status=done&style=none&taskId=u3adf36d9-e5e5-49f1-9037-00b2e2c7944&title=&width=683)
## 修改配置文件 
修改项目文件夹下的 config.json 中 redis 的密码

![image.png](https://cdn.nlark.com/yuque/0/2024/png/2484069/1709793084694-575ed91c-71b3-4b74-96d8-250967a3ee43.png#averageHue=%23f9f7f7&clientId=u19b91260-0f48-4&from=paste&height=352&id=u6edf01d5&originHeight=352&originWidth=653&originalType=binary&ratio=1&rotation=0&showTitle=false&size=24922&status=done&style=none&taskId=u05d357e9-3e52-4425-925c-7c55c4eb849&title=&width=653)


# 二、在浏览器中观看
项目默认使用 9655 端口，项目启动后你可以打开 http://localhost:9655 观看视频直播。
![image.png](https://cdn.nlark.com/yuque/0/2024/png/2484069/1709796791010-41d62709-a47a-4eb6-823d-ea8fb9ac1e26.png#averageHue=%232b2e2d&clientId=ua7cee7c3-81fa-4&from=paste&height=899&id=u92a7e082&originHeight=899&originWidth=1587&originalType=binary&ratio=1&rotation=0&showTitle=false&size=1648344&status=done&style=none&taskId=u47cfdae5-f7d4-4e57-9ad5-fea59f1d86a&title=&width=1587)

