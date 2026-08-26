import os
import json
import shutil

def export_data():
    source_json = 'Than_Nu_Tieu_Dao_Luc.json'
    web_dir = 'web'
    data_dir = os.path.join(web_dir, 'data')
    chapters_dir = os.path.join(data_dir, 'chapters')
    img_dir = os.path.join(web_dir, 'images')

    os.makedirs(chapters_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    if not os.path.exists(source_json):
        print(f"Error: {source_json} not found.")
        return

    with open(source_json, 'r', encoding='utf-8') as f:
        chapters = json.load(f)

    toc = []
    total_words = 0

    for item in chapters:
        idx = item.get('index')
        title = item.get('title', f'Chương {idx}')
        content = item.get('content', '')
        char_count = len(content)
        word_count = len(content.split())
        total_words += word_count

        # Save TOC entry
        toc.append({
            'index': idx,
            'title': title,
            'char_count': char_count,
            'word_count': word_count
        })

        # Save individual chapter JSON
        chap_file = os.path.join(chapters_dir, f"{idx}.json")
        with open(chap_file, 'w', encoding='utf-8') as cf:
            json.dump({
                'index': idx,
                'title': title,
                'content': content,
                'word_count': word_count,
                'char_count': char_count
            }, cf, ensure_ascii=False, indent=2)

    # Save TOC JSON
    toc_file = os.path.join(data_dir, 'toc.json')
    with open(toc_file, 'w', encoding='utf-8') as tf:
        json.dump({
            'story_title': 'Thần Nữ Tiêu Dao Lục',
            'story_original_title': '神女逍遥录',
            'author': 'Vô Danh',
            'category': 'Tiên Hiệp, Huyền Huyễn, Tu Chân, Hậu Cung, Sắc Hiệp',
            'status': 'Hoàn Thành',
            'total_chapters': len(toc),
            'total_words': total_words,
            'chapters': toc
        }, tf, ensure_ascii=False, indent=2)

    print(f"Successfully exported {len(toc)} chapters ({total_words} words) to {data_dir}")

    # Copy cover image if available in brain directory
    cover_artifact = r'C:\Users\DONGTTNT\.gemini\antigravity-ide\brain\e21e1fc3-75ce-42f7-92fa-fea77708768e\than_nu_cover_1787731152238.jpg'
    target_cover = os.path.join(img_dir, 'cover.jpg')
    if os.path.exists(cover_artifact):
        shutil.copy(cover_artifact, target_cover)
        print(f"Copied cover image to {target_cover}")

if __name__ == '__main__':
    export_data()
