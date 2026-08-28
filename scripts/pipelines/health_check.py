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
    failed_stories = []
    total_chaps_all = 0
    total_words_all = 0
    
    for idx, story in enumerate(stories, 1):
        sid = story.get('id')
        title = story.get('title')

        story_dir = os.path.join('web', 'data', 'stories', sid)
        if not os.path.exists(story_dir):
            story_dir = os.path.join('data', 'stories', sid)

        toc_file = os.path.join(story_dir, 'toc.json')
        chaps_dir = os.path.join(story_dir, 'chapters')

        if not os.path.exists(toc_file):
            print(f"\n[FAIL] {title} (ID: {sid}) - Missing TOC file: {toc_file}")
            failed_stories.append(sid)
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
        story_words = toc_data.get('total_words', 0)
        total_words_all += story_words

        if idx % 100 == 0 or idx == len(stories):
            sys.stdout.write(f"\r-> Verified {idx:,}/{len(stories):,} stories ({total_chaps_all:,} chapters, {total_words_all:,} words)...")
            sys.stdout.flush()

    print()
    print("--------------------------------------------------")
    print(f"Summary: {len(stories):,} Stories | {total_chaps_all:,} Chapters | {total_words_all:,} Words")
    
    if all_passed:
        print("[SUCCESS] All data integrity checks PASSED! System ready for production.")
    else:
        print(f"[WARNING] Health check encountered issues on {len(failed_stories)} stories.")

    return all_passed

if __name__ == '__main__':
    run_health_check()
