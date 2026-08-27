import os
import sys
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from clean_utils import clean_chapter_title, generate_story_markdown
from build_library import build_all_library

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

COOKIE_STR = (
    "XSRF-TOKEN=eyJpdiI6IjVoSUpqa251dGJ6d1FXWGd5emlPR1E9PSIsInZhbHVlIjoib1drWkpMSGxnNE1Fb2dRWHZ2ZkVVNDV4VkF6NzV3aUluWDVYYWJTWmxhcnhObUdLbFNqOHl2Z0ZYL2pPN3BmRnBEMTZHU2xjMTRNbzVwclI5MHUvTnJ6ZXhRU3I5OWR5ZjZPU0VyTHhoT0tTU2txTE9CeVZ3VU1Cdm1rNWNwWGIiLCJtYWMiOiJkZjJkNjJjYThmOWE2ZjA3ODM3YjU0MWMwYjYwODcwYjc3ZGU2Njc0Njg2ODBiMmFiMDQ2MGM0YWZlYjMwZTAxIiwidGFnIjoiIn0%3D; "
    "akaytruyen-session=eyJpdiI6IjloQjJEZW55UFFrSWR0dkdiTVhIRVE9PSIsInZhbHVlIjoiYVZDRHpnYzlEYmdlTGM0UUhPZjFzVDJVRXdXN1pNNVh3OTNCQmRPVGlpR1dVeG8reXlxcm9sL3ovajFvVHUxc2Z0ZFBiY2tBbm9CYVpOZXhpU3d0K2NDeDcrWFpxWEs3TTREcTBtTXI1TFlqMDA1WkljYXgrMGJQRmpQSk5qRlYiLCJtYWMiOiJlMTFlOTlmMWNhZTJlOWRkMTZkYzdhZTE0YTllMTE0MmQ0MDZmNWE1NzAzMGE2MzVlZmUzYzI1NTJhYzk5YTU1IiwidGFnIjoiIn0%3D"
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Cookie': COOKIE_STR,
    'Referer': 'https://akaytruyen.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
}

STORY_URL = 'https://akaytruyen.com/truyen/ngoai-truyen-chua-te-chi-lo'
BASE_URL = 'https://akaytruyen.com'

def fetch_story_meta():
    print(f"[*] Đang lấy thông tin bộ truyện từ: {STORY_URL}")
    resp = requests.get(STORY_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    title = "Ngoại Truyện - Chúa Tể Chi Lộ"
    author = "Akay Hậu"
    category = "Tiên Hiệp, Huyền Huyễn, Trọng Sinh, Hắc Ám"
    desc = "Ngoại truyện độc quyền của siêu phẩm Chúa Tể Chi Lộ. Khắc họa hành trình xưng bá, ma đạo thức tỉnh, tranh đoạt thiên địa của Lạc Nam."
    cover_url = "https://akaytruyen.com/storage/stories/story_1784701732_6a606324e7cdf.png?v=1784701733"

    # Download cover image
    try:
        os.makedirs(os.path.join('web', 'images'), exist_ok=True)
        os.makedirs('images', exist_ok=True)
        cover_resp = requests.get(cover_url, headers=HEADERS, timeout=15)
        if cover_resp.status_code == 200:
            with open(os.path.join('web', 'images', 'ngoai_truyen_chua_te_chi_lo_cover.jpg'), 'wb') as f:
                f.write(cover_resp.content)
            with open(os.path.join('images', 'ngoai_truyen_chua_te_chi_lo_cover.jpg'), 'wb') as f:
                f.write(cover_resp.content)
            print("[+] Đã tải ảnh bìa thành công.")
    except Exception as e:
        print(f"[-] Lỗi tải ảnh bìa: {e}")

    # Extract all chapter links
    unique_chaps = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/ngoai-truyen-chua-te-chi-lo/chuong-' in href:
            if not href.startswith('http'):
                href = BASE_URL + href if href.startswith('/') else BASE_URL + '/' + href
            # Extract chapter number
            m = re.search(r'chuong-(\d+)', href)
            if m:
                c_num = int(m.group(1))
                t = a.text.strip()
                if c_num not in unique_chaps or len(t) > len(unique_chaps[c_num]['raw_title']):
                    unique_chaps[c_num] = {
                        'index': c_num,
                        'url': href,
                        'raw_title': t
                    }

    # Sort chapters 1 -> N
    sorted_chaps = [unique_chaps[k] for k in sorted(unique_chaps.keys())]
    print(f"[+] Tìm thấy tổng cộng {len(sorted_chaps)} chương truyện.")
    return {
        'title': title,
        'author': author,
        'category': category,
        'description': desc,
        'chapters_meta': sorted_chaps
    }

def clean_chapter_body(text: str) -> str:
    if not text:
        return ""
    # Remove hashtag tags at top like #CTCL #akayhau
    text = re.sub(r'^\s*#\w+\s+#\w+\s*', '', text)
    text = re.sub(r'^\s*#\w+\s*', '', text)
    # Remove leading chapter title repetition if present
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
                # Title
                title_tag = soup.find('h2') or soup.find('h1')
                if not title_tag:
                    page_title = soup.find('title')
                    raw_title = page_title.text if page_title else f"Chương {c_idx}"
                else:
                    raw_title = title_tag.text.strip()

                clean_t = clean_chapter_title(raw_title, "Ngoại Truyện - Chúa Tể Chi Lộ")
                if not clean_t or not re.search(r'Chương\s*\d+', clean_t, flags=re.IGNORECASE):
                    clean_t = f"Chương {c_idx}"

                # Content
                content_div = soup.find('div', class_='chapter-content')
                if not content_div:
                    content_div = soup.find('div', id='chapter-content') or soup.find('div', class_='chapter-c')

                if content_div:
                    # Remove script/ads
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
                    return {'index': c_idx, 'title': clean_t, 'content': '', 'error': 'No content div found'}
            elif r.status_code == 403:
                return {'index': c_idx, 'title': f'Chương {c_idx}', 'content': '', 'error': '403 Forbidden (VIP Required)'}
            time.sleep(1)
        except Exception as e:
            if retry == 2:
                return {'index': c_idx, 'title': f'Chương {c_idx}', 'content': '', 'error': str(e)}
            time.sleep(1)

def run_crawler():
    meta = fetch_story_meta()
    chaps_meta = meta['chapters_meta']
    
    print("\n" + "="*50)
    print(f" BẮT ĐẦU CRAWL {len(chaps_meta)} CHƯƠNG VIP TỪ AKAY TRUYỆN")
    print("="*50)

    results = {}
    session = requests.Session()

    # Use multi-threading to speed up crawling safely
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_single_chapter, item, session): item for item in chaps_meta}
        for fut in as_completed(futures):
            res = fut.result()
            idx = res['index']
            results[idx] = res
            status = "OK" if res.get('content') else f"LỖI ({res.get('error')})"
            words = len(res.get('content', '').split())
            print(f"[{idx:02d}/{len(chaps_meta):02d}] {res['title']} -> {status} ({words:,} từ)")

    # Sort results
    sorted_chapters = [results[k] for k in sorted(results.keys())]

    # Save JSON dataset
    json_path = 'ngoai_truyen_chua_te_chi_lo.json'
    story_data = {
        'title': meta['title'],
        'author': meta['author'],
        'category': meta['category'],
        'description': meta['description'],
        'cover_image': 'images/ngoai_truyen_chua_te_chi_lo_cover.jpg',
        'chapters': sorted_chapters
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(story_data, f, ensure_ascii=False, indent=2)
    print(f"\n[+] Đã lưu toàn bộ dữ liệu vào: {json_path}")

    # Generate complete Markdown file
    md_path = 'ngoai_truyen_chua_te_chi_lo.md'
    md_content = generate_story_markdown(meta['title'], sorted_chapters)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"[+] Đã tạo file Markdown đọc offline: {md_path}")

    # Update web library
    print("\n[*] Đang tích hợp bộ truyện vào Thư Viện Web Reader...")
    build_all_library()
    print("\n" + "="*50)
    print(" HOÀN TẤT CÀO DỮ LIỆU & ĐỒNG BỘ THƯ VIỆN WEB THÀNH CÔNG!")
    print("="*50)

if __name__ == '__main__':
    run_crawler()
