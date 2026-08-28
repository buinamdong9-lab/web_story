import asyncio
import httpx
from lxml import html
import json
import time
import sys
import os
from clean_utils import clean_chapter_title

sys.stdout.reconfigure(encoding='utf-8')

class BatchCrawler:
    def __init__(self, cookie_str: str = "", max_concurrent: int = 15):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        if cookie_str:
            self.headers['Cookie'] = cookie_str

    async def fetch_chapter(self, client: httpx.AsyncClient, chapter_num: int, base_url: str) -> dict:
        url = f"{base_url}/chuong-{chapter_num}"
        async with self.semaphore:
            start_t = time.perf_counter()
            try:
                res = await client.get(url, headers=self.headers, follow_redirects=True, timeout=12.0)
                
                tree = html.fromstring(res.content)
                raw_title = "".join(tree.xpath('//title/text()')).strip()
                title = clean_chapter_title(raw_title)
                
                chapter_elem = tree.xpath('//*[@id="chapter-content"]')
                content_text = chapter_elem[0].text_content().strip() if chapter_elem else ""

                elapsed = round((time.perf_counter() - start_t) * 1000, 2)
                is_vip = "dành cho tài khoản VIP" in content_text or "Truy cập bị hạn chế" in content_text
                
                status_str = "🔒 VIP Lock" if is_vip else "✅ Public"
                print(f"[{status_str}] Chương {chapter_num:02d} | Status: {res.status_code} | Time: {elapsed}ms | {title[:40]}")

                return {
                    "chapter": chapter_num,
                    "url": url,
                    "title": title,
                    "is_vip_locked": is_vip,
                    "content": content_text,
                    "status": res.status_code,
                    "fetch_time_ms": elapsed
                }
            except Exception as e:
                print(f"❌ Chương {chapter_num}: Lỗi {e}")
                return {"chapter": chapter_num, "url": url, "error": str(e)}

    async def crawl_batch(self, start_chap: int, end_chap: int, base_url: str):
        limits = httpx.Limits(max_keepalive_connections=30, max_connections=30)
        async with httpx.AsyncClient(limits=limits) as client:
            tasks = [self.fetch_chapter(client, i, base_url) for i in range(start_chap, end_chap + 1)]
            results = await asyncio.gather(*tasks)
            return list(results)

if __name__ == "__main__":
    BASE_STORY_URL = "https://akaytruyen.com/ngoai-truyen-chua-te-chi-lo"
    COOKIE = "" 
    
    START_CHAP = 1
    END_CHAP = 39
    
    print(f"🚀 Tiến hành cào hàng loạt từ Chương {START_CHAP} đến Chương {END_CHAP}...")
    start_time = time.perf_counter()
    
    crawler = BatchCrawler(cookie_str=COOKIE, max_concurrent=15)
    results = asyncio.run(crawler.crawl_batch(START_CHAP, END_CHAP, BASE_STORY_URL))
    
    total_time = round(time.perf_counter() - start_time, 2)
    print(f"\n✨ Hoàn thành cào {len(results)} chương trong {total_time} giây!")
    
    # Save output
    out_json = "full_story_batch.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    out_md = "full_story_batch.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(f"# Kết quả cào bộ truyện: Ngoại Truyện - Chúa Tể Chi Lộ (Chương {START_CHAP} - {END_CHAP})\n\n")
        f.write(f"- **Tổng số chương:** {len(results)}\n")
        f.write(f"- **Thời gian thực hiện:** {total_time} giây\n\n")
        f.write("--- \n\n")
        for item in results:
            if "error" in item:
                f.write(f"## Chương {item['chapter']}: Lỗi - {item['error']}\n\n")
            else:
                f.write(f"# {item['title']}\n\n")
                f.write("```\n")
                f.write(item['content'][:500] + ("..." if len(item['content']) > 500 else ""))
                f.write("\n```\n\n---\n\n")
                
    print(f"💾 Đã lưu kết quả tại: {out_json} và {out_md}")

