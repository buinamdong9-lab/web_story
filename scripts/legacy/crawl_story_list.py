import asyncio
import httpx
from lxml import html
import json
import time
import sys
from clean_utils import clean_chapter_title

sys.stdout.reconfigure(encoding='utf-8')

STORY_URL = "https://akaytruyen.com/truyen/ngoai-truyen-chua-te-chi-lo"

async def get_chapter_list():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    async with httpx.AsyncClient() as client:
        res = await client.get(STORY_URL, headers=headers, follow_redirects=True)
        tree = html.fromstring(res.content)
        
        # Find all chapter links
        links = tree.xpath('//a[contains(@href, "/chuong-")]/@href')
        
        seen = set()
        chapter_urls = []
        for l in links:
            if not l.startswith('http'):
                l = "https://akaytruyen.com" + l
            if l not in seen:
                seen.add(l)
                chapter_urls.append(l)
                
        return chapter_urls

class FastBatchCrawler:
    def __init__(self, cookie_str: str = "", max_concurrent: int = 20):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        if cookie_str:
            self.headers['Cookie'] = cookie_str

    async def fetch_chapter(self, client: httpx.AsyncClient, idx: int, url: str) -> dict:
        async with self.semaphore:
            start_t = time.perf_counter()
            try:
                res = await client.get(url, headers=self.headers, follow_redirects=True, timeout=15.0)
                tree = html.fromstring(res.content)
                
                raw_title = "".join(tree.xpath('//title/text()')).strip()
                title = clean_chapter_title(raw_title, "Ngoại Truyện - Chúa Tể Chi Lộ")
                chapter_elem = tree.xpath('//*[@id="chapter-content"]')
                content_text = chapter_elem[0].text_content().strip() if chapter_elem else ""
                
                elapsed = round((time.perf_counter() - start_t) * 1000, 2)
                is_vip = "dành cho tài khoản VIP" in content_text or "Truy cập bị hạn chế" in content_text
                
                status_str = "🔒 VIP" if is_vip else "✅ FREE"
                chap_name = url.split('/')[-1]
                print(f"[{status_str}] ({idx:02d}) {chap_name} | {res.status_code} | {elapsed}ms")

                return {
                    "index": idx,
                    "url": url,
                    "slug": chap_name,
                    "title": title,
                    "is_vip_locked": is_vip,
                    "content": content_text,
                    "status": res.status_code,
                    "fetch_time_ms": elapsed
                }
            except Exception as e:
                print(f"❌ ({idx:02d}) {url}: Lỗi {e}")
                return {"index": idx, "url": url, "error": str(e)}

    async def crawl_urls(self, urls: list[str]):
        limits = httpx.Limits(max_keepalive_connections=40, max_connections=40)
        async with httpx.AsyncClient(limits=limits) as client:
            tasks = [self.fetch_chapter(client, i+1, u) for i, u in enumerate(urls)]
            return await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("🔍 Đang kết nối lấy danh sách tất cả các chương từ trang chủ bộ truyện...")
    urls = asyncio.run(get_chapter_list())
    print(f"📋 Tìm thấy tổng cộng {len(urls)} chương!")
    
    if urls:
        print(f"\n🚀 Bắt đầu cào siêu tốc {len(urls)} chương...")
        start_t = time.perf_counter()
        
        crawler = FastBatchCrawler(max_concurrent=20)
        results = asyncio.run(crawler.crawl_urls(urls))
        
        total_time = round(time.perf_counter() - start_t, 2)
        print(f"\n✨ Hoàn thành cào {len(results)} chương trong {total_time} giây!")
        
        # Save output
        out_json = "all_chapters_crawled.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        out_md = "all_chapters_crawled.md"
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(f"# Kết quả cào bộ truyện: Ngoại Truyện - Chúa Tể Chi Lộ\n\n")
            f.write(f"- **Tổng số chương cào:** {len(results)}\n")
            f.write(f"- **Thời gian cào:** {total_time} giây\n\n")
            f.write("---\n\n")
            for item in results:
                if "error" in item:
                    f.write(f"## Chương {item['index']}: Lỗi - {item['error']}\n\n")
                else:
                    f.write(f"# {item['title']}\n\n")
                    f.write("```\n")
                    f.write(item['content'][:300] + ("..." if len(item['content']) > 300 else ""))
                    f.write("\n```\n\n---\n\n")
                    
        print(f"💾 Kết quả đã được xuất ra tệp:\n - {out_json}\n - {out_md}")

