# 📚 Nền Tảng Thư Viện Web Đọc Truyện & Nghe Audio Tự Động (Multi-Story Library & TTS Engine)

> **Live Demo**: [https://buinamdong9-lab.github.io/web_story/](https://buinamdong9-lab.github.io/web_story/)  
> **GitHub Repository**: [https://github.com/buinamdong9-lab/web_story](https://github.com/buinamdong9-lab/web_story)

---

## 📖 1. TỔNG QUAN HỆ THỐNG
Dự án là nền tảng web tĩnh đọc truyện chữ và nghe audio AI tốc độ cao, hỗ trợ đa bộ truyện (Multi-Story Library Engine) có thể mở rộng không giới hạn các bộ truyện mới được crawl, hỗ trợ PWA đọc offline và tối ưu chuyên sâu cho cả máy tính và điện thoại di động (iOS & Android).

---

## 🗂️ 2. BẢN ĐỒ CẤU TRÚC MÃ NGUỒN & TỆP TIN

```text
├── index.html                 # Giao diện chính của ứng dụng (SPA 3 tầng: Library, Overview, Reader)
├── manifest.json              # File cấu hình Progressive Web App (PWA) cài đặt ra màn hình chính
├── sw.js                      # Service Worker xử lý bộ nhớ đệm Stale-While-Revalidate & đọc Offline
├── css/
│   └── style.css              # Hệ thống CSS Tokens, 5 bộ Theme, Scrubber Bar, Layout Responsive
├── js/
│   └── app.js                 # Bộ máy JavaScript điều khiển Router, TTS Engine, LRU Cache, WakeLock
├── images/
│   ├── cover.jpg              # Ảnh bìa mặc định
│   └── than_nu_tieu_dao_luc_cover.jpg # Ảnh bìa nghệ thuật truyện Thần Nữ Tiêu Dao Lục
├── data/
│   ├── stories.json           # Danh mục tổng hợp tất cả truyện trong thư viện (Minified JSON)
│   ├── toc.json               # Mục lục truyện mặc định
│   └── stories/               # Thư mục dữ liệu phân tách theo từng bộ truyện
│       └── than_nu_tieu_dao_luc/
│           ├── toc.json       # Mục lục riêng của truyện
│           └── chapters/      # 102 file chương độc lập (1.json -> 102.json)
│
├── deploy.py                  # 🚀 1-CLICK DEPLOY: Tự động Build, Health Check và Push GitHub
├── build_library.py           # SCRIPT TỰ ĐỘNG: Quét truyện, nén JSON, sinh PWA manifest & sync root
├── add_story.py               # SCRIPT NHẬP TRUYỆN: Làm sạch text, gán metadata và nhập vào thư viện
├── health_check.py            # SCRIPT KIỂM TRA: Quét tính toàn vẹn của dữ liệu và các chương
├── export_ebook.py            # SCRIPT XUẤT EBOOK: Gộp toàn bộ truyện thành file Markdown / TXT duy nhất
├── clean_utils.py             # Bộ công cụ lọc và làm sạch văn bản rác khi crawl truyện
└── web/                       # Thư mục chứa web assets gốc (tự động đồng bộ ra root)
```

---

## ⚡ 3. CÁC TỐI ƯU & TÍNH NĂNG ĐÃ NÂNG CẤP

### 🎧 A. Đọc Giọng Nói Tự Động (Multi-Voice TTS Engine & Scrubber)
- **Đa dạng giọng đọc**: Tự động nhận diện và kết nối với giọng tiếng Việt trên từng hệ điều hành:
  - **iOS (iPhone/iPad)**: Siri Tiếng Việt / Linh (Apple Voice).
  - **Android (Samsung, Xiaomi...)**: Google Tiếng Việt chuẩn ngữ điệu.
  - **Windows / Web**: Microsoft Hoài Mỹ, Nam Minh Neural Online.
- **Thanh tua tiến trình (Audio Scrubber Bar)**: Kéo trượt để tua nhanh đến bất kỳ đoạn văn nào trong chương.
- **Click-to-Seek**: Nhấp trực tiếp vào bất kỳ đoạn văn nào trên màn hình để giọng đọc phát ngay từ đoạn đó.
- **Tùy biến âm thanh**: Điều chỉnh cao độ tông giọng (Pitch: Trầm ấm, Chuẩn, Trong trẻo), Tốc độ đọc (0.8x - 2.0x), và các bộ Preset phong cách.

### 📱 B. Tối Ưu Chuyên Sâu Cho Di Động (iOS Safari & Android Chrome)
- **Screen Wake Lock API**: Tự động giữ màn hình điện thoại luôn sáng khi đang nghe truyện, **không bị khóa màn hình tự động làm tắt tiếng**.
- **MediaSession API Widget**: Hiển thị tên truyện, tên chương và ảnh bìa trên **Màn hình khóa / Control Center**, cho phép bấm Play/Pause/Next ngay trên màn hình khóa.
- **Watchdog Auto-Advance**: Bộ đếm thời gian thông minh khắc phục triệt để lỗi ngắt giọng ở đoạn văn dài của trình duyệt di động, tự động nối tiếp các đoạn văn liên tục.
- **Touch Warmup**: Vượt qua rào cản phân quyền âm thanh của Apple Safari ngay từ cú chạm đầu tiên.

### 📚 C. Kiến Trúc Thư Viện Đa Truyện (Multi-Story Library Engine)
- **Trang chủ Tủ Sách (`#library`)**: Lưới hiển thị toàn bộ các bộ truyện kèm bìa, số chương, tác giả, thể loại và tìm kiếm tức thì.
- **Kệ sách "Đang Đọc Dở" (Recent Shelf)**: Tự động ghi nhớ tiến độ riêng biệt của từng bộ truyện để người dùng quay lại đọc tiếp ngay.
- **Hệ thống URL Hash Router**:
  - `#library`: Danh mục thư viện.
  - `#story/{story_id}`: Trang chi tiết tác phẩm.
  - `#read/{story_id}/{chap_index}`: Giao diện đọc & nghe audio cho từng chương của bộ truyện đó.

### 🚀 D. Hiệu Suất Tối Đa & Đọc Offline (Enterprise Performance)
- **Minified JSON Payloads**: Toàn bộ dữ liệu chương được nén cấu trúc JSON (`separators=(',', ':')`), giảm hơn **35% dung lượng truyền tải mạng**.
- **Service Worker & PWA (`sw.js`)**: Bộ nhớ đệm *Stale-While-Revalidate* tải trang **0ms**, có thể cài đặt làm App và **đọc truyện offline ngay cả khi mất mạng**.
- **LRU Memory Cache**: Giới hạn lưu tối đa 60 chương gần nhất trong RAM của `app.js`, tự động dọn dẹp bộ nhớ chống tràn RAM trên điện thoại.
- **Background Pre-fetching**: Nạp ngầm trước Chương N+1 và N-1 khi người đọc đang đọc Chương N, giúp bấm chuyển chương lập tức không có độ trễ.
- **DNS Preconnect**: Tải font chữ Google Fonts không giật hình (Zero-Layout Shift).

---

## 🛠️ 4. HƯỚNG DẪN BỘ SCRIPTS VẬN HÀNH (CLI TOOLKIT PLAYBOOK)

### 📌 1. Triển Khai Nhanh 1-Click (1-Click Auto Deploy):
```bash
# Tự động đóng gói, nén JSON, kiểm tra lỗi toàn vẹn và đẩy lên GitHub Pages:
python deploy.py "feat: cập nhật hệ thống và dữ liệu"
```

---

### 📌 2. Nhập & Làm Sạch Truyện Mới Vào Thư Viện (`add_story.py`):
```bash
# Nhập file JSON truyện crawl với đầy đủ thông tin metadata:
python add_story.py --json story.json --title "Đấu Phá Thương Khung" --author "Thiên Tằm Thổ Đậu" --category "Tiên Hiệp, Dị Giới" --desc "Tóm tắt truyện..."
```

---

### 📌 3. Kiểm Tra Toàn Vẹn Dữ Liệu (`health_check.py`):
```bash
# Quét toàn bộ thư viện, kiểm tra số chương, số từ và ảnh bìa:
python health_check.py
```

---

### 📌 4. Xuất Truyện Ra File Ebook Độc Lập (`export_ebook.py`):
```bash
# Xuất truyện thành file Markdown duy nhất để lưu trữ / đọc offline:
python export_ebook.py --id than_nu_tieu_dao_luc --format md --out Than_Nu_Full.md

# Hoặc xuất thành file Text (.txt):
python export_ebook.py --id than_nu_tieu_dao_luc --format txt --out Than_Nu_Full.txt
```

---

### 📌 5. Đóng Gói Thủ Công & Đồng Bộ Toàn Bộ Thư Viện (`build_library.py`):
```bash
# Quét tất cả file JSON truyện trong thư mục, nén minified và đồng bộ sang root:
python build_library.py
```

---

### 📌 6. Chạy Máy Chủ Thử Nghiệm Tại Máy Cục Bộ (Localhost):
```bash
# Khởi chạy HTTP Server trên cổng 8080:
python -m http.server 8080 --directory web

# Mở trình duyệt: http://localhost:8080
```