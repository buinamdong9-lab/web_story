#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebStory Turbo Crawler Engine (AsyncIO + aiohttp)
Extreme High-Throughput Web Scraping & Multi-Story Concurrent Partitioning:
- 50-100 concurrent HTTP streams with Keep-Alive & DNS Cache
- Concurrent Multi-Story Pipeline (10 stories downloaded in parallel)
- Rapid Parallel Category Pagination Scanning
- In-Memory Text Sanitization & Minified JSON Writer
- Checkpoint Recovery & Resumable Tasks
"""

import os
import sys
import re
import json
import time
import asyncio
import unicodedata
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup

# Ensure UTF-8 Output on Windows Shell
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://truyenc.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://truyenc.com/'
}

CHECKPOINT_FILE = 'crawler_checkpoint.json'
STORIES_DIR = os.path.join('data', 'stories')
MAX_CONCURRENT_STORIES = 8
MAX_CONCURRENT_CHAPTERS = 40


def slugify(text):
    if not text:
        return 'unnamed'
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text) or 'unnamed'


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'completed_stories': [], 'in_progress': {}}


def save_checkpoint(cp):
    try:
        with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
            json.dump(cp, f, ensure_ascii=False, indent=2)
    except Exception as e:
        pass


def clean_story_text(html_or_text):
    if not html_or_text:
        return ""
    soup = BeautifulSoup(html_or_text, 'html.parser')
    for tag in soup.find_all(['script', 'style', 'iframe', 'ins', 'button', 'input', 'noscript']):
        tag.decompose()
    for br in soup.find_all('br'):
        br.replace_with('\n')
    for p in soup.find_all('p'):
        p.append('\n\n')
    text = soup.get_text()
    
    lines = []
    watermark_patterns = [
        r'truyenc\.com', r'đọc truyện tại', r'nguồn truyện',
        r'chúc bạn đọc truyện vui vẻ', r'ủng hộ tác giả', r'chia sẻ truyện'
    ]
    for line in text.split('\n'):
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
        if any(re.search(pat, cleaned_line, re.IGNORECASE) for pat in watermark_patterns):
            if len(cleaned_line) < 80:
                continue
        lines.append(cleaned_line)
    return '\n\n'.join(lines)


def get_story_id_from_url(url):
    path = urlparse(url).path.strip('/')
    parts = path.split('/')
    if len(parts) >= 2:
        return parts[1]
    return slugify(path)


async def fetch_url(session, url, retries=3):
    for attempt in range(retries):
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as res:
                if res.status == 200:
                    return await res.text()
        except Exception:
            await asyncio.sleep(0.2 * (attempt + 1))
    return None


async def download_image(session, img_url, dest_path):
    if not img_url or os.path.exists(dest_path):
        return
    try:
        if img_url.startswith('/'):
            img_url = urljoin(BASE_URL, img_url)
        async with session.get(img_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=12)) as res:
            if res.status == 200:
                content = await res.read()
                if len(content) > 1000:
                    with open(dest_path, 'wb') as f:
                        f.write(content)
    except Exception:
        pass


async def fetch_chapter(session, chap_info, chaps_dest_dir, sem):
    idx = chap_info['index']
    chap_file = os.path.join(chaps_dest_dir, f"{idx}.json")
    
    if os.path.exists(chap_file):
        try:
            with open(chap_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return idx, chap_info['title'], data.get('word_count', 0)
        except Exception:
            pass
            
    async with sem:
        html = await fetch_url(session, chap_info['url'])
        
    content = ""
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        content_el = soup.find('div', class_='story-content') or \
                     soup.find('div', class_='content') or \
                     soup.find('div', class_='page-content') or \
                     soup.find('article') or soup.find('body')
        if content_el:
            content = clean_story_text(str(content_el))
            
    if not content:
        content = f"Nội dung chương {idx} đang được cập nhật."
        
    word_count = len(content.split())
    payload = {
        'index': idx,
        'title': chap_info['title'],
        'word_count': word_count,
        'content': content
    }
    with open(chap_file, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))
        
    return idx, chap_info['title'], word_count


async def crawl_single_story(session, story_url, checkpoint, default_category, story_sem, chap_sem):
    async with story_sem:
        story_id = get_story_id_from_url(story_url)
        story_dest_dir = os.path.join(STORIES_DIR, story_id)
        chaps_dest_dir = os.path.join(story_dest_dir, 'chapters')
        toc_file = os.path.join(story_dest_dir, 'toc.json')
        
        # Check if already completed
        if story_url in checkpoint['completed_stories'] and os.path.exists(toc_file):
            return True
            
        html = await fetch_url(session, story_url)
        if not html:
            return False
            
        soup = BeautifulSoup(html, 'html.parser')
        h1 = soup.find('h1')
        title = h1.get_text(strip=True) if h1 else 'Truyện Không Tên'
        
        author = 'Đang cập nhật'
        category = default_category
        description = 'Bộ truyện đặc sắc được tổng hợp từ TruyenC.'
        
        for div in soup.find_all(['div', 'p', 'span']):
            t = div.get_text(strip=True)
            if 'Tác giả:' in t:
                extracted = t.replace('Tác giả:', '').strip()
                if len(extracted) < 40:
                    author = extracted
            elif 'Thể loại:' in t:
                extracted = t.replace('Thể loại:', '').strip()
                if len(extracted) < 60:
                    category = extracted
                    
        if len(author) > 50 or 'Truyện' in author:
            author = 'Nhiều Tác Giả'
            
        desc_el = soup.find('div', class_='story-desc') or soup.find('div', class_='desc') or soup.find('div', class_='description')
        if desc_el:
            desc_text = desc_el.get_text(strip=True)
            if len(desc_text) > 10:
                description = desc_text
                
        # Cover image
        cover_img_url = None
        img_el = soup.find('img', class_='story-cover') or (soup.find('div', class_='cover').find('img') if soup.find('div', class_='cover') else None)
        if not img_el:
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or ''
                if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']) and 'avatar' not in src:
                    img_el = img
                    break
        if img_el:
            cover_img_url = img_el.get('src') or img_el.get('data-src')
            
        # Chapter links
        chap_links = []
        seen_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if ('/chuong-' in href or '/chap-' in href) and href not in seen_links:
                full_url = urljoin(BASE_URL, href)
                chap_title = a.get_text(strip=True) or f"Chương {len(chap_links) + 1}"
                chap_links.append({'index': len(chap_links) + 1, 'title': chap_title, 'url': full_url})
                seen_links.add(href)
                
        if not chap_links:
            chap_links.append({'index': 1, 'title': title, 'url': story_url})
            
        os.makedirs(chaps_dest_dir, exist_ok=True)
        local_cover_path = os.path.join(story_dest_dir, 'cover.jpg')
        if cover_img_url:
            asyncio.create_task(download_image(session, cover_img_url, local_cover_path))
            
        # Parallel chapter download
        tasks = [fetch_chapter(session, chap, chaps_dest_dir, chap_sem) for chap in chap_links]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        toc_entries = []
        total_words = 0
        for r in results:
            if isinstance(r, tuple):
                idx, ch_title, w_count = r
                total_words += w_count
                toc_entries.append({'index': idx, 'title': ch_title, 'word_count': w_count})
                
        toc_entries.sort(key=lambda x: x['index'])
        
        toc_payload = {
            'id': story_id,
            'title': title,
            'author': author,
            'category': category,
            'status': 'Hoàn Thành',
            'total_chapters': len(toc_entries),
            'total_words': total_words,
            'description': description,
            'source_url': story_url,
            'cover_image': f"images/{story_id}_cover.jpg" if os.path.exists(local_cover_path) else "images/cover.jpg",
            'chapters': toc_entries
        }
        with open(toc_file, 'w', encoding='utf-8') as f:
            json.dump(toc_payload, f, ensure_ascii=False, indent=2)
            
        if story_url not in checkpoint['completed_stories']:
            checkpoint['completed_stories'].append(story_url)
            
        print(f"[TURBO FETCHED] '{title}' ({len(toc_entries)} chaps, {total_words:,} words)")
        return True


async def scan_category_pages(session, category_path, max_pages=None):
    cat_url = urljoin(BASE_URL, category_path)
    print(f"\n[TURBO SCAN] Discovering all catalogue pages for {cat_url}...")
    
    # 1. Fetch first page to find total pages
    html = await fetch_url(session, cat_url)
    if not html:
        return []
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find last page number
    max_page_num = 1
    for a in soup.find_all('a', href=True):
        m = re.search(r'page=(\d+)', a['href'])
        if m:
            max_page_num = max(max_page_num, int(m.group(1)))
            
    if max_pages:
        max_page_num = min(max_page_num, max_pages)
        
    print(f"-> Detected {max_page_num} pages in category {category_path}. Scanning in parallel...")
    
    page_urls = [f"{cat_url}?page={p}" if p > 1 else cat_url for p in range(1, max_page_num + 1)]
    
    async def get_page_stories(p_url):
        p_html = await fetch_url(session, p_url)
        if not p_html:
            return []
        p_soup = BeautifulSoup(p_html, 'html.parser')
        urls = []
        for a in p_soup.find_all('a', href=True):
            h = a['href']
            if '/truyen/' in h and not '/chuong-' in h and not '/chap-' in h:
                urls.append(urljoin(BASE_URL, h))
        return urls

    page_tasks = [get_page_stories(u) for u in page_urls]
    page_results = await asyncio.gather(*page_tasks)
    
    all_story_urls = []
    seen = set()
    for res_list in page_results:
        for u in res_list:
            if u not in seen and u != cat_url:
                seen.add(u)
                all_story_urls.append(u)
                
    print(f"-> Discovered total {len(all_story_urls)} unique stories across {max_page_num} pages in seconds!")
    return all_story_urls


async def run_turbo_crawler(categories_to_crawl, limit_pages=None, limit_stories=None):
    checkpoint = load_checkpoint()
    
    connector = aiohttp.TCPConnector(limit=100, limit_per_host=50, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        story_sem = asyncio.Semaphore(MAX_CONCURRENT_STORIES)
        chap_sem = asyncio.Semaphore(MAX_CONCURRENT_CHAPTERS)
        
        for c_slug, c_path, c_name in categories_to_crawl:
            print(f"\n==================================================")
            print(f" STARTING TURBO PIPELINE: {c_name}")
            print(f"==================================================")
            
            story_urls = await scan_category_pages(session, c_path, max_pages=limit_pages)
            if limit_stories:
                story_urls = story_urls[:limit_stories]
                
            print(f"\n[RUNNING] Crawling {len(story_urls)} stories in parallel (8 stories simultaneously, 40 concurrent chapter streams)...")
            
            # Execute stories in chunks of 20 with auto checkpoint save
            chunk_size = 20
            for i in range(0, len(story_urls), chunk_size):
                chunk = story_urls[i:i+chunk_size]
                story_tasks = [crawl_single_story(session, url, checkpoint, c_name, story_sem, chap_sem) for url in chunk]
                await asyncio.gather(*story_tasks)
                
                # Flush checkpoint and trigger incremental build
                save_checkpoint(checkpoint)
                print(f"\n[CHECKPOINT SAVED] Completed chunk {min(i+chunk_size, len(story_urls))}/{len(story_urls)} stories. Syncing library...")
                os.system("python build_library.py")
                
    print("\n==================================================")
    print(" ALL CATEGORIES CRAWLED AT TURBO SPEED!")
    print("==================================================")


def main():
    categories = [
        ('18', '/tim-truyen-18', 'Truyện 18+, Ngôn Tình'),
        ('cuoi', '/tim-truyen-cuoi', 'Truyện Cười, Hài Hước'),
        ('audio', '/tim-truyen-audio', 'Truyện Audio, Đêm Khuya'),
        ('ma', '/tim-truyen-ma', 'Truyện Ma, Kinh Dị')
    ]
    
    print("==================================================")
    print("      WEB STORY TURBO ASYNC CRAWLER ENGINE        ")
    print("==================================================")
    
    asyncio.run(run_turbo_crawler(categories))


if __name__ == '__main__':
    main()
