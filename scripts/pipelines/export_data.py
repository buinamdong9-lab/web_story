import sys
import json
import urllib.request
from bs4 import BeautifulSoup
from clean_utils import clean_chapter_title

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://akaytruyen.com/ngoai-truyen-chua-te-chi-lo/chuong-39-nguoi-la-ac-quy'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

req = urllib.request.Request(url, headers=headers)
html_str = urllib.request.urlopen(req).read().decode('utf-8')
soup = BeautifulSoup(html_str, 'html.parser')

raw_title = soup.title.get_text(strip=True) if soup.title else ""
title = clean_chapter_title(raw_title)

# Extract breadcrumb or chapter header info
header_info = []
for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
    text = h.get_text(strip=True)
    if text:
        header_info.append(clean_chapter_title(text))

# Extract chapter-content
chapter_content_div = soup.find(id='chapter-content')
chapter_content_text = chapter_content_div.get_text(separator='\n', strip=True) if chapter_content_div else ""

# Extract comments if any
comments = []
comment_divs = soup.find_all(class_='content-post-comments')
for c in comment_divs:
    text = c.get_text(separator='\n', strip=True)
    if text:
        comments.append(text)

data = {
    "page_title": title,
    "headings": header_info,
    "chapter_content": chapter_content_text,
    "comments_count": len(comments),
    "comments": comments
}

# Save as JSON
with open('chuong_39_nguoi_la_ac_quy.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Save as Markdown report
md_content = f"""# {title}

## Thông tin chương:
- **Tiêu đề:** {title}
- **Các mục tiêu đề (Headings):**
{chr(10).join(f'  - {h}' for h in header_info)}

## Nội dung chương (Chapter Content):
```
{chapter_content_text}
```

> **Ghi chú về nội dung:** Chương 39 này thuộc danh mục Ngoại Truyện khóa VIP của `akaytruyen.com`. Nội dung chữ của chương yêu cầu tài khoản VIP mới có thể truy cập đầy đủ từ máy chủ.

## Bình luận nổi bật ({len(comments)} bình luận):
"""
for idx, cm in enumerate(comments[:10], 1):
    md_content += f"\n### Bình luận {idx}:\n```\n{cm}\n```\n"

with open('chuong_39_nguoi_la_ac_quy.md', 'w', encoding='utf-8') as f:
    f.write(md_content)

print("Export completed successfully!")

