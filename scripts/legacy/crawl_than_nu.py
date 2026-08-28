import sys
import httpx
from lxml import html
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

STORY_URL = "https://truyenc.com/truyen/than-nu-tieu-dao-luc-ntr-1857"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_all_chapter_urls():
    res = httpx.get(STORY_URL, follow_redirects=True, headers=headers)
    tree = html.fromstring(res.content)
    
    # Check pagination
    page_links = tree.xpath('//ul[contains(@class, "pagination")]//a/@href | //div[contains(@class, "pagination")]//a/@href')
    print("Pagination links found:", len(page_links))
    
    all_pages = [STORY_URL]
    for p in page_links:
        if not p.startswith('http'):
            p = "https://truyenc.com" + p
        if p not in all_pages:
            all_pages.append(p)
            
    chapter_urls = []
    seen = set()
    
    for page_url in all_pages:
        r = httpx.get(page_url, follow_redirects=True, headers=headers)
        t = html.fromstring(r.content)
        links = t.xpath('//a[contains(@href, "/chuong-") or contains(@href, "/tua-")]/@href')
        for l in links:
            if not l.startswith('http'):
                l = "https://truyenc.com" + l
            if l not in seen:
                seen.add(l)
                chapter_urls.append(l)
                
    return chapter_urls

if __name__ == "__main__":
    chaps = get_all_chapter_urls()
    print(f"Found {len(chaps)} chapter URLs total!")
    for i, c in enumerate(chaps[:10], 1):
        print(f"  {i}. {c}")
