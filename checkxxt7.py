import time
import requests
from playwright.sync_api import sync_playwright

# ================= 配置区 =================
# 替换为你企业微信群机器人的 Webhook 地址
WECOM_WEBHOOK_URL = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key='  
CHAOXING_PHONE = ''          # 你的超星账号
CHAOXING_PWD = ''            # 你的超星密码
# ==========================================


def send_wecom_push(title, content):
    """
    使用企业微信群机器人发送 Markdown 格式的推送
    """
    if not WECOM_WEBHOOK_URL or 'YOUR_KEY_HERE' in WECOM_WEBHOOK_URL:
        print(" [提示] 未配置企业微信 Webhook 链接，跳过微信推送。")
        return

    # 组装 Markdown 格式文本内容
    markdown_text = f"### <font color=\"warning\">{title}</font>\n\n{content}"
    
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown_text
        }
    }
    
    try:
        response = requests.post(WECOM_WEBHOOK_URL, json=data)
        
        # 尝试解析 JSON 前，先判断是不是正常的 200 响应
        if response.status_code != 200:
            print(f" 企业微信请求失败！HTTP 状态码: {response.status_code}")
            print(f" 服务器返回的原始内容: {response.text}")
            return

        # 尝试解析 JSON
        try:
            result = response.json()
            if result.get('errcode') == 0:
                print(" 企业微信提醒推送成功！")
            else:
                print(f" 企业微信提醒推送失败：{result}")
        except Exception as json_err:
            print(f" 无法解析服务器返回的数据，原始内容为：\n{response.text}")
            
    except Exception as e:
        print(f" 企业微信推送网络请求异常：{e}")


def extract_notice_paragraphs(detail_page):
    """精准提取 .noticeContent 下的 <p> 标签文本"""
    try:
        detail_page.wait_for_selector('.noticeContent', state='attached', timeout=8000)
    except:
        return []
    
    time.sleep(1)
    p_elements = detail_page.locator('.noticeContent > p').all()
    
    lines = []
    for p in p_elements:
        try:
            text = p.inner_text(timeout=2000).strip()
            if text:
                lines.append(text)
        except:
            continue
    
    return lines


def check_chaoxing_homework():
    summary_messages = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        inbox_url = "https://notice.chaoxing.com/pc/notice/myNotice"
        
        print(" 正在访问超星通知中心...")
        page.goto(inbox_url)

        try:
            page.wait_for_selector('input[id="phone"]', timeout=3000)
            need_login = True
        except:
            need_login = False

        if need_login:
            print(" 正在自动输入账号密码登录...")
            page.fill('input[id="phone"]', CHAOXING_PHONE)
            page.fill('input[id="pwd"]', CHAOXING_PWD)
            page.click('#loginBtn')
            page.wait_for_url("**/pc/notice/myNotice", timeout=10000)

        print(" 已进入收件箱，正在扫描作业通知...")

        try:
            page.wait_for_selector('.notice_title', timeout=5000)
            all_titles_text = page.locator('.notice_title').all_inner_texts()
            target_indices = []
            
            for index, text in enumerate(all_titles_text):
                if "作业结束提醒" in text or "作业截止" in text:
                    target_indices.append(index)
            
            if not target_indices:
                print(" 当前没有新的作业截止提醒。")
            else:
                print(f" 扫描完毕,发现 {len(target_indices)} 条作业通知。")
                
                for i in target_indices:
                    if page.url != inbox_url:
                        page.goto(inbox_url)
                        page.wait_for_selector('.notice_title', timeout=5000)

                    target_element = page.locator('.notice_title').nth(i)
                    title_text = target_element.inner_text()
                    
                    print("\n" + "═" * 50)
                    print(f" 正在提取: {title_text}")
                    
                    pages_before_click = len(context.pages)
                    
                    try:
                        with context.expect_page(timeout=3000) as new_page_info:
                            target_element.click(force=True)
                        detail_page = new_page_info.value
                        is_new_tab = True
                        try:
                            detail_page.wait_for_load_state('domcontentloaded', timeout=8000)
                        except:
                            pass
                    except:
                        time.sleep(1.5)
                        if len(context.pages) > pages_before_click:
                            detail_page = context.pages[-1]
                            is_new_tab = True
                        else:
                            detail_page = page
                            is_new_tab = False
                    
                    lines = extract_notice_paragraphs(detail_page)
                    
                    if lines:
                        print(" 【详细信息】:")
                        # === 使用 Markdown 格式拼装企业微信消息 ===
                        msg_chunk = f"**{title_text}**\n"
                        for line in lines:
                            print(f"   {line}")
                            # 用引用语法（>）让作业详情在微信里显得更规整
                            msg_chunk += f"> <font color=\"info\">{line}</font>\n" 
                        summary_messages.append(msg_chunk)
                    else:
                        print(" 未提取到 <p> 内容")
                    
                    print("═" * 50 + "\n")
                    
                    if is_new_tab:
                        print(" 关闭详情页标签...")
                        try:
                            detail_page.close()
                        except:
                            pass
                    else:
                        print(" 返回收件箱...")
                        page.goto(inbox_url)
                        page.wait_for_selector('.notice_title', timeout=5000)
                    
                    time.sleep(1)

        except Exception as e:
            print(f" 出错: {e}")
            summary_messages.append(f"**脚本运行出错:**\n> {e}")

        print(" 所有作业通知提取完毕！")
        browser.close()

    # 如果有抓取到作业通知，则发送企业微信推送
    if summary_messages:
        print(" 正在发送企业微信提醒...")
        # 多条作业之间使用 Markdown 的分割线（---）隔开
        final_push_content = "\n\n---\n\n".join(summary_messages)
        send_wecom_push(
            title=f"【超星作业提醒】共 {len(target_indices)} 个",
            content=final_push_content
        )

if __name__ == "__main__":
    check_chaoxing_homework()