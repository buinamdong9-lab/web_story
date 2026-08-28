import os
import json
import re
import sys
from clean_utils import clean_chapter_title, generate_story_markdown

sys.stdout.reconfigure(encoding='utf-8')

def clean_than_nu_dataset():
    json_path = "Than_Nu_Tieu_Dao_Luc.json"
    md_path = "Than_Nu_Tieu_Dao_Luc.md"

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            if "title" in item:
                item["title"] = clean_chapter_title(item["title"], "Thần Nữ Tiêu Dao Lục")
            if "url" in item:
                del item["url"]

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã làm sạch file: {json_path}")

        # Re-generate clean Markdown with TOC & Outline
        md_content = generate_story_markdown("Thần Nữ Tiêu Dao Lục", data)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"✅ Đã làm sạch & xuất tệp Markdown với Mục Lục chuẩn: {md_path}")


def clean_batch_dataset(json_path, md_path, story_name=""):
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            if "title" in item:
                item["title"] = clean_chapter_title(item["title"], story_name)
            if "url" in item:
                del item["url"]

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã làm sạch file: {json_path}")

        if os.path.exists(md_path):
            md_content = generate_story_markdown(story_name or "Kết quả cào bộ truyện", data)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            print(f"✅ Đã làm sạch & xuất tệp Markdown với Mục Lục chuẩn: {md_path}")



if __name__ == "__main__":
    clean_than_nu_dataset()
    clean_batch_dataset("full_story_batch.json", "full_story_batch.md", "Ngoại Truyện - Chúa Tể Chi Lộ")
    clean_batch_dataset("all_chapters_crawled.json", "all_chapters_crawled.md", "Ngoại Truyện - Chúa Tể Chi Lộ")
