#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Performance Resumable Multi-Threaded Crawler for TruyenC.com
Features:
- Partitioned Data Storage (data/stories/{story_id}/)
- Text Sanitization & Minified JSON Payloads
- Checkpointing & Resume on Interruption
- Multi-threaded Chapter Fetching with Jitter Delay
- Automatic Incremental Library Sync (every 10 stories)
"""

import os
import sys
import re
import json
import time
import random
import argparse
import unicodedata
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
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


def slugify(text):
    """Generate safe ASCII folder/file names from Vietnamese strings."""
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
        print(f"[WARN] Could not save checkpoint: {e}")


def clean_story_text(html_or_text):
    """Sanitize and clean raw chapter text for clean reading and AI audio synthesis."""
    if not html_or_text:
        return ""
    
    soup = BeautifulSoup(html_or_text, 'html.parser')
    
    # Remove unwanted DOM nodes
    for tag in soup.find_all(['script', 'style', 'iframe', 'ins', 'button', 'input', 'noscript']):
        tag.decompose()
        
    # Replace <br> and </p> with linebreaks
    for br in soup.find_all('br'):
        br.replace_with('\n')
    for p in soup.find_all('p'):
        p.append('\n\n')
        
    text = soup.get_text()
    
    lines = []
    watermark_patterns = [
        r'truyenc\.com',
        r'đọc truyện tại',
        r'nguồn truyện',
        r'chúc bạn đọc truyện vui vẻ',
        r'ủng hộ tác giả',
        r'chia sẻ truyện'
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
    """Extract clean unique story identifier from URL."""
    path = urlparse(url).path.strip('/')
    parts = path.split('/')
    if len(parts) >= 2:
        return parts[1]
    return slugify(path)


def download_cover_image(img_url, dest_path):
    """Download and save story cover image locally."""
    if not img_url:
        return None
    try:
        if img_url.startswith('/'):
            img_url = urljoin(BASE_URL, img_url)
        res = requests.get(img_url, headers=HEADERS, timeout=12)
        if res.status_code == 200 and len(res.content) > 1000:
            with open(dest_path, 'wb') as f:
                f.write(res.content)
            return dest_path
    except Exception as e:
        pass
    return None


def fetch_chapter_content(chap_url):
    """Fetch single chapter text content with retry."""
    for attempt in range(3):
        try:
            res = requests.get(chap_url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                content_el = soup.find('div', class_='story-content') or \
                             soup.find('div', class_='content') or \
                             soup.find('div', class_='page-content')
                             
                if content_el:
                    return clean_story_text(str(content_el))
                    
                body = soup.find('article') or soup.find('body')
                if body:
                    return clean_story_text(str(body))
        except Exception:
            time.sleep(0.8 + attempt)
    return None


def crawl_story(story_url, checkpoint, default_category='Truyện Hay'):
    """Crawl full story metadata, TOC, and all chapters."""
    print(f"\n==================================================")
    print(f"[CRAWL STORY] {story_url}")
    print(f"==================================================")
    
    try:
        res = requests.get(story_url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"[ERROR] HTTP {res.status_code} fetching story page.")
            return False
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. Parse Metadata
        h1 = soup.find('h1')
        title = h1.get_text(strip=True) if h1 else 'Truyện Không Tên'
        story_id = get_story_id_from_url(story_url)
        
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
                    
        # Clean author if it contains junk
        if len(author) > 50 or 'Truyện' in author:
            author = 'Nhiều Tác Giả'
                
        # Description
        desc_el = soup.find('div', class_='story-desc') or \
                  soup.find('div', class_='desc') or \
                  soup.find('div', class_='description')
        if desc_el:
            desc_text = desc_el.get_text(strip=True)
            if len(desc_text) > 10:
                description = desc_text
            
        # Cover Image URL
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
            
        # 2. Extract Chapters TOC
        chap_links = []
        seen_links = set()
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if ('/chuong-' in href or '/chap-' in href) and href not in seen_links:
                full_url = urljoin(BASE_URL, href)
                chap_title = a.get_text(strip=True) or f"Chương {len(chap_links) + 1}"
                chap_links.append({
                    'index': len(chap_links) + 1,
                    'title': chap_title,
                    'url': full_url
                })
                seen_links.add(href)
                
        if not chap_links:
            # Single-chapter story / one-shot
            chap_links.append({
                'index': 1,
                'title': title,
                'url': story_url
            })
            
        print(f"-> Title: {title}")
        print(f"-> Author: {author} | Category: {category}")
        print(f"-> Total Chapters: {len(chap_links)}")
        
        # 3. Setup Partitioned Directory Structure
        story_dest_dir = os.path.join(STORIES_DIR, story_id)
        chaps_dest_dir = os.path.join(story_dest_dir, 'chapters')
        os.makedirs(chaps_dest_dir, exist_ok=True)
        
        # Download Cover Image
        local_cover_path = os.path.join(story_dest_dir, 'cover.jpg')
        if not os.path.exists(local_cover_path) and cover_img_url:
            download_cover_image(cover_img_url, local_cover_path)
            
        # 4. Crawl Chapters (Multi-threaded)
        total_words = 0
        toc_entries = []
        
        def process_chap(chap_info):
            idx = chap_info['index']
            chap_file = os.path.join(chaps_dest_dir, f"{idx}.json")
            
            if os.path.exists(chap_file):
                try:
                    with open(chap_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return idx, chap_info['title'], data.get('word_count', 0), True
                except Exception:
                    pass
                    
            content = fetch_chapter_content(chap_info['url'])
            if not content:
                content = f"Nội dung chương {idx} đang được cập nhật."
                
            word_count = len(content.split())
            chap_payload = {
                'index': idx,
                'title': chap_info['title'],
                'word_count': word_count,
                'content': content
            }
            
            with open(chap_file, 'w', encoding='utf-8') as f:
                json.dump(chap_payload, f, ensure_ascii=False, separators=(',', ':'))
                
            time.sleep(random.uniform(0.05, 0.2))
            return idx, chap_info['title'], word_count, False

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_chap, chap) for chap in chap_links]
            for fut in as_completed(futures):
                idx, ch_title, w_count, from_cache = fut.result()
                total_words += w_count
                toc_entries.append({
                    'index': idx,
                    'title': ch_title,
                    'word_count': w_count
                })
                
                status_str = "[CACHED]" if from_cache else "[FETCHED]"
                sys.stdout.write(f"\r   {status_str} Chapter {idx}/{len(chap_links)}: {w_count:,} words")
                sys.stdout.flush()
                
        print()
        toc_entries.sort(key=lambda x: x['index'])
        
        # 5. Save Partitioned TOC & Metadata
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
        
        with open(os.path.join(story_dest_dir, 'toc.json'), 'w', encoding='utf-8') as f:
            json.dump(toc_payload, f, ensure_ascii=False, indent=2)
            
        with open(os.path.join(story_dest_dir, 'metadata.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'id': story_id,
                'title': title,
                'author': author,
                'category': category,
                'source_url': story_url,
                'crawled_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, ensure_ascii=False, indent=2)
            
        # Update checkpoint
        if story_url not in checkpoint['completed_stories']:
            checkpoint['completed_stories'].append(story_url)
            save_checkpoint(checkpoint)
            
        print(f"[SUCCESS] Story '{title}' crawled ({len(toc_entries)} chaps, {total_words:,} words)!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to crawl story {story_url}: {e}")
        return False


def crawl_category(category_path, default_cat_name='Truyện Hay', max_pages=None, max_stories=None):
    """Crawl all stories listed under a specific category on TruyenC."""
    checkpoint = load_checkpoint()
    
    cat_url = urljoin(BASE_URL, category_path)
    print(f"\n==================================================")
    print(f" SCANNING CATEGORY: {cat_url} ({default_cat_name})")
    print(f"==================================================")
    
    page = 1
    story_urls = []
    seen_urls = set()
    
    while True:
        if max_pages and page > max_pages:
            break
            
        page_url = f"{cat_url}?page={page}" if page > 1 else cat_url
        print(f"-> Scanning catalogue page {page}: {page_url}")
        
        try:
            res = requests.get(page_url, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                break
                
            soup = BeautifulSoup(res.text, 'html.parser')
            page_story_urls = []
            
            for a in soup.find_all('a', href=True):
                h = a['href']
                if '/truyen/' in h and not '/chuong-' in h and not '/chap-' in h:
                    full = urljoin(BASE_URL, h)
                    if full not in seen_urls and full != cat_url:
                        seen_urls.add(full)
                        page_story_urls.append(full)
                        
            if not page_story_urls:
                print(f"-> No more stories on page {page}. Done scanning category.")
                break
                
            story_urls.extend(page_story_urls)
            print(f"   Found {len(page_story_urls)} stories (Total so far: {len(story_urls)})")
            
            if max_stories and len(story_urls) >= max_stories:
                story_urls = story_urls[:max_stories]
                break
                
            page += 1
            time.sleep(0.3)
            
        except Exception as e:
            print(f"[WARN] Error scanning page {page}: {e}")
            break
            
    print(f"\n[FOUND] Total {len(story_urls)} stories to crawl in this category.")
    
    success_count = 0
    for idx, s_url in enumerate(story_urls, 1):
        print(f"\n[{idx}/{len(story_urls)}] Processing: {s_url}")
        if s_url in checkpoint['completed_stories']:
            print("   -> Already in checkpoint. Skipping.")
            success_count += 1
            continue
            
        if crawl_story(s_url, checkpoint, default_cat_name):
            success_count += 1
            
        # Incremental sync every 10 stories
        if success_count > 0 and success_count % 10 == 0:
            print("\n[AUTO-SYNC] Synchronizing batch into Web Library...")
            os.system("python build_library.py")
            
    print(f"\n==================================================")
    print(f" CATEGORY CRAWL FINISHED: {success_count}/{len(story_urls)} stories completed")
    print(f"==================================================")


def main():
    parser = argparse.ArgumentParser(description="High-Performance Resumable Crawler for TruyenC.com")
    parser.add_argument('--category', type=str, help="Category slug (ma, 18, cuoi, audio, etc.)")
    parser.add_argument('--url', type=str, help="Crawl a single specific story URL")
    parser.add_argument('--all', action='store_true', help="Crawl all available categories")
    parser.add_argument('--limit-pages', type=int, default=None, help="Limit number of catalogue pages to scan")
    parser.add_argument('--limit-stories', type=int, default=None, help="Limit number of stories to crawl")
    
    args = parser.parse_args()
    
    categories = [
        ('ma', '/tim-truyen-ma', 'Truyện Ma, Kinh Dị'),
        ('18', '/tim-truyen-18', 'Truyện 18+, Ngôn Tình'),
        ('cuoi', '/tim-truyen-cuoi', 'Truyện Cười, Hài Hước'),
        ('audio', '/tim-truyen-audio', 'Truyện Audio, Đêm Khuya')
    ]
    
    checkpoint = load_checkpoint()
    
    if args.url:
        crawl_story(args.url, checkpoint)
    elif args.category:
        found = False
        for c_slug, c_path, c_name in categories:
            if args.category.lower() in [c_slug, c_slug.replace('-', '')]:
                crawl_category(c_path, c_name, max_pages=args.limit_pages, max_stories=args.limit_stories)
                found = True
                break
        if not found:
            crawl_category(f"/tim-truyen-{args.category}", f"Truyện {args.category.title()}", max_pages=args.limit_pages, max_stories=args.limit_stories)
    else:
        # Default or --all: Crawl all categories sequentially
        print("[INFO] Starting comprehensive full website crawl across all categories...")
        for c_slug, c_path, c_name in categories:
            crawl_category(c_path, c_name, max_pages=args.limit_pages, max_stories=args.limit_stories)
            
    print("\n[FINAL SYNC] Integrating all crawled stories into Web Library...")
    os.system("python build_library.py")


if __name__ == '__main__':
    main()
