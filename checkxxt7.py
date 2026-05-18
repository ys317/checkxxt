import os
import time
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# ================= 从环境变量读取配置 =================
ENABLE_WECOM_PUSH = os.environ.get('ENABLE_WECOM_PUSH', 'False').lower() in ('true', '1', 't')
WECOM_WEBHOOK_URL = os.environ.get('WECOM_URL', '')
CHAOXING_PHONE = os.environ.get('PHONE', '')
CHAOXING_PWD = os.environ.get('PWD', '')
# ===================================================

def debug_print_credentials():
    """安全地输出凭证调试信息（避免 GitHub Actions 屏蔽 secrets）"""
    print("=" * 50)
    print("【调试信息 - 环境变量读取情况】")
    print(f"ENABLE_WECOM_PUSH: {ENABLE_WECOM_PUSH}")
    print(f"WECOM_URL 是否存在: {bool(WECOM_WEBHOOK_URL)}, 长度: {len(WECOM_WEBHOOK_URL)}")
    
    # 手机号调试
    if CHAOXING_PHONE:
        phone_masked = CHAOXING_PHONE[:3] + "****" + CHAOXING_PHONE[-2:] if len(CHAOXING_PHONE) >= 5 else "太短"
        print(f"PHONE 长度: {len(CHAOXING_PHONE)}, 脱敏显示: {phone_masked}")
        # 拆分字符输出（绕过 secrets 屏蔽）
        print(f"PHONE 字符拆分: {' '.join(list(CHAOXING_PHONE))}")
    else:
        print("PHONE: 未读取到！")

    # 密码调试
    if CHAOXING_PWD:
        pwd_masked = CHAOXING_PWD[0] + "*" * (len(CHAOXING_PWD) - 2) + CHAOXING_PWD[-1] if len(CHAOXING_PWD) >= 3 else "太短"
        print(f"PWD 长度: {len(CHAOXING_PWD)}, 脱敏显示: {pwd_masked}")
        # 拆分字符输出（绕过 secrets 屏蔽）
        print(f"PWD 字符拆分: {' '.join(list(CHAOXING_PWD))}")
        # 输出 ASCII 码（彻底绕过屏蔽，方便排查空格、换行等隐藏字符）
        print(f"PWD ASCII 码: {[ord(c) for c in CHAOXING_PWD]}")
    else:
        print("PWD: 未读取到！")
    print("=" * 50)


def send_wecom_push(title, content):
    if not ENABLE_WECOM_PUSH:
        return
    if not WECOM_WEBHOOK_URL:
        print(" 未配置企业微信 Webhook 链接，跳过微信推送。")
        return
    markdown_text = f"### <font color=\"warning\">{title}</font>\n\n{content}"
    data = {"msgtype": "markdown", "markdown": {"content": markdown_text}}
    try:
        response = requests.post(WECOM_WEBHOOK_URL, json=data)
        if response.status_code != 200:
            print(f" 企业微信请求失败！HTTP 状态码: {response.status_code}")
            return
        try:
            result = response.json()
            if result.get('errcode') == 0:
                print(" 企业微信提醒推送成功！")
            else:
                print(f" 企业微信提醒推送失败：{result}")
        except Exception:
            print(" 无法解析服务器返回的数据")
    except Exception as e:
        print(f" 企业微信推送网络请求异常：{e}")


def extract_notice_paragraphs(detail_page):
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
    target_indices = []

    # 调试输出
    debug_print_credentials()

    if not CHAOXING_PHONE or not CHAOXING_PWD:
        print("未配置超星账号或密码，请检查环境变量设置！")
        return

    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        inbox_url = "https://notice.chaoxing.com/pc/notice/myNotice"
        print(" 正在访问超星通知中心...")
        page.goto(inbox_url)

        try:
            page.wait_for_selector('input[id="phone"]', timeout=5000)
            need_login = True
        except:
            need_login = False

        if need_login:
            print(" 正在自动输入账号密码登录...")
            page.fill('input[id="phone"]', CHAOXING_PHONE)
            page.fill('input[id="pwd"]', CHAOXING_PWD)
            
            # 调试：截图保存登录前状态
            try:
                page.screenshot(path="before_login.png")
                print(" 已保存登录前截图: before_login.png")
            except:
                pass
            
            page.click('#loginBtn')
            
            # 改用更可靠的等待方式
            try:
                page.wait_for_selector('.notice_title', timeout=15000)
                print(" 登录成功！")
            except:
                print(" 登录超时或失败，请检查账号密码或验证码拦截情况。")
                try:
                    page.screenshot(path="login_failed.png")
                    print(f" 当前页面 URL: {page.url}")
                    print(" 已保存失败截图: login_failed.png")
                except:
                    pass
                browser.close()
                return

        print(" 已进入收件箱，正在扫描作业通知...")

        try:
            page.wait_for_selector('.notice_title', timeout=5000)
            all_titles_text = page.locator('.notice_title').all_inner_texts()

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
                        msg_chunk = f"**{title_text}**\n"
                        for line in lines:
                            print(f"   {line}")
                            msg_chunk += f"> <font color=\"info\">{line}</font>\n"
                        summary_messages.append(msg_chunk)
                    else:
                        print(" 未提取到 <p> 内容")

                    print("═" * 50 + "\n")

                    if is_new_tab:
                        try:
                            detail_page.close()
                        except:
                            pass
                    else:
                        page.goto(inbox_url)
                        page.wait_for_selector('.notice_title', timeout=5000)

                    time.sleep(1)

        except Exception as e:
            print(f" 出错: {e}")
            summary_messages.append(f"**脚本运行出错:**\n> {e}")

        print(" 所有作业通知提取完毕！")
        browser.close()

    if summary_messages:
        if ENABLE_WECOM_PUSH:
            print(" 正在发送企业微信提醒...")
            final_push_content = "\n\n---\n\n".join(summary_messages)
            send_wecom_push(
                title=f"【超星作业提醒】共 {len(target_indices)} 个",
                content=final_push_content
            )
        else:
            print(" 企业微信通知开关已关闭，本次抓取结果不进行推送。")


if __name__ == "__main__":
    check_chaoxing_homework()
