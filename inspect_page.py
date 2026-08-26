import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('page.html', 'r', encoding='utf-8') as f:
    html = f.read()

lw = re.findall(r'wire:snapshot="([^"]+)"', html)
print(f"Livewire snapshots found: {len(lw)}")
for s in lw[:5]:
    print("Snapshot:", s[:200])

apis = re.findall(r'https?://[^\s"\'<>]+', html)
api_set = set(apis)
print("Total URLs in HTML:", len(api_set))
for u in sorted(api_set):
    if any(k in u for k in ['api', 'livewire', 'storage', 'chapter', 'json', 'content']):
        print(" -", u)
