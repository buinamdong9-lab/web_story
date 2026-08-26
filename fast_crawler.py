import asyncio
import httpx
from lxml import html
import json
import time
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

class FastCrawler:
    """
    High-Performance Crawler utilizing:
    - HTTP/2 & Async I/O (httpx / asyncio) for non-blocking concurrent requests.
    - C-based HTML Engine (lxml with C-libxml2 binding) for ultra-fast DOM parsing.
    """
    def __init__(self, cookie_str: str = ""):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        if cookie_str:
            self.headers['Cookie'] = cookie_str
            
    async def fetch_page(self, client: httpx.AsyncClient, url: str) -> dict:
        start_t = time.perf_counter()
        try:
            res = await client.get(url, headers=self.headers, follow_redirects=True, timeout=10.0)
            fetch_time = (time.perf_counter() - start_t) * 1000  # ms

            parse_start = time.perf_counter()
            # C-Engine Parsing via lxml
            tree = html.fromstring(res.content)
            
            title = "".join(tree.xpath('//title/text()')).strip()
            
            # Extract content via XPath (C-implemented)
            chapter_elem = tree.xpath('//*[@id="chapter-content"]')
            content_text = chapter_elem[0].text_content().strip() if chapter_elem else ""

            # Extract headings
            headings = [h.text_content().strip() for h in tree.xpath('//h1|//h2|//h3|//h4') if h.text_content().strip()]
            
            # Extract comments
            comments = [c.text_content().strip() for c in tree.xpath('//*[contains(@class, "content-post-comments")]')]
            
            parse_time = (time.perf_counter() - parse_start) * 1000  # ms
            
            return {
                "url": url,
                "status_code": res.status_code,
                "page_title": title,
                "headings": headings,
                "chapter_content": content_text,
                "comments_count": len(comments),
                "comments": comments,
                "metrics": {
                    "fetch_time_ms": round(fetch_time, 2),
                    "c_parse_time_ms": round(parse_time, 2)
                }
            }
        except Exception as e:
            return {
                "url": url,
                "error": str(e)
            }

    async def crawl_urls(self, urls: list[str], max_concurrency: int = 10) -> list[dict]:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=max_concurrency)
        async with httpx.AsyncClient(limits=limits) as client:
            tasks = [self.fetch_page(client, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return list(results)

if __name__ == "__main__":
    test_urls = [
        "https://akaytruyen.com/ngoai-truyen-chua-te-chi-lo/chuong-39-nguoi-la-ac-quy"
    ]
    
    # Enter valid cookie here if available
    COOKIE = "" 
    
    print("🚀 Starting High-Performance Crawler (Async I/O + C-libxml2 Engine)...")
    start = time.perf_counter()
    
    crawler = FastCrawler(cookie_str=COOKIE)
    results = asyncio.run(crawler.crawl_urls(test_urls))
    
    total_time = (time.perf_counter() - start) * 1000
    
    for res in results:
        print(f"\n✅ Finished URL: {res['url']}")
        print(f"   - HTTP Status: {res.get('status_code')}")
        print(f"   - Page Title: {res.get('page_title')}")
        print(f"   - Fetch Time: {res['metrics']['fetch_time_ms']} ms")
        print(f"   - C-Engine Parse Time: {res['metrics']['c_parse_time_ms']} ms")
        print(f"   - Total Crawl Execution: {round(total_time, 2)} ms")
        
    # Save output
    output_path = "fast_crawl_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved results to {output_path}")
