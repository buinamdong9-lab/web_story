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
3. Mở `web/index.html` và thêm nút chọn theme tương ứng vào phần Settings Drawer:
   ```html
   <button class="theme-btn theme-midnight-btn" data-theme="theme-midnight">Midnight</button>
   ```
4. Chạy `python deploy.py "feat: add midnight theme"`.

---

## 🎨 7. HƯỚNG DẪN CHI TIẾT PHÁT TRIỂN & THÊM CHỨC NĂNG MỚI TRÊN GIAO DIỆN (FRONTEND UI/UX MANUAL)

Phần này hướng dẫn từng bước kỹ lưỡng khi bạn muốn thêm bất kỳ nút bấm, menu, thanh công cụ, hiệu ứng hoạt ảnh hay tính năng tương tác mới nào vào giao diện đọc truyện.

### A. Kiến Trúc Vòng Đời Router Frontend (SPA Architecture)
Giao diện hoạt động theo mô hình **Single Page Application (SPA)** điều hướng bằng **URL Hash** (`window.location.hash`):
- `#` hoặc `""`: Chế độ **Trang Chủ / Thư Viện** (`#viewLibrary`).
- `#story/{story_id}`: Chế độ **Trang Chi Tiết Bộ Truyện & Mục Lục** (`#viewStoryDetail`).
- `#read/{story_id}/{chapter_index}`: Chế độ **Đọc & Nghe Âm Thanh Chương Truyện** (`#viewReader`).

Mỗi khi hash thay đổi, hàm `handleHashChange()` trong `web/js/app.js` được kích hoạt $\to$ gọi `switchView(viewName)` để ẩn/hiện các container DOM và gọi hàm render tương ứng (`loadStoryTOC()` hoặc `loadChapter()`).

---

### B. QUY TRÌNH 4 BƯỚC CHUẨN ĐỂ THÊM MỘT TÍNH NĂNG GIAO DIỆN MỚI

#### Bước 1: Khai Báo HTML Cấu Trúc (`web/index.html`)
Xác định vị trí component mới của bạn nằm ở đâu trong giao diện:
- **Thanh Header trên cùng**: `<header class="app-header">` (nút tìm kiếm, nút cài đặt, logo).
- **Thanh Công Cụ Đọc Truyện**: `<div class="reader-floating-bar">` hoặc `<div class="reader-controls">`.
- **Thanh Tua Âm Thanh / Audio Bar**: `<div class="audio-panel">` & `<div class="scrubber-container">`.
- **Drawer / Menu Trượt Cài Đặt**: `<div id="settingsDrawer" class="drawer">`.
- **Modal / Hộp Thoại Nổi**: `<div id="myModal" class="modal-overlay hidden">`.

> ⚠️ **Quy tắc HTML**: Luôn đặt `id` rõ ràng và duy nhất (ví dụ `id="btnSleepTimer"`), sử dụng thẻ ngữ nghĩa (`<button>`, `<section>`, `<dialog>`), thêm `aria-label` và `title` để hỗ trợ trợ năng (Accessibility).

#### Bước 2: Viết CSS Glassmorphism & Tương Thích 5 Themes (`web/css/style.css`)
> ⚠️ **Quy tắc CSS tối thượng**: **KHÔNG BAO GIỜ** dùng mã màu cố định như `#ffffff`, `#000000`, `black`, `white` cho chữ và nền component. **LUÔN DÙNG** biến CSS (CSS Variables) để giao diện tự động đẹp trên cả 5 Themes (Dark, OLED Black, Sepia, Cream, Emerald):

```css
/* Các biến CSS chuẩn hệ thống có sẵn */
--bg-main            /* Màu nền chính trang */
--bg-card            /* Màu nền thẻ card / modal */
--bg-header          /* Màu nền mờ thanh header (Glassmorphism) */
--text-main          /* Màu chữ nội dung chính */
--text-heading       /* Màu chữ tiêu đề */
--text-muted         /* Màu chữ phụ, mờ */
--accent-color       /* Màu tím/xanh thương hiệu nổi bật */
--border-color       /* Màu đường viền khung */
--radius-md          /* Bo góc chuẩn (12px) */
--shadow-card        /* Hiệu ứng đổ bóng nổi */
--shadow-glow        /* Hiệu ứng hào quang neon khi hover */
--transition-fast    /* Chuyển động mượt (0.15s ease) */
```

**Ví dụ viết Style chuẩn cho một Component mới:**
```css
.my-custom-box {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-main);
  padding: 16px;
  backdrop-filter: blur(12px); /* Hiệu ứng Glassmorphism */
  box-shadow: var(--shadow-card);
  transition: all var(--transition-fast);
}

.my-custom-box:hover {
  border-color: var(--accent-color);
  box-shadow: var(--shadow-card), var(--shadow-glow);
  transform: translateY(-2px);
}
```

#### Bước 3: Đăng Ký Biến DOM & Khởi Tạo Trạng Thái (`web/js/app.js`)
1. Thêm selector vào đối tượng `DOM` ở đầu file `app.js`:
   ```javascript
   const DOM = {
     // ... các selector cũ
     btnSleepTimer: document.getElementById('btnSleepTimer'),
     sleepTimerModal: document.getElementById('sleepTimerModal'),
     sleepTimerDisplay: document.getElementById('sleepTimerDisplay')
   };
   ```
2. Khai báo biến lưu trữ trong đối tượng `state`:
   ```javascript
   const state = {
     // ... state cũ
     sleepTimer: {
       timerId: null,
       remainingSeconds: 0,
       isEnabled: false
     }
   };
   ```
3. Đọc dữ liệu đã lưu từ `localStorage` nếu là cài đặt cá nhân:
   ```javascript
   state.userCustomSetting = localStorage.getItem('tn_custom_setting') || 'default_value';
   ```

#### Bước 4: Viết Event Listener & Logic Xử Lý
1. Viết hàm xử lý logic (Handler Function):
   ```javascript
   function startSleepTimer(minutes) {
     if (state.sleepTimer.timerId) clearInterval(state.sleepTimer.timerId);
     
     state.sleepTimer.remainingSeconds = minutes * 60;
     state.sleepTimer.isEnabled = true;
     
     state.sleepTimer.timerId = setInterval(() => {
       state.sleepTimer.remainingSeconds--;
       updateTimerUI();
       
       if (state.sleepTimer.remainingSeconds <= 0) {
         clearInterval(state.sleepTimer.timerId);
         stopTTS(); // Dừng phát giọng đọc khi hết giờ
         showToast('⏰ Đã dừng phát theo hẹn giờ.');
       }
     }, 1000);
   }
   ```
2. Gắn sự kiện trong hàm `bindEvents()` của `app.js`:
   ```javascript
   function bindEvents() {
     // ... các event cũ
     if (DOM.btnSleepTimer) {
       DOM.btnSleepTimer.addEventListener('click', () => {
         openSleepTimerModal();
       });
     }
   }
   ```

---

### 💡 C. 3 VÍ DỤ THỰC CHIẾN MẪU ĐỂ ÁP DỤNG NGAY

---

#### 🌟 Ví Dụ 1: Thêm Chức Năng "Đếm Thời Gian Hẹn Giờ Tự Tắt Khi Nghe Audio (Sleep Timer)"

1. **HTML (`web/index.html`)**: Thêm nút hẹn giờ vào cụm điều khiển âm thanh:
   ```html
   <button id="btnSleepTimer" class="icon-btn" title="Hẹn giờ tắt audio">
     <span>⏱️</span>
   </button>
   ```
2. **CSS (`web/css/style.css`)**:
   ```css
   .timer-badge {
     font-size: 0.75rem;
     background: var(--accent-color);
     color: #fff;
     padding: 2px 6px;
     border-radius: 10px;
     margin-left: 4px;
   }
   ```
3. **JS (`web/js/app.js`)**:
   - Khi bấm vào nút, hiển thị danh sách chọn: `15 phút`, `30 phút`, `45 phút`, `Hết chương này`.
   - Khi hết thời gian $\to$ gọi `pauseTTS()` hoặc `stopTTS()` và giải phóng `wakeLock`.

---

#### 🌟 Ví Dụ 2: Thêm "Chế Độ Đọc Hai Cột Dạng Trang Sách (Dual-Column Book Mode)"

1. **HTML (`web/index.html`)**: Thêm nút gạt chế độ đọc 2 cột trong Settings Drawer:
   ```html
   <div class="setting-item">
     <span>Chế độ 2 cột (Dạng sách):</span>
     <input type="checkbox" id="chkDualColumn">
   </div>
   ```
2. **CSS (`web/css/style.css`)**:
   ```css
   .reader-body.dual-column {
     column-count: 2;
     column-gap: 48px;
     column-rule: 1px solid var(--border-color);
     text-align: justify;
   }
   
   @media (max-width: 900px) {
     /* Tự động về 1 cột trên màn hình điện thoại/tablet nhỏ */
     .reader-body.dual-column {
       column-count: 1;
     }
   }
   ```
3. **JS (`web/js/app.js`)**:
   ```javascript
   DOM.chkDualColumn.addEventListener('change', (e) => {
     const isDual = e.target.checked;
     DOM.readerBody.classList.toggle('dual-column', isDual);
     localStorage.setItem('tn_dual_column', isDual ? 'true' : 'false');
   });
   ```

---

#### 🌟 Ví Dụ 3: Thêm "Công Cụ Đánh Dấu / Highlight Đoạn Văn Hay (Text Highlight & Notes)"

1. **JS (`web/js/app.js`)**: Lắng nghe sự kiện bôi đen chữ của người dùng:
   ```javascript
   DOM.readerBody.addEventListener('mouseup', () => {
     const selection = window.getSelection();
     const selectedText = selection.toString().trim();
     if (selectedText.length > 5) {
       showFloatingHighlightToolbar(selection);
     }
   });
   ```
2. Lưu các đoạn trích dẫn vào `IndexedDB` hoặc `localStorage` theo khóa `{storyId}_{chapterIndex}_highlights`.
3. Khi nạp chương đọc $\to$ tự động bọc thẻ `<mark class="user-highlight">` vào nội dung tương ứng.

---

### 📋 D. QUY TRÌNH KIỂM THỬ & DEPLOY TÍNH NĂNG MỚI LÊN LIVE

1. **Kiểm thử cục bộ trên máy tính**:
   Khởi chạy server tĩnh tại thư mục `web/`:
   ```bash
   python -m http.server 8000 -d web
   ```
   Mở trình duyệt truy cập: `http://localhost:8000/` để thử nghiệm UI và kiểm tra Console xem có lỗi JavaScript nào không.

2. **Cập nhật phiên bản Cache PWA (`web/sw.js`)**:
   Khi sửa đổi file `app.js` hoặc `style.css`, tăng phiên bản cache lên 1 số (ví dụ: `v5` $\to$ `v6`) để tất cả người dùng cũ tự động nhận giao diện mới nhất:
   ```javascript
   const CACHE_NAME = 'webstory-cache-v6';
   ```

3. **Xuất bản tự động lên GitHub Pages**:
   Chạy lệnh:
   ```bash
   python deploy.py "feat: add sleep timer and dual column reading mode"
   ```
   Lệnh này sẽ tự động build lại manifest, kiểm tra tính toàn vẹn 100% dữ liệu và push thẳng lên GitHub Pages! 🚀

