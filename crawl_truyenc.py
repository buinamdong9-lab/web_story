import sys
import httpx
from lxml import html
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

url = "https://truyenc.com/truyen/than-nu-tieu-dao-luc-ntr-1857"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

res = httpx.get(url, follow_redirects=True, headers=headers)
print("Status:", res.status_code)
print("Final URL:", res.url)
print("Length:", len(res.text))

tree = html.fromstring(res.content)
title = "".join(tree.xpath('//title/text()')).strip()
print("Title:", title)

# Save page html for analysis
with open("truyenc_main.html", "w", encoding="utf-8") as f:
    f.write(res.text)

# Find all links
all_links = tree.xpath('//a/@href')
print(f"Total links found: {len(all_links)}")

chap_links = []
for l in all_links:
    if any(k in l for k in ['chuong', 'chapter', 'than-nu-tieu-dao-luc']):
        if not l.startswith('http'):
            l = "https://truyenc.com" + l
        chap_links.append(l)

# Unique chap links
unique_chaps = list(dict.fromkeys(chap_links))
print(f"Chapter links ({len(unique_chaps)}):")
for c in unique_chaps[:20]:
    print(" -", c)
