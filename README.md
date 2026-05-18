## 仓库介绍

本仓库主要用于自动检测学习通是否有作业截止通知，可以通过设定比如早上八点自动运行代码来检测 ~~初衷是防止本人忘记作业~~

## 使用方式

**添加配置项的方式：**

1. 打开你的 GitHub 仓库页面，点击顶部的 **Settings**（设置）。
2. 在左侧菜单栏中找到 **Secrets and variables**，展开后点击 **Actions**。
3. 点击右上角的绿色按钮 **New repository secret**。
4. 依次添加以下 4 个密钥：

| **Name (名称)**     | **Value (填入的内容)**            | **说明**                                     |
| ------------------- | --------------------------------- | -------------------------------------------- |
| `CHAOXING_PHONE`    | `138xxxx`                         | 你的超星手机号账号                           |
| `CHAOXING_PWD`      | `你的密码`                        | 你的超星登录密码                             |
| `ENABLE_WECOM_PUSH` | `True`                            | 是否开启企业微信推送（填 `True` 或 `False`） |
| `WECOM_WEBHOOK_URL` | `https://qyapi.weixin.qq.com/...` | 你的企业微信机器人完整的 Webhook 链接        |

### 通过企业微信发送消息给手机（可选）

因为通过GitHub运行一般会在邮件里收到通知，所以企业微信通知可以说是一个可选项，配置也会相对麻烦一点

获取webhook[企业微信群机器人获取 Webhook方法](https://www.tencentcloud.com/zh/document/product/1254/78645)

