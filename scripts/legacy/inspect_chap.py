import sys
import httpx
from lxml import html

sys.stdout.reconfigure(encoding='utf-8')

chap_url = 'https://truyenc.com/truyen/than-nu-tieu-dao-luc-ntr/chuong-1-day-song-gio-87709'
res = httpx.get(chap_url, follow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
print("Status:", res.status_code)

tree = html.fromstring(res.content)
title = "".join(tree.xpath('//title/text()')).strip()
print("Title:", title)

# Save chapter HTML for inspection
with open("chap_sample.html", "w", encoding="utf-8") as f:
    f.write(res.text)

# Search for story content container
for elem in tree.xpath('//*[contains(@class, "chapter") or contains(@class, "content") or contains(@id, "chapter") or contains(@id, "content")]'):
    text = elem.text_content().strip()
    if len(text) > 300 and "truyenc" not in text[:50].lower():
        print(f"Elem <{elem.tag}> class='{elem.get('class')}' id='{elem.get('id')}':")
        print(text[:300])
        print("="*40)
