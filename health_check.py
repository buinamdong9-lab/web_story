import os
import sys
import json

# Ensure utf-8 stdout
if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

def run_health_check():
    """Validates library data integrity, chapter sequence, and assets"""
    print("==================================================")
    print("       WEB STORY LIBRARY HEALTH CHECK ENGINE      ")
    print("==================================================")

    stories_json_path = os.path.join('web', 'data', 'stories.json')
    if not os.path.exists(stories_json_path):
        stories_json_path = os.path.join('data', 'stories.json')

    if not os.path.exists(stories_json_path):
        print(f"[ERROR] Stories manifest not found: {stories_json_path}")
        return False

    with open(stories_json_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    stories = manifest.get('stories', [])
    print(f"-> Total registered stories: {len(stories)}")

    all_passed = True
    total_words_all = 0
    total_chaps_all = 0

    for story in stories:
        sid = story.get('id')
        title = story.get('title')
        print(f"\n[STORY] {title} (ID: {sid})")

        story_dir = os.path.join('web', 'data', 'stories', sid)
        if not os.path.exists(story_dir):
            story_dir = os.path.join('data', 'stories', sid)

        toc_file = os.path.join(story_dir, 'toc.json')
        chaps_dir = os.path.join(story_dir, 'chapters')

        if not os.path.exists(toc_file):
            print(f"  [FAIL] Missing TOC file: {toc_file}")
            all_passed = False
            continue

        with open(toc_file, 'r', encoding='utf-8') as tf:
            toc_data = json.load(tf)

        chapters = toc_data.get('chapters', [])
        total_chaps = len(chapters)
        total_chaps_all += total_chaps

        # Check chapter files integrity
        missing_chaps = []
        corrupted_chaps = []
        story_words = 0

        for chap_meta in chapters:
            c_idx = chap_meta.get('index')
            c_file = os.path.join(chaps_dir, f"{c_idx}.json")
            if not os.path.exists(c_file):
                missing_chaps.append(c_idx)
            else:
                try:
                    with open(c_file, 'r', encoding='utf-8') as cf:
                        c_data = json.load(cf)
                        story_words += c_data.get('word_count', 0)
                except Exception:
                    corrupted_chaps.append(c_idx)

        total_words_all += story_words

        if missing_chaps:
            print(f"  [FAIL] Missing chapter files: {missing_chaps[:5]}...")
            all_passed = False
        elif corrupted_chaps:
            print(f"  [FAIL] Corrupted chapter files: {corrupted_chaps[:5]}...")
            all_passed = False
        else:
            print(f"  [PASS] All {total_chaps} chapters verified ({story_words:,} words).")

        # Check Cover Image
        cover_path = os.path.join('web', story.get('cover_image', 'images/cover.jpg'))
        if not os.path.exists(cover_path):
            cover_path = story.get('cover_image', 'images/cover.jpg')

        if os.path.exists(cover_path):
            print(f"  [PASS] Cover image found: {cover_path}")
        else:
            print(f"  [WARN] Cover image not found: {cover_path} (Using default fallback)")

    print("\n--------------------------------------------------")
    print(f"Summary: {len(stories)} Stories | {total_chaps_all:,} Chapters | {total_words_all:,} Words")
    
    if all_passed:
        print("[SUCCESS] All data integrity checks PASSED! System ready for production.")
    else:
        print("[WARNING] Health check encountered issues. Please inspect the log above.")

    return all_passed

if __name__ == '__main__':
    run_health_check()
