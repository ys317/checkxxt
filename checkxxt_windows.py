import time
import re
import requests
from datetime import datetime, date, timedelta
from playwright.sync_api import sync_playwright

WECOM_WEBHOOK_URL = ''   #例如https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=3d23432rf格式
CHAOXING_PHONE = ''
CHAOXING_PWD = ''


def send_wecom_push(content):
    if not WECOM_WEBHOOK_URL or 'YOUR_KEY_HERE' in WECOM_WEBHOOK_URL:
        return
    data = {"msgtype": "markdown", "markdown": {"content": content}}
    try:
        r = requests.post(WECOM_WEBHOOK_URL, json=data, timeout=10)
        if r.status_code == 200 and r.json().get('errcode') == 0:
            print("  企业微信提醒推送成功！")
        else:
            print(f"  推送失败: {r.text[:100]}")
    except Exception as e:
        print(f"  推送异常: {e}")


def parse_datetime(s):
    if not s: return None
    m = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日\s]+(\d{1,2}):(\d{2})', s)
    if m: return datetime(*[int(x) for x in m.groups()])
    return None


def fmt_remain(dl):
    if not dl: return ""
    d = dl - datetime.now()
    if d.total_seconds() < 0: return "已截止"
    if d.days == 0: return f"今天截止（{int(d.total_seconds()//3600)}小时后）"
    if d.days == 1: return "明天截止"
    return f"还剩{d.days}天"


def get_urgency(dl):
    if not dl: return "info"
    days = (dl.date() - date.today()).days
    return "warning" if days <= 3 else "info"


def check_chaoxing_homework():
    inbox_url = "https://notice.chaoxing.com/pc/notice/myNotice"
    detail_base = "https://notice.chaoxing.com/res/pc/mobileHtml/html/noticeDetail.html?noticeId="

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page()

        print("登录超星...")
        page.goto(inbox_url)
        try:
            page.wait_for_selector('input[id="phone"]', timeout=3000)
            page.fill('input[id="phone"]', CHAOXING_PHONE)
            page.fill('input[id="pwd"]', CHAOXING_PWD)
            page.click('#loginBtn')
            time.sleep(4)
        except:
            pass

        print("加载收件箱...")
        page.wait_for_selector('ul.item', timeout=10000)
        time.sleep(2)
        items = page.locator('ul.item > li.flex-row')
        count = items.count()
        print(f"共 {count} 条消息")

        # ---- 第一步：提取所有 noticeId 和标题 ----
        notice_data = page.evaluate("""
            () => {
                const items = document.querySelectorAll('ul.item > li.flex-row');
                return Array.from(items).map((el, i) => {
                    const h3 = el.querySelector('h3');
                    const text = h3 ? h3.textContent.trim() : el.textContent.trim();
                    // 直接触发 Vue 路由点击
                    return { index: i, text };
                });
            }
        """)
        print(f"提取到 {len(notice_data)} 项")

        # 分类
        dl_items = [(i, d) for i, d in enumerate(notice_data) if "结束提醒" in d['text']]
        hw_items = [(i, d) for i, d in enumerate(notice_data) 
                    if "作业" in d['text'] and "结束提醒" not in d['text'] and "消息" not in d['text']]
        print(f"截止提醒 {len(dl_items)} 条，作业 {len(hw_items)} 条\n")

        results = []

        # ---- 第二步：逐个点击提取 ----
        for idx, item_data in dl_items + hw_items[:10]:
            try:
                title = item_data['text']
                is_dl = idx in [x[0] for x in dl_items]
                label = "截止" if is_dl else "作业"
                print(f"  [{label}] {title[:50]}...")

                # 点击列表项触发 Vue 路由
                loc = page.locator('ul.item > li.flex-row').nth(idx)
                loc.click()
                time.sleep(2.5)

                # 等待跳转到详情页
                try:
                    page.wait_for_url('**/noticeDetail**', timeout=8000)
                except:
                    pass

                time.sleep(1)
                body = page.locator('body').inner_text()

                # 解析
                course = hwname = ""
                start_dt = end_dt = None
                
                m = re.search(r'课程[：:]\s*(.+)', body, re.M)
                if m: course = m.group(1).strip()
                m = re.search(r'作业[名称]*[：:]\s*(.+)', body, re.M)
                if m: hwname = m.group(1).strip()
                m = re.search(r'开始时间[：:]\s*([^\n]+)', body)
                if m: start_dt = parse_datetime(m.group(1))
                m = re.search(r'结束时间[：:]\s*([^\n]+)', body)
                if m: end_dt = parse_datetime(m.group(1))

                # 对于截止提醒：用通知时间推算
                if is_dl and not end_dt:
                    notif_m = re.search(r'(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})', body)
                    if notif_m:
                        try:
                            notif_time = datetime(date.today().year, 
                                int(notif_m.group(1)), int(notif_m.group(2)),
                                int(notif_m.group(3)), int(notif_m.group(4)))
                            now = datetime.now()
                            if (now - notif_time).total_seconds() > 24 * 3600:
                                print(f"    通知已过时（{notif_time.strftime('%m月%d日 %H:%M')}发出），跳过")
                                page.goto(inbox_url)
                                time.sleep(2)
                                page.wait_for_selector('ul.item', timeout=8000)
                                time.sleep(1)
                                continue
                            end_dt = notif_time + timedelta(hours=24)
                            print(f"    有效截止提醒，预计截止: {end_dt.strftime('%m月%d日 %H:%M')}")
                        except:
                            pass

                if end_dt:
                    results.append(("deadline" if is_dl else "homework", end_dt, course, hwname, start_dt))
                    print(f"    截止: {end_dt.strftime('%m月%d日 %H:%M')} {fmt_remain(end_dt)}")
                elif course or hwname:
                    results.append(("deadline" if is_dl else "homework", None, course, hwname, start_dt))
                    print(f"    未找到截止时间")

                # 返回收件箱
                page.goto(inbox_url)
                time.sleep(2)
                page.wait_for_selector('ul.item', timeout=8000)
                time.sleep(1)

            except Exception as e:
                print(f"    异常: {e}")
                try:
                    page.goto(inbox_url)
                    time.sleep(2)
                    page.wait_for_selector('ul.item', timeout=8000)
                    time.sleep(1)
                except:
                    pass
                continue

        browser.close()

    # ---- 组装推送 ----
    push = []
    far = datetime(9999, 12, 31)

    for ttype, label in [("deadline", "作业即将截止"), ("homework", "作业列表")]:
        items = [(e, c, n, s) for (tt, e, c, n, s) in results if tt == ttype]
        if not items: continue
        items.sort(key=lambda x: x[0] or far)

        push.append(f"##  {label}（{len(items)}项）\n")
        for i, (dl, c, n, sd) in enumerate(items, 1):
            color = get_urgency(dl)
            push.append(f"**{i}. <font color=\"{color}\">{c} - {n}</font>**")
            if sd: push.append(f"> 开始：{sd.strftime('%m月%d日 %H:%M')}")
            if dl: push.append(f"> 截止：{dl.strftime('%m月%d日 %H:%M')}（{fmt_remain(dl)}）")
            push.append("")

    if push:
        msg = f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n" + "\n".join(push).strip()
        print("\n发送企业微信...")
        send_wecom_push(msg)
    else:
        print("\n无作业通知")


if __name__ == "__main__":
    check_chaoxing_homework()
