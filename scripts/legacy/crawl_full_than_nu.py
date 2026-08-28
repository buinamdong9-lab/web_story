import asyncio
import httpx
from lxml import html
import json
import time
import sys
import re
from clean_utils import clean_chapter_title

sys.stdout.reconfigure(encoding='utf-8')

STORY_URL = "https://truyenc.com/truyen/than-nu-tieu-dao-luc-ntr-1857"

def extract_chap_num(url: str) -> float:
    if "tua-" in url:
        return 0.0
    match = re.search(r'chuong-(\d+)', url)
    if match:
        return float(match.group(1))
    return 999.0

async def get_sorted_chapter_urls():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    async with httpx.AsyncClient() as client:
        res = await client.get(STORY_URL, headers=headers, follow_redirects=True)
        tree = html.fromstring(res.content)
        
        links = tree.xpath('//a[contains(@href, "/chuong-") or contains(@href, "/tua-")]/@href')
        seen = set()
        urls = []
        for l in links:
            if not l.startswith('http'):
                l = "https://truyenc.com" + l
            if l not in seen:
                seen.add(l)
                urls.append(l)
                
        # Sort by chapter number
        urls.sort(key=extract_chap_num)
        return urls

class ThanNuCrawler:
    def __init__(self, max_concurrent: int = 15):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

    async def fetch_chapter(self, client: httpx.AsyncClient, idx: int, url: str) -> dict:
        async with self.semaphore:
            start_t = time.perf_counter()
            try:
                res = await client.get(url, headers=self.headers, follow_redirects=True, timeout=20.0)
                tree = html.fromstring(res.content)
                
                # Clean scripts/styles/iframes
                for bad in tree.xpath('//script|//style|//iframe'):
                    bad.getparent().remove(bad)
                    
                title_elem = tree.xpath('//h1|//title')
                raw_title = title_elem[0].text_content().strip() if title_elem else f"Chương {idx}"
                title = clean_chapter_title(raw_title, "Thần Nữ Tiêu Dao Lục")

                content_div = tree.xpath('//div[contains(@class, "story-content")]')
                if content_div:
                    # Clean paragraphs
                    paras = [p.text_content().strip() for p in content_div[0].xpath('.//p') if p.text_content().strip()]
                    if not paras:
                        # Fallback to direct text
                        raw_text = content_div[0].text_content().strip()
                        paras = [line.strip() for line in raw_text.split('\n') if line.strip()]
                    content_text = "\n\n".join(paras)
                else:
                    content_text = ""

                elapsed = round((time.perf_counter() - start_t) * 1000, 2)
                slug = url.split('/')[-1]
                print(f"✅ ({idx:03d}/{102}) {slug[:35]} | HTTP {res.status_code} | {elapsed}ms | {len(content_text)} chars")

                return {
                    "index": idx,
                    "url": url,
                    "title": title,
                    "content": content_text,
                    "char_count": len(content_text),
                    "status": res.status_code,
                    "fetch_time_ms": elapsed
                }
            except Exception as e:
                print(f"❌ ({idx:03d}) {url}: Lỗi {e}")
                return {"index": idx, "url": url, "error": str(e)}

    async def crawl_all(self, urls: list[str]):
        limits = httpx.Limits(max_keepalive_connections=30, max_connections=30)
        async with httpx.AsyncClient(limits=limits) as client:
            tasks = [self.fetch_chapter(client, i+1, u) for i, u in enumerate(urls)]
            return await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("🔍 Đang kết nối lấy danh sách chương của bộ truyện 'Thần Nữ Tiêu Dao Lục'...")
    urls = asyncio.run(get_sorted_chapter_urls())
    print(f"📋 Đã tìm thấy và sắp xếp theo thứ tự {len(urls)} chương!")

    if urls:
        print(f"\n🚀 Bắt đầu cào siêu tốc {len(urls)} chương...")
        start_t = time.perf_counter()

        crawler = ThanNuCrawler(max_concurrent=15)
        results = asyncio.run(crawler.crawl_all(urls))

        total_time = round(time.perf_counter() - start_t, 2)
        print(f"\n✨ Đã hoàn thành cào {len(results)} chương trong {total_time} giây!")

        # Export to Markdown file
        md_file = "Than_Nu_Tieu_Dao_Luc.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("# Thần Nữ Tiêu Dao Lục\n\n")
            f.write(f"- **Tổng số chương:** {len(results)}\n")
            f.write(f"- **Thời gian cào:** {total_time} giây\n\n")
            f.write("---\n\n")
            
            for item in results:
                if "error" in item:
                    f.write(f"## Chương {item['index']}: Lỗi - {item['error']}\n\n")
                else:
                    f.write(f"# {item['title']}\n\n")
                    f.write(item['content'])
                    f.write("\n\n---\n\n")

        # Export JSON
        json_file = "Than_Nu_Tieu_Dao_Luc.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Tệp Markdown chính thức đã lưu tại: {md_file}")
        print(f"💾 Tệp JSON đã lưu tại: {json_file}")


