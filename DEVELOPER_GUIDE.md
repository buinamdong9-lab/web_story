# 📘 HƯỚNG DẪN KỸ THUẬT & TÀI LIỆU TOÀN DIỆN MÃ NGUỒN (DEVELOPER GUIDE & CODEBASE LOGS)

> **Mục đích tài liệu**: Dành cho bất kỳ lập trình viên nào (hoặc các phiên làm việc tiếp theo của AI) có thể đọc hiểu toàn bộ cấu trúc mã nguồn, luồng dữ liệu, các thuật toán cốt lõi và cách mở rộng/chỉnh sửa hệ thống một cách nhanh chóng, chính xác.

---

## 🗺️ 1. TỔNG QUAN HỆ THỐNG & TRIẾT LÝ THIẾT KẾ

Dự án **WebStory** là hệ thống xuất bản và đọc truyện PWA tĩnh (Static Single Page Application) kết hợp với các pipeline cào, xử lý và nén dữ liệu quy mô lớn (**1.906+ bộ truyện, 57.000+ chương, 109+ triệu từ**).

### Triết lý thiết kế cốt lõi:
1. **Serverless & Zero Hosting Cost**: Toàn bộ hệ thống chạy 100% trên **GitHub Pages** tĩnh, không cần Node.js backend hay cơ sở dữ liệu SQL đắt đỏ.
2. **High-Efficiency Data Partitioning**: Dữ liệu được chia nhỏ (sharding/partitioning) theo từng bộ truyện (`data/stories/{id}/`) và từng chương (`chapters/{index}.json`), giúp tải nhanh tức thì và không làm nghẽn RAM trình duyệt.
3. **4-Tier Caching Engine**:
   - **Tầng 1 (RAM LRU)**: Truy xuất ngay lập tức trong `Map()` với giới hạn 80 chương gần nhất.
   - **Tầng 2 (IndexedDB `webstory_db`)**: Lưu vĩnh viễn trên trình duyệt của người đọc (đọc offline hoàn toàn).
   - **Tầng 3 (Service Worker Cache v5)**: Tự động lưu cache HTTP tĩnh theo chiến lược Stale-While-Revalidate & Cache-First.
   - **Tầng 4 (HTTP Network Stream)**: Chỉ tải khi chưa có trong bộ nhớ đệm.
4. **GPU Layout Virtualization**: Sử dụng CSS `content-visibility: auto` giúp trình duyệt chỉ render các card trong viewport, giữ vững **60fps** trên hàng ngàn bộ truyện.
5. **Parallel Multiprocessing Toolkit**: Tận dụng tối đa sức mạnh phần cứng máy tính (16-20 CPU cores) để nén và xử lý dữ liệu hàng trăm ngàn file chỉ trong vài giây.

---

## 📂 2. CẤU TRÚC THƯ MỤC CHI TIẾT & TRÁCH NHIỆM FILE

```
d:\Crawl_Data/
├── web/                                # 🌐 Mã nguồn ứng dụng Frontend PWA
│   ├── index.html                      # Khung HTML ngữ nghĩa chuẩn SEO, Responsive
│   ├── css/
│   │   └── style.css                   # Glassmorphism, 5 Themes màu, CSS Virtualization, Scrubber
│   ├── js/
│   │   └── app.js                      # Core Frontend Logic (Router, Search, TTS, IndexedDB, Cache)
│   ├── sw.js                           # Service Worker điều khiển PWA Cache v5 Offline
│   ├── manifest.json                   # Cấu hình PWA để cài đặt Web App lên điện thoại/máy tính
│   ├── images/                         # Ảnh bìa truyện đã nén tối ưu (JPEG quality=80)
│   │   ├── cover.jpg                   # Ảnh bìa mặc định
│   │   ├── favicon.svg                 # Icon vector
│   │   └── {story_id}_cover.jpg        # Ảnh bìa riêng cho từng bộ truyện
│   └── data/
│       ├── stories.json                # Danh mục tóm tắt toàn bộ 1.906 truyện (~120KB)
│       └── stories/{story_id}/         # Dữ liệu phân vùng phục vụ Frontend
│           ├── metadata.json           # Thông tin tác giả, thể loại, mô tả
│           ├── toc.json                # Mục lục chương (TOC)
│           ├── cover.jpg               # File ảnh bìa
│           └── chapters/
│               ├── 1.json              # Payload chương 1: {index, title, content, word_count}
│               └── ...
│
├── data/                               # 🗄️ Master Partitioned Database (Cơ sở dữ liệu gốc)
│   ├── stories/{story_id}/             # Tương tự web/data/stories/{id}/ (kho lưu trữ trung tâm)
│   └── archives/                       # Lưu trữ các file dump thô, backup
│
├── scripts/                            # 🛠️ Bộ công cụ tự động hóa & Pipeline
│   ├── crawlers/                       # Các Crawler Engines
│   │   ├── hyper_crawler.py            # [Khuyên dùng] Engine cào siêu tốc AsyncIO TCP Pool
│   │   ├── eco_crawler.py              # Engine cào tiết kiệm băng thông tối đa
│   │   ├── turbo_crawler.py            # Engine cào đa luồng ThreadPool
│   │   ├── auto_crawler.py             # Engine cào lặp theo dõi truyện mới
│   │   └── crawl_truyenc.py            # Engine cào chuyên sâu TruyenC
│   ├── pipelines/                      # Các Pipeline xử lý dữ liệu & Triển khai
│   │   ├── build_library.py            # Quét và tạo file danh mục stories.json siêu tốc (0.5s)
│   │   ├── optimize_data.py            # Nén song song 16 nhân toàn bộ JSON và ảnh bìa
│   │   ├── health_check.py             # Quét kiểm tra toàn vẹn 100% dữ liệu (1.8s)
│   │   ├── deploy.py                   # Triển khai 1-click tự động lên GitHub Pages
│   │   └── export_ebook.py             # Xuất truyện thành file TXT/EPUB
│   └── legacy/                         # Nơi lưu trữ các file test cũ, bản nháp
│
├── build_library.py                    # Root Proxy -> scripts/pipelines/build_library.py
├── optimize_data.py                    # Root Proxy -> scripts/pipelines/optimize_data.py
├── health_check.py                     # Root Proxy -> scripts/pipelines/health_check.py
├── deploy.py                           # Root Proxy -> scripts/pipelines/deploy.py
├── ARCHITECTURE.md                     # Báo cáo kiến trúc hệ thống
├── CHANGELOG.md                        # Lịch sử phiên bản & thay đổi
├── DEVELOPER_GUIDE.md                  # [File này] Hướng dẫn bảo trì & phát triển mã nguồn
└── README.md                           # Hướng dẫn sử dụng nhanh cho người dùng
```

---

## 🧩 3. CẤU TRÚC DỮ LIỆU & JSON SCHEMAS

### A. Danh mục toàn bộ truyện (`web/data/stories.json`)
File này được tải 1 lần khi người dùng mở trang chủ. Định dạng cực kỳ tinh gọn:
```json
{
  "updated_at": "2026-08-28",
  "total_stories": 1906,
  "categories": ["Cạnh Kỹ", "Dị Năng", "Đô Thị", "Huyền Huyễn", "Khoa Huyễn", "Lịch Sử", "Ngôn Tình", "Tiên Hiệp", "Xuyên Không"],
  "stories": [
    {
      "id": "than_nu_tieu_dao_luc",
      "title": "Thần Nữ Tiêu Dao Lục",
      "author": "Vô Danh",
      "category": "Tiên Hiệp, Huyền Huyễn, Tu Chân, Sắc Hiệp",
      "status": "Hoàn Thành",
      "description": "Bộ truyện hấp dẫn với nhiều tình tiết đặc sắc...",
      "cover_image": "images/than_nu_tieu_dao_luc_cover.jpg",
      "total_chapters": 140,
      "total_words": 159938
    }
  ]
}
```

### B. Mục lục chương (`data/stories/{id}/toc.json`)
Được tải khi người dùng click vào một truyện cụ thể:
```json
{
  "id": "than_nu_tieu_dao_luc",
  "title": "Thần Nữ Tiêu Dao Lục",
  "author": "Vô Danh",
  "category": "Tiên Hiệp, Huyền Huyễn",
  "status": "Hoàn Thành",
  "description": "Nội dung tóm tắt chi tiết...",
  "cover_image": "images/than_nu_tieu_dao_luc_cover.jpg",
  "total_chapters": 140,
  "total_words": 159938,
  "chapters": [
    {
      "index": 1,
      "title": "Chương 1: Khởi đầu tiêu dao",
      "word_count": 1250
    }
  ]
}
```

### C. File từng chương (`data/stories/{id}/chapters/{index}.json`)
Được tải theo yêu cầu khi người dùng đọc đến chương tương ứng:
```json
{
  "index": 1,
  "title": "Chương 1: Khởi đầu tiêu dao",
  "content": "Nội dung chương truyện được làm sạch hoàn toàn...",
  "word_count": 1250
}
```

---

## 💻 4. KIẾN TRÚC FRONTEND (`web/js/app.js`)

### A. Quản Lý Trạng Thái (Application State)
`app.js` được bao bọc trong một IIFE `(function() { ... })();` tránh xung đột biến toàn cục. Đối tượng `state` quản lý:
- `state.stories`: Mảng 1.906 bộ truyện từ `stories.json`.
- `state.chapterCache`: `Map()` chứa tối đa 80 chương đọc gần nhất (LRU).
- `state.settings`: Theme, font, font-size lưu trong `localStorage`.
- `state.tts`: SpeechSynthesis engine, danh sách giọng đọc, trạng thái phát, chỉ số đoạn văn đang đọc.

### B. Thuật Toán Tìm Kiếm Tiếng Việt Thông Minh
- **Hàm `normalizeSearchText(str)`**:
  Loại bỏ toàn bộ dấu thanh và ký tự đặc biệt trong tiếng Việt (`á, à, ả, ã, ạ, â, ă, đ` $\to$ `a, d`).
- **Cache Token**:
  Mỗi story được tự động gán các trường `_normTitle`, `_normAuthor`, `_normCategory`, `_normDesc` sau khi tải danh mục để không phải chạy regex nhiều lần khi người dùng gõ phím.
- **Hàm `highlightMatches(text, query)`**:
  Sử dụng RegExp với flag `gi` để bao bọc các từ khóa tìm kiếm bằng thẻ `<mark class="search-highlight">` giúp người dùng nhận diện kết quả tức thì.

### C. Bộ Máy Đọc Âm Thanh AI TTS (`state.tts`)
- Sử dụng **Web Speech API** (`window.speechSynthesis`, `SpeechSynthesisUtterance`).
- Chia nhỏ nội dung chương thành các đoạn văn (`paragraphs`) để tránh lỗi ngắt giọng trên các trình duyệt Chromium khi phát nội dung dài.
- Tích hợp **Audio Scrubber Bar** cho phép tua trực tiếp đến bất kỳ đoạn văn nào trong chương.
- Hỗ trợ **MediaSession API** (phím điều khiển tai nghe / màn hình khóa) và **WakeLock API** (ngăn tắt màn hình khi đang đọc/nghe).

---

## ⚙️ 5. PIPELINE XỬ LÝ & BẢO TRÌ

### 1. Kiểm tra toàn vẹn hệ thống (`python health_check.py`)
- **Tập lệnh**: `scripts/pipelines/health_check.py`
- **Chức năng**: Quét nhanh 1.906 truyện, kiểm tra xem có chương nào bị thiếu file JSON, lỗi cú pháp hoặc mất ảnh bìa không.
- **Thời gian chạy**: ~1.8 giây.

### 2. Xây dựng lại danh mục (`python build_library.py`)
- **Tập lệnh**: `scripts/pipelines/build_library.py`
- **Chức năng**:
  1. Đọc cache `.build_cache.json` để chỉ xử lý các truyện có thay đổi (Incremental Build).
  2. Tạo file `web/data/stories.json` rút gọn (~120KB).
  3. Cập nhật `manifest.json` và đồng bộ file tĩnh lên thư mục gốc.
- **Thời gian chạy**: ~0.53 giây.

### 3. Nén dữ liệu đa nhân (`python optimize_data.py`)
- **Tập lệnh**: `scripts/pipelines/optimize_data.py`
- **Chức năng**:
  1. Nén ảnh bìa với PIL (JPEG quality=80, progressive).
  2. Khởi tạo `multiprocessing.Pool(16)` để nén và loại bỏ khoảng trắng thừa trên toàn bộ 114.706 file JSON chương truyện.
- **Thời gian chạy**: ~5 giây.

### 4. Xuất bản lên GitHub (`python deploy.py "commit message"`)
- **Tập lệnh**: `scripts/pipelines/deploy.py`
- **Chức năng**: Chạy tự động chuỗi 3 bước: `build_library` $\to$ `health_check` $\to$ `git commit & push` lên nhánh `main`.

---

## 🛠️ 6. HƯỚNG DẪN MỞ RỘNG (HOW-TO GUIDE)

### Làm sao để thêm một bộ truyện mới thủ công?
1. Tạo thư mục `data/stories/{story_slug}/`
2. Tạo file `metadata.json`:
   ```json
   {
     "title": "Tên Truyện Mới",
     "author": "Tên Tác Giả",
     "category": "Tiên Hiệp",
     "status": "Hoàn Thành",
     "description": "Mô tả truyện..."
   }
   ```
3. Đặt các chương vào `data/stories/{story_slug}/chapters/{index}.json`:
   ```json
   {
     "index": 1,
     "title": "Chương 1: Mở đầu",
     "content": "Nội dung chương truyện...",
     "word_count": 1500
   }
   ```
4. Đặt ảnh bìa vào `data/stories/{story_slug}/cover.jpg` (nếu có).
5. Chạy:
   ```bash
   python build_library.py
   python deploy.py "feat: them truyen moi"
   ```

### Làm sao để thêm Theme màu mới vào Web Reader?
1. Mở `web/css/style.css`.
2. Định nghĩa class theme mới, ví dụ:
   ```css
   .theme-midnight {
     --bg-main: #0a0e1a;
     --bg-card: #121829;
     --bg-header: rgba(10, 14, 26, 0.85);
     --text-main: #cbd5e1;
     --text-heading: #f8fafc;
     --accent-color: #38bdf8;
   }
   ```
3. Mở `web/index.html` và thêm nút chọn theme tương ứng vào phần Settings Drawer.
4. Chạy `python deploy.py "feat: add midnight theme"`.
