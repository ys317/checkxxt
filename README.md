## 仓库介绍

本仓库主要用于自动检测学习通作业截止时间并汇总，可以通过设定比如早上八点自动运行代码来检测 ~~初衷是防止本人忘记作业~~

## 使用方式

#### 通过GitHub运行

**添加配置项的方式：**

1. 打开你的 GitHub 仓库页面，点击顶部的 **Settings**（设置）。
2. 在左侧菜单栏中找到 **Secrets and variables**，展开后点击 **Actions**。
3. 点击右上角的绿色按钮 **New repository secret**。
4. 依次添加以下 4 个密钥：

| **Name (名称)**     | **Value (填入的内容)**            | **说明**                                     |
| ------------------- | --------------------------------- | -------------------------------------------- |
| `PHONE`             | `138xxxx`                         | 你的超星手机号账号                           |
| `PASSWORD`               | `你的密码`                        | 你的超星登录密码                             |
| `ENABLE_WECOM_PUSH` | `True`                            | 是否开启企业微信推送（填 `True` 或 `False`） |
| `WECOM_URL`         | `https://qyapi.weixin.qq.com/...` | 你的企业微信机器人完整的 Webhook 链接        |
<img width="1851" height="1290" alt="P1" src="https://github.com/user-attachments/assets/d778cc62-3931-41a9-9075-d6e372698c2e" />



#### 设定Windows任务计划程序

##### 第一步：下载或复制checkxxt_windows.py到你的电脑

##### 第二步：准备好你的路径

在开始之前，你需要知道两个重要路径：

1. **Python 解释器的路径**：通常是 `python.exe` 的绝对路径。 *(例如：`C:\Users\YourName\AppData\Local\Programs\Python\Python310\python.exe`)* *(你可以打开命令提示符 cmd，输入 `where python` 来查找)*
2. **你的 Python 脚本路径**：你的 `.py` 文件所在的绝对路径。 *(例如：`D:\MyScripts\auto_task.py`)*

##### 第三步：创建定时任务

1. **打开任务计划程序**：按 `Win + S` 快捷键打开搜索，输入“任务计划程序”并打开它（或者按 `Win + R` 输入 `taskschd.msc`）。
2. **创建基本任务**：在右侧的“操作”栏中，点击“创建基本任务...”。
3. **命名**：给这个任务起个名字（比如“自动运行Python作业”），点击“下一步”。
4. **设置触发器**：选择你想运行的频率（比如每天、每周、计算机启动时等），点击“下一步”，并设置具体的执行时间。
5. **设置操作**：选择“启动程序”，点击“下一步”。
6. **配置程序参数**：
   - **程序或脚本**：填入你的 **Python 解释器路径**（比如 `C:\Python310\python.exe`）。
   - **添加参数(可选)**：填入你的 **Python 脚本绝对路径**（比如 `D:\MyScripts\auto_task.py`）。
7. **完成**：点击“下一步”，然后点击“完成”。
<img width="564" height="626" alt="P2" src="https://github.com/user-attachments/assets/bf106d77-b453-45dc-bed0-200d1d269d9d" />



#### 通过企业微信发送消息给手机（可选）

因为通过GitHub运行一般会在邮件里收到通知，所以企业微信通知可以说是一个可选项，配置也会相对麻烦一点

获取webhook[企业微信群机器人获取 Webhook方法](https://www.tencentcloud.com/zh/document/product/1254/78645)

