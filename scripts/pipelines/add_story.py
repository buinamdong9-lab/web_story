import os
import sys
import json
import argparse
import re
from clean_utils import clean_chapter_content, clean_chapter_title
from build_library import build_all_library, slugify

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

def import_story(json_path, title=None, author=None, category=None, description=None, status=None, cover_path=None):
    """Imports, cleans, and registers a new story into the library"""
    print("==================================================")
    print("       WEB STORY - IMPORT & CLEAN ENGINE          ")
    print("==================================================")

    if not os.path.exists(json_path):
        print(f"[ERROR] JSON file not found: {json_path}")
        return False

    with open(json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    if isinstance(raw_data, list):
        chapters = raw_data
        default_title = os.path.splitext(os.path.basename(json_path))[0].replace('_', ' ').title()
    elif isinstance(raw_data, dict) and 'chapters' in raw_data:
        chapters = raw_data['chapters']
        default_title = raw_data.get('title', 'Truyện Mới')
    else:
        chapters = [raw_data]
        default_title = raw_data.get('title', 'Truyện Mới')

    title = title or default_title
    author = author or 'Đang Cập Nhật'
    category = category or 'Tiên Hiệp, Huyền Huyễn'
    description = description or 'Bộ truyện hấp dẫn với nhiều tình tiết đặc sắc.'
    status = status or ('Hoàn Thành' if len(chapters) > 10 else 'Đang Cập Nhật')
    story_id = slugify(title)

    print(f"-> Processing story: '{title}' ({len(chapters)} chapters)")

    # Clean chapters content and titles
    cleaned_chapters = []
    for i, chap in enumerate(chapters):
        c_idx = chap.get('index', i + 1)
        raw_t = chap.get('title', f'Chương {c_idx}')
        raw_c = chap.get('content', '')

        clean_t = clean_chapter_title(raw_t) or f"Chương {c_idx}"
        clean_c = clean_chapter_content(raw_c)

        cleaned_chapters.append({
            'index': c_idx,
            'title': clean_t,
            'content': clean_c
        })

    # Save cleaned version back to stories dir
    out_dir = os.path.join('web', 'data', 'stories', story_id)
    chaps_dir = os.path.join(out_dir, 'chapters')
    os.makedirs(chaps_dir, exist_ok=True)

    cover_filename = f"images/{story_id}_cover.jpg"
    if cover_path and os.path.exists(cover_path):
        import shutil
        target_img_web = os.path.join('web', cover_filename)
        target_img_root = os.path.join(cover_filename)
        shutil.copy(cover_path, target_img_web)
        shutil.copy(cover_path, target_img_root)
        print(f"-> Saved cover image to {cover_filename}")
    else:
        cover_filename = 'images/cover.jpg'

    # Run build_library to pack, minify, and sync
    build_all_library()

    print(f"\n[SUCCESS] Successfully imported '{title}' into Web Story Library!")
    print(f"-> Access story at: #story/{story_id}")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Import a crawled JSON story into Web Story Library")
    parser.add_argument('--json', help="Path to story JSON file")
    parser.add_argument('--title', help="Story Title")
    parser.add_argument('--author', help="Story Author")
    parser.add_argument('--category', help="Story Category/Genres")
    parser.add_argument('--desc', help="Story Description")
    parser.add_argument('--cover', help="Path to cover image file")

    args = parser.parse_args()

    if args.json:
        import_story(
            json_path=args.json,
            title=args.title,
            author=args.author,
            category=args.category,
            description=args.desc,
            cover_path=args.cover
        )
    else:
        print("Usage Example:")
        print("python add_story.py --json story.json --title \"Đấu Phá Thương Khung\" --author \"Thiên Tằm Thổ Đậu\"")
