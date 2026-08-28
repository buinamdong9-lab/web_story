import os
import sys
import time
import json
import socket
import datetime
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from clean_utils import clean_chapter_title, generate_story_markdown
from build_library import build_all_library

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# CẤU HÌNH CRAWLER TỰ ĐỘNG & TỐI ƯU HÓA
# ==========================================
INTERVAL_HOURS = 6               # Tần suất kiểm tra (mỗi 6 tiếng)
RETRY_NETWORK_MINUTES = 2        # Thời gian thử lại nếu mất kết nối Internet (phút)
LOG_FILE = "auto_crawler.log"    # File lưu lịch sử hoạt động
MAX_LOG_BYTES = 5 * 1024 * 1024  # Giới hạn kích thước log (5MB)

DEFAULT_COOKIE = (
    "XSRF-TOKEN=eyJpdiI6IjVoSUpqa251dGJ6d1FXWGd5emlPR1E9PSIsInZhbHVlIjoib1drWkpMSGxnNE1Fb2dRWHZ2ZkVVNDV4VkF6NzV3aUluWDVYYWJTWmxhcnhObUdLbFNqOHl2Z0ZYL2pPN3BmRnBEMTZHU2xjMTRNbzVwclI5MHUvTnJ6ZXhRU3I5OWR5ZjZPU0VyTHhoT0tTU2txTE9CeVZ3VU1Cdm1rNWNwWGIiLCJtYWMiOiJkZjJkNjJjYThmOWE2ZjA3ODM3YjU0MWMwYjYwODcwYjc3ZGU2Njc0Njg2ODBiMmFiMDQ2MGM0YWZlYjMwZTAxIiwidGFnIjoiIn0%3D; "
    "akaytruyen-session=eyJpdiI6IjloQjJEZW55UFFrSWR0dkdiTVhIRVE9PSIsInZhbHVlIjoiYVZDRHpnYzlEYmdlTGM0UUhPZjFzVDJVRXdXN1pNNVh3OTNCQmRPVGlpR1dVeG8reXlxcm9sL3ovajFvVHUxc2Z0ZFBiY2tBbm9CYVpOZXhpU3d0K2NDeDcrWFpxWEs3TTREcTBtTXI1TFlqMDA1WkljYXgrMGJQRmpQSk5qRlYiLCJtYWMiOiJlMTFlOTlmMWNhZTJlOWRkMTZkYzdhZTE0YTllMTE0MmQ0MDZmNWE1NzAzMGE2MzVlZmUzYzI1NTJhYzk5YTU1IiwidGFnIjoiIn0%3D"
)
COOKIE_STR = os.environ.get('AKAY_COOKIE') or DEFAULT_COOKIE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Cookie': COOKIE_STR,
    'Referer': 'https://akaytruyen.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
}

STORY_URL = 'https://akaytruyen.com/truyen/ngoai-truyen-chua-te-chi-lo'
JSON_FILE = 'ngoai_truyen_chua_te_chi_lo.json'
MD_FILE = 'ngoai_truyen_chua_te_chi_lo.md'

def get_optimized_session():
    """Tạo HTTP Session tối ưu với connection pool và tự động thử lại khi mạng chập chờn"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{now}] {msg}"
    print(formatted)
    try:
        # Giới hạn kích thước file log tự động
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_BYTES:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                f.writelines(lines[-2000:])
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def is_internet_available():
    """Kiểm tra máy tính có đang kết nối internet hay không"""
    test_hosts = [("8.8.8.8", 53), ("1.1.1.1", 53), ("akaytruyen.com", 443)]
    for host, port in test_hosts:
        try:
            socket.setdefaulttimeout(3)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                return True
        except Exception:
            continue
    return False

def clean_chapter_body(text: str) -> str:
    if not text:
        return ""
    import re
    text = re.sub(r'^\s*#\w+\s+#\w+\s*', '', text)
    text = re.sub(r'^\s*#\w+\s*', '', text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned_lines = []
    for line in lines:
        if re.search(r'^(?:CHƯƠNG|Chương)\s*\d+[:\s]', line, flags=re.IGNORECASE):
            continue
        cleaned_lines.append(line)
    return '\n\n'.join(cleaned_lines)

def fetch_single_chapter(item, session):
    c_idx = item['index']
    url = item['url']
    for retry in range(3):
        try:
            r = session.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                title_tag = soup.find('h2') or soup.find('h1')
                if not title_tag:
                    page_title = soup.find('title')
                    raw_title = page_title.text if page_title else f"Chương {c_idx}"
                else:
                    raw_title = title_tag.text.strip()

                import re
                clean_t = clean_chapter_title(raw_title, "Ngoại Truyện - Chúa Tể Chi Lộ")
                if not clean_t or not re.search(r'Chương\s*\d+', clean_t, flags=re.IGNORECASE):
                    clean_t = f"Chương {c_idx}"

                content_div = soup.find('div', class_='chapter-content')
                if not content_div:
                    content_div = soup.find('div', id='chapter-content') or soup.find('div', class_='chapter-c')

                if content_div:
                    for s in content_div(['script', 'style', 'iframe', 'button']):
                        s.decompose()
                    raw_content = content_div.get_text('\n')
                    clean_content = clean_chapter_body(raw_content)
                    return {
                        'index': c_idx,
                        'title': clean_t,
                        'content': clean_content,
                        'url': url
                    }
                else:
                    return {'index': c_idx, 'title': clean_t, 'content': '', 'error': 'Không tìm thấy nội dung'}
            time.sleep(1)
        except Exception as e:
            if retry == 2:
                return {'index': c_idx, 'title': f'Chương {c_idx}', 'content': '', 'error': str(e)}
            time.sleep(1)

def check_and_update_story():
    """Kiểm tra chương mới và chỉ tải các chương chưa có (Incremental Update)"""
    log("▶ Đang kết nối tới Akay Truyện để kiểm tra chương mới...")
    
    # 1. Đọc dữ liệu hiện có
    existing_story = {}
    existing_chapters = {}
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                existing_story = json.load(f)
                for chap in existing_story.get('chapters', []):
                    existing_chapters[chap['index']] = chap
        except Exception as e:
            log(f"Lỗi đọc {JSON_FILE}: {e}")

    # 2. Lấy danh sách chương mới nhất trên website
    try:
        resp = requests.get(STORY_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        log(f"[-] Không thể truy cập trang truyện: {e}")
        return False

    soup = BeautifulSoup(resp.text, 'html.parser')
    import re
    unique_web_chaps = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/ngoai-truyen-chua-te-chi-lo/chuong-' in href:
            if not href.startswith('http'):
                href = 'https://akaytruyen.com' + (href if href.startswith('/') else '/' + href)
            m = re.search(r'chuong-(\d+)', href)
            if m:
                c_num = int(m.group(1))
                t = a.text.strip()
                if c_num not in unique_web_chaps or len(t) > len(unique_web_chaps[c_num]['raw_title']):
                    unique_web_chaps[c_num] = {
                        'index': c_num,
                        'url': href,
                        'raw_title': t
                    }

    total_web_chaps = len(unique_web_chaps)
    log(f"[*] Trang web hiện có: {total_web_chaps} chương. Máy tính hiện có: {len(existing_chapters)} chương.")

    # 3. Tìm các chương còn thiếu
    missing_chaps = [meta for idx, meta in sorted(unique_web_chaps.items()) if idx not in existing_chapters or not existing_chapters[idx].get('content')]

    if not missing_chaps:
        log("✔ Dữ liệu đã là mới nhất! Không có chương mới cần tải.")
        return True

    log(f"⚡ Phát hiện {len(missing_chaps)} chương mới cần tải: {[m['index'] for m in missing_chaps]}")

    # 4. Tải các chương mới
    session = get_optimized_session()
    newly_fetched = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_single_chapter, item, session): item for item in missing_chaps}
        for fut in as_completed(futures):
            res = fut.result()
            idx = res['index']
            newly_fetched[idx] = res
            status = "OK" if res.get('content') else f"LỖI ({res.get('error')})"
            words = len(res.get('content', '').split())
            log(f"  + [Chương {idx:02d}] {res['title']} -> {status} ({words:,} từ)")

    # 5. Hợp nhất vào bộ nhớ
    for idx, chap in newly_fetched.items():
        existing_chapters[idx] = chap

    all_sorted_chapters = [existing_chapters[k] for k in sorted(existing_chapters.keys())]

    # 6. Ghi đè an toàn file JSON (Atomic Write) & Markdown
    story_data = {
        'title': existing_story.get('title', 'Ngoại Truyện - Chúa Tể Chi Lộ'),
        'author': existing_story.get('author', 'Akay Hậu'),
        'category': existing_story.get('category', 'Tiên Hiệp, Huyền Huyễn, Trọng Sinh, Hắc Ám'),
        'description': existing_story.get('description', 'Ngoại truyện độc quyền của siêu phẩm Chúa Tể Chi Lộ.'),
        'cover_image': 'images/ngoai_truyen_chua_te_chi_lo_cover.jpg',
        'chapters': all_sorted_chapters
    }

    temp_json = JSON_FILE + ".tmp"
    with open(temp_json, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    if os.path.exists(JSON_FILE):
        os.replace(temp_json, JSON_FILE)
    else:
        os.rename(temp_json, JSON_FILE)

    md_content = generate_story_markdown(story_data['title'], all_sorted_chapters)
    temp_md = MD_FILE + ".tmp"
    with open(temp_md, 'w', encoding='utf-8') as f:
        f.write(md_content)
    if os.path.exists(MD_FILE):
        os.replace(temp_md, MD_FILE)
    else:
        os.rename(temp_md, MD_FILE)

    # 7. Đồng bộ Thư Viện Web
    log("[*] Đang cập nhật Thư Viện Web...")
    build_all_library()
    log(f"🎉 Cập nhật thành công! Tổng cộng hiện có {len(all_sorted_chapters)} chương.")

    # 8. Tự động Push lên GitHub
    latest_chap_idx = all_sorted_chapters[-1]['index'] if all_sorted_chapters else total_web_chaps
    push_to_github(f"Auto-update: Ngoại Truyện - Chúa Tể Chi Lộ (Chương {latest_chap_idx})")
    return True

def push_to_github(commit_msg="Auto update story chapters"):
    """Tự động commit và push các chương truyện mới lên GitHub"""
    try:
        import subprocess
        log("🚀 Đang tự động đồng bộ và đẩy thay đổi lên GitHub...")
        subprocess.run(["git", "add", "-A"], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            log("✔ Kho Git đã đồng bộ, không có thay đổi mới cần push.")
            return True
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
        if res.returncode == 0:
            log("🎉 Đã đẩy dữ liệu mới lên GitHub thành công!")
            return True
        else:
            log(f"[-] Lỗi git push: {res.stderr or res.stdout}")
            return False
    except Exception as e:
        log(f"[-] Lỗi khi đồng bộ GitHub: {e}")
        return False

def main_loop():
    log("="*60)
    log(f" KHỞI ĐỘNG AUTO-CRAWLER (Kiểm tra mỗi {INTERVAL_HOURS} tiếng)")
    log("="*60)

    while True:
        try:
            if is_internet_available():
                check_and_update_story()
                log(f"💤 Đang ngủ trong {INTERVAL_HOURS} tiếng trước lần kiểm tra tiếp theo...")
                sleep_seconds = INTERVAL_HOURS * 3600
            else:
                log(f"⚠ Chưa có kết nối Internet. Sẽ thử lại sau {RETRY_NETWORK_MINUTES} phút...")
                sleep_seconds = RETRY_NETWORK_MINUTES * 60

            # Ngủ ngắt quãng để phản hồi mượt mà
            for _ in range(int(sleep_seconds // 5)):
                time.sleep(5)

        except KeyboardInterrupt:
            log("🛑 Đã dừng Auto-Crawler bởi người dùng.")
            break
        except Exception as e:
            log(f"[ERROR] Ngoại lệ không mong muốn: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main_loop()
