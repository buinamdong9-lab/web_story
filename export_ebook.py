import os
import sys
import json
import argparse

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

def export_story_to_ebook(story_id='than_nu_tieu_dao_luc', format_type='md', output_file=None):
    """Exports all chapters of a story into a single unified Markdown/TXT/HTML eBook file"""
    story_dir = os.path.join('web', 'data', 'stories', story_id)
    if not os.path.exists(story_dir):
        story_dir = os.path.join('data', 'stories', story_id)

    if not os.path.exists(story_dir):
        print(f"[ERROR] Story '{story_id}' not found in library.")
        return False

    toc_file = os.path.join(story_dir, 'toc.json')
    chaps_dir = os.path.join(story_dir, 'chapters')

    with open(toc_file, 'r', encoding='utf-8') as tf:
        story_meta = json.load(tf)

    title = story_meta.get('title', 'Truyện')
    author = story_meta.get('author', 'Đang cập nhật')
    description = story_meta.get('description', '')
    chapters = story_meta.get('chapters', [])

    if not output_file:
        output_file = f"{story_id}_full.{format_type}"

    print(f"-> Exporting '{title}' ({len(chapters)} chapters) to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as out:
        if format_type == 'md':
            out.write(f"# {title}\n\n")
            out.write(f"**Tác giả**: {author}  \n")
            out.write(f"**Thể loại**: {story_meta.get('category', '')}  \n")
            out.write(f"**Tổng số chương**: {len(chapters)}  \n\n")
            out.write(f"## Giới thiệu\n{description}\n\n---\n\n")

            for chap in chapters:
                c_idx = chap.get('index')
                c_file = os.path.join(chaps_dir, f"{c_idx}.json")
                if os.path.exists(c_file):
                    with open(c_file, 'r', encoding='utf-8') as cf:
                        c_data = json.load(cf)
                        out.write(f"## {c_data.get('title')}\n\n")
                        out.write(f"{c_data.get('content')}\n\n---\n\n")

        elif format_type == 'txt':
            out.write(f"{title.upper()}\nTác giả: {author}\n\n{description}\n\n{'='*50}\n\n")
            for chap in chapters:
                c_idx = chap.get('index')
                c_file = os.path.join(chaps_dir, f"{c_idx}.json")
                if os.path.exists(c_file):
                    with open(c_file, 'r', encoding='utf-8') as cf:
                        c_data = json.load(cf)
                        out.write(f"\n{c_data.get('title')}\n\n")
                        out.write(f"{c_data.get('content')}\n\n{'-'*30}\n")

    print(f"[SUCCESS] Exported full story to: {output_file}")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Export story to unified Markdown or Text eBook")
    parser.add_argument('--id', default='than_nu_tieu_dao_luc', help="Story ID (e.g. than_nu_tieu_dao_luc)")
    parser.add_argument('--format', default='md', choices=['md', 'txt'], help="Output format (md or txt)")
    parser.add_argument('--out', help="Output filename")

    args = parser.parse_args()
    export_story_to_ebook(story_id=args.id, format_type=args.format, output_file=args.out)
