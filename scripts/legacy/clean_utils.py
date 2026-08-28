import re

def clean_chapter_title(raw_title: str, story_title: str = "") -> str:
    """
    Làm sạch tiêu đề chương:
    - Loại bỏ thẻ VIP, status: [VIP Khóa], [Công khai], [VIP]
    - Loại bỏ tên trang web suffix (e.g. - TruyenC, - AkayTruyen, - TruyenFull)
    - Loại bỏ tên bộ truyện prefix (e.g. Thần Nữ Tiêu Dao Lục (NTR) - )
    - Chỉ giữ lại tên/thứ tự chương gọn gàng (e.g. Chương 1: Dấy Sóng Gió, Tựa: Thiên Cơ)
    """
    if not raw_title:
        return ""

    title = raw_title.strip()

    # 1. Loại bỏ các thẻ vuông, thẻ nhạy cảm như [VIP Khóa], [Công khai], [VIP], (NTR)
    title = re.sub(r'^\[.*?\]\s*', '', title)
    title = re.sub(r'\s*\(\s*NTR\s*\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\bNTR\b', '', title, flags=re.IGNORECASE)

    # 2. Loại bỏ tên website ở cuối (ví dụ: " - TruyenC", " - AkayTruyen", " - TruyenFull", " | TruyenC")
    title = re.sub(
        r'\s*[-|]\s*([A-Za-z0-9]+(?:\.[a-z]{2,})?|TruyenC|AkayTruyen|TruyenFull|TruyenCV|Wikidich|TangThuVien|Metruyenchu|STruyen|TruyenHD)\s*$',
        '',
        title,
        flags=re.IGNORECASE
    )

    # 3. Nếu truyền vào story_title, loại bỏ prefix tên truyện
    if story_title:
        escaped_story = re.escape(story_title.strip())
        title = re.sub(rf'^{escaped_story}\s*[-|:]\s*', '', title, flags=re.IGNORECASE)

    # 4. Tìm vị trí chương: Ưu tiên "Chương <số>", "Tựa", "Hồi <số>", "Quyển <số>", "Tiết <số>", "Phần <số>"
    chap_match = re.search(
        r'((?:Chương\s*\d+.*|Tựa:?.*|Hồi\s*\d+.*|Quyển\s*\d+.*|Tiết\s*\d+.*|Phần\s*\d+.*))$',
        title,
        flags=re.IGNORECASE
    )
    if not chap_match:
        # Nhánh fallback cho "Chương", "Mở đầu", v.v. không chứa số
        chap_match = re.search(
            r'((?:Chương|Tựa|Hồi|Quyển|Tiết|Phần|Mở đầu).*)$',
            title,
            flags=re.IGNORECASE
        )

    if chap_match:
        title = chap_match.group(1).strip()
    else:
        # Nếu tiêu đề dạng "Tên Truyện - Tên Chương"
        if " - " in title:
            parts = title.split(" - ")
            if len(parts) >= 2:
                title = parts[-1].strip()

    return title.strip()


def format_chapter_markdown(title: str, content: str, chap_idx: int = None) -> str:
    """
    Tạo định dạng markdown sạch cho một chương, hỗ trợ anchor link.
    """
    anchor = f'<a id="chuong-{chap_idx}"></a>\n' if chap_idx is not None else ""
    return f"{anchor}## {title.strip()}\n\n{content.strip()}\n\n---\n\n"


def generate_story_markdown(story_title: str, chapters: list[dict]) -> str:
    """
    Tạo tệp Markdown hoàn chỉnh với Mục Lục (TOC) liên kết và cấu trúc Outline chuẩn cho người đọc.
    """
    md = []
    md.append(f"# {story_title.strip()}\n")
    md.append(f"> **Tổng số chương:** {len(chapters)} chương  ")
    md.append(f"> **Định dạng:** Markdown Reader với Mục Lục Tự Động  \n")
    md.append("---\n")
    md.append("## 📌 MỤC LỤC\n")

    # Tạo danh sách Mục Lục với link neo
    for idx, item in enumerate(chapters):
        if "error" in item:
            chap_num = item.get("chapter", item.get("index", idx + 1))
            md.append(f"- [Chương {chap_num}: Lỗi](#chuong-{idx})")
        else:
            title = item.get("title", f"Chương {idx + 1}")
            md.append(f"- [{title}](#chuong-{idx})")

    md.append("\n---\n")

    # Tạo nội dung từng chương với heading level 2 (##) để hiển thị cây Outline
    for idx, item in enumerate(chapters):
        md.append(f'<a id="chuong-{idx}"></a>\n')
        if "error" in item:
            chap_num = item.get("chapter", item.get("index", idx + 1))
            md.append(f"## Chương {chap_num}: Lỗi - {item['error']}\n\n")
        else:
            title = item.get("title", f"Chương {idx + 1}")
            content = item.get("content", "").strip()
            md.append(f"## {title}\n\n{content}\n\n---\n")

    return "\n".join(md)


