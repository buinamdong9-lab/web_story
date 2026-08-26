import sys
import httpx
from lxml import html

sys.stdout.reconfigure(encoding='utf-8')

chap_url = 'https://truyenc.com/truyen/than-nu-tieu-dao-luc-ntr/chuong-1-day-song-gio-87709'
res = httpx.get(chap_url, follow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})

tree = html.fromstring(res.content)
for bad in tree.xpath('//script|//style|//iframe'):
    bad.getparent().remove(bad)

elem = tree.xpath('//div[contains(@class, "story-content")]')
if elem:
    text = elem[0].text_content().strip()
    print("Clean Chapter 1 Text (First 600 chars):")
    print(text[:600])
    print("\nLength of Chapter 1 text:", len(text))
