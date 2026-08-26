import sys
import urllib.request
from bs4 import BeautifulSoup
import re
import os

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://akaytruyen.com/ngoai-truyen-chua-te-chi-lo/chuong-39-nguoi-la-ac-quy'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

req = urllib.request.Request(url, headers=headers)
html = urllib.request.urlopen(req).read().decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')

print("Page Title:", soup.title.get_text(strip=True) if soup.title else "No title")

# Save raw HTML for inspection if needed
with open('page.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Look for story content block
possible_containers = soup.find_all(class_=lambda x: x and ('content' in x or 'chapter' in x or 'reading' in x or 'box' in x or 'truyen' in x))
print(f"Found {len(possible_containers)} potential content elements")

for i, c in enumerate(possible_containers):
    text = c.get_text(separator="\n", strip=True)
    if len(text) > 300 and "Thế lực" not in text[:50] and "Thể loại" not in text[:50]:
        print(f"--- Candidate {i} (Class: {c.get('class')}, ID: {c.get('id')}, Length {len(text)}): ---")
        print(text[:300])
        print("...\n")
