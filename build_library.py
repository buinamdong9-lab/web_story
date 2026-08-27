import os
import sys
import json
import re
import shutil

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

def slugify(text):
    """Convert Vietnamese text to a clean URL-friendly slug"""
    text = text.lower().replace('_', ' ')
    text = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', text)
    text = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', text)
    text = re.sub(r'[ìíịỉĩ]', 'i', text)
    text = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', text)
    text = re.sub(r'[ùúụủũưừứựửữ]', 'u', text)
    text = re.sub(r'[ỳýỵỷỹ]', 'y', text)
    text = re.sub(r'[đ]', 'd', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text or 'story'

def process_story(json_path, story_id=None, story_meta=None):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        if isinstance(data, dict) and 'chapters' in data:
            chapters_data = data['chapters']
            default_title = data.get('title', 'Truyện Mới')
        else:
            chapters_data = [data]
            default_title = data.get('title', 'Truyện Mới')
    else:
        chapters_data = data
        default_title = os.path.splitext(os.path.basename(json_path))[0].replace('_', ' ').title()

    if not story_id:
        story_id = slugify(default_title)

    meta = {
        'id': story_id,
        'title': default_title,
        'original_title': '',
        'author': 'Đang Cập Nhật',
        'category': 'Tiên Hiệp, Huyền Huyễn',
        'status': 'Hoàn Thành' if len(chapters_data) > 10 else 'Đang Cập Nhật',
        'description': 'Bộ truyện hấp dẫn với nhiều tình tiết đặc sắc.',
        'cover_image': f'images/{story_id}_cover.jpg'
    }

    if isinstance(data, dict):
        for k in ['title', 'author', 'category', 'status', 'description', 'cover_image', 'original_title']:
            if k in data and data[k]:
                meta[k] = data[k]

    if story_meta:
        meta.update(story_meta)

    # Special metadata for Thần Nữ Tiêu Dao Lục
    if 'than_nu' in story_id or 'than-nu' in story_id:
        meta['title'] = 'Thần Nữ Tiêu Dao Lục'
        meta['original_title'] = '神女逍遥录'
        meta['author'] = 'Vô Danh'
        meta['category'] = 'Tiên Hiệp, Huyền Huyễn, Tu Chân, Hậu Cung, Sắc Hiệp'
        meta['status'] = 'Hoàn Thành'
        meta['description'] = 'Tại rìa bắc đại lục, đỉnh tuyết sơn sừng sững chín tầng mây có Thiên Cơ Các thần bí. Truyền thuyết kể rằng nơi đây cất giấu Thiên Mệnh Bảng và Mỹ Nhân Bảng. Thiếu niên Tô Lan mười sáu tuổi tại thôn Triều Sinh vô tình có được một thiên pháp môn tu đạo thâm áo trong nội thị tâm hải, mở ra hành trình kỳ duyên giữa Long tộc cấm địa và các tuyệt sắc thần nữ tiên tử...'
        meta['cover_image'] = 'images/than_nu_tieu_dao_luc_cover.jpg'

    toc = []
    total_words = 0

    web_stories_dir = os.path.join('web', 'data', 'stories', story_id)
    chapters_dir = os.path.join(web_stories_dir, 'chapters')
    os.makedirs(chapters_dir, exist_ok=True)

    for i, item in enumerate(chapters_data):
        idx = item.get('index', i + 1)
        title = item.get('title', f'Chương {idx}')
        content = item.get('content', '')
        char_count = len(content)
        word_count = len(content.split())
        total_words += word_count

        toc.append({
            'index': idx,
            'title': title,
            'char_count': char_count,
            'word_count': word_count
        })

        chap_file = os.path.join(chapters_dir, f"{idx}.json")
        # Save ultra-compact minified JSON
        with open(chap_file, 'w', encoding='utf-8') as cf:
            json.dump({
                'story_id': story_id,
                'index': idx,
                'title': title,
                'content': content,
                'word_count': word_count,
                'char_count': char_count
            }, cf, ensure_ascii=False, separators=(',', ':'))

    meta['total_chapters'] = len(toc)
    meta['total_words'] = total_words

    # Save detailed story TOC (minified)
    toc_file = os.path.join(web_stories_dir, 'toc.json')
    with open(toc_file, 'w', encoding='utf-8') as tf:
        json.dump({
            **meta,
            'chapters': toc
        }, tf, ensure_ascii=False, separators=(',', ':'))

    print(f"-> Processed '{meta['title']}' ({len(toc)} chaps, {total_words:,} words) -> {web_stories_dir}")

    # Return ultra-lightweight card index record for the 100-1000 story catalogue
    # We truncate description to 120 chars so 1,000 stories JSON index is < 150KB!
    short_desc = (meta['description'][:120] + '...') if len(meta['description']) > 120 else meta['description']
    return {
        'id': meta['id'],
        'title': meta['title'],
        'author': meta['author'],
        'category': meta['category'],
        'status': meta['status'],
        'description': short_desc,
        'cover_image': meta['cover_image'],
        'total_chapters': meta['total_chapters'],
        'total_words': meta['total_words']
    }

def generate_pwa_manifest(web_dir):
    """Generate Progressive Web App manifest for offline installation"""
    manifest = {
        "name": "Kho Truyện Chữ & Audio Tự Động",
        "short_name": "WebStory",
        "start_url": "./",
        "display": "standalone",
        "background_color": "#0d0f17",
        "theme_color": "#8b5cf6",
        "description": "Đọc và nghe audio truyện online tốc độ cao, hỗ trợ đa giọng đọc AI và offline reading.",
        "icons": [
            {
                "src": "images/cover.jpg",
                "sizes": "512x512",
                "type": "image/jpeg"
            }
        ]
    }
    with open(os.path.join(web_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def build_all_library():
    web_dir = 'web'
    data_dir = os.path.join(web_dir, 'data')
    img_dir = os.path.join(web_dir, 'images')

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    # Copy cover images if available
    cover_artifact = r'C:\Users\DONGTTNT\.gemini\antigravity-ide\brain\e21e1fc3-75ce-42f7-92fa-fea77708768e\than_nu_cover_1787731152238.jpg'
    if os.path.exists(cover_artifact):
        shutil.copy(cover_artifact, os.path.join(img_dir, 'than_nu_tieu_dao_luc_cover.jpg'))
        shutil.copy(cover_artifact, os.path.join(img_dir, 'cover.jpg'))

    stories_manifest = []

    # 1. Main story: Than Nu Tieu Dao Luc
    if os.path.exists('Than_Nu_Tieu_Dao_Luc.json'):
        meta = process_story('Than_Nu_Tieu_Dao_Luc.json', 'than_nu_tieu_dao_luc')
        stories_manifest.append(meta)

        # For backwards compatibility with single-story endpoints:
        shutil.copytree(
            os.path.join(data_dir, 'stories', 'than_nu_tieu_dao_luc', 'chapters'),
            os.path.join(data_dir, 'chapters'),
            dirs_exist_ok=True
        )
        shutil.copy(
            os.path.join(data_dir, 'stories', 'than_nu_tieu_dao_luc', 'toc.json'),
            os.path.join(data_dir, 'toc.json')
        )

    # 2. Automatically scan for any other story JSON files
    for fname in os.listdir('.'):
        if fname.endswith('.json') and fname not in [
            'Than_Nu_Tieu_Dao_Luc.json', 'all_chapters_crawled.json', 
            'fast_crawl_results.json', 'full_story_batch.json',
            'manifest.json', 'package.json', 'package-lock.json', 'tsconfig.json'
        ]:
            try:
                sid = slugify(os.path.splitext(fname)[0])
                meta = process_story(fname, sid)
                stories_manifest.append(meta)
            except Exception as e:
                print(f"Skipping {fname}: {e}")

    # Extract all distinct categories for instant category filtering
    all_categories = set()
    for s in stories_manifest:
        cats = [c.strip() for c in s.get('category', '').split(',') if c.strip()]
        all_categories.update(cats)

    # Write global Library stories catalogue (Ultra-lean & Minified)
    library_file = os.path.join(data_dir, 'stories.json')
    with open(library_file, 'w', encoding='utf-8') as lf:
        json.dump({
            'updated_at': '2026-08-26',
            'total_stories': len(stories_manifest),
            'categories': sorted(list(all_categories)),
            'stories': stories_manifest
        }, lf, ensure_ascii=False, separators=(',', ':'))

    generate_pwa_manifest(web_dir)

    # Sync web assets to root directory for direct GitHub Pages support
    for folder in ['css', 'js', 'data', 'images']:
        src = os.path.join(web_dir, folder)
        if os.path.exists(src):
            shutil.copytree(src, folder, dirs_exist_ok=True)
    
    for f in ['index.html', 'manifest.json', 'sw.js']:
        src_f = os.path.join(web_dir, f)
        if os.path.exists(src_f):
            shutil.copy(src_f, f)

    print(f"\n[SUCCESS] Scalable Index generated for {len(stories_manifest)} stories in {library_file}")
    print("[SUCCESS] All minified web assets & PWA manifest synced to root directory for GitHub Pages.")

if __name__ == '__main__':
    build_all_library()
