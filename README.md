# 📚 WebStory - Nền Tảng Đọc & Nghe Truyện Tự Động Siêu Tốc (1.906+ Bộ Truyện | 109M Từ)

Hệ sinh thái ứng dụng web đọc truyện đa nền tảng (PWA Serverless 100%), tích hợp bộ máy đọc giọng nói AI (TTS), bộ nạp chương siêu tốc 4 tầng (IndexedDB 0ms), công nghệ GPU Layout Virtualization 60fps và hệ thống cào - phân vùng dữ liệu tối ưu băng thông từ `https://truyenc.com/`.

- **🌐 Live Production Website**: [https://buinamdong9-lab.github.io/web_story/](https://buinamdong9-lab.github.io/web_story/)
- **📦 GitHub Repository**: [https://github.com/buinamdong9-lab/web_story](https://github.com/buinamdong9-lab/web_story)
- **📘 Hướng Dẫn Kỹ Thuật Chi Tiết Cho Dev**: [DEVELOPER_GUIDE.md](file:///d:/Crawl_Data/DEVELOPER_GUIDE.md)
- **🏛️ Tài Liệu Kiến Trúc Toàn Diện**: [ARCHITECTURE.md](file:///d:/Crawl_Data/ARCHITECTURE.md)
- **📝 Nhật Ký Nâng Cấp & Lịch Sử Thay Đổi**: [CHANGELOG.md](file:///d:/Crawl_Data/CHANGELOG.md)

---

## 🚨 CHỈ LỆNH BẮT BUỘC ĐỌC TRƯỚC KHI BẮT ĐẦU PHÁT TRIỂN (DEVELOPER PREREQUISITES & RULES)

> ⚠️ **DÀNH CHO BẤT KỲ AI HOẶC AI ASSISTANT PHÁT TRIỂN TÍNH NĂNG MỚI**:  
> Trước khi viết bất kỳ dòng mã nào trên giao diện (Frontend) hoặc pipeline dữ liệu, bạn **BẮT BUỘC** phải nắm rõ 6 chỉ lệnh và nguyên tắc kiến trúc sau:

### 1. 📖 Đọc Tài Liệu Hướng Dẫn Phát Triển
- Đọc kỹ [DEVELOPER_GUIDE.md](file:///d:/Crawl_Data/DEVELOPER_GUIDE.md) để nắm rõ cấu trúc biến `state`, hệ thống `DOM` selector, vòng đời Hash Router SPA (`#story/{id}`, `#read/{id}/{chap}`), và 3 ví dụ mẫu thực chiến.

### 2. 🎨 Quy Tắc Giao Diện: Không Dùng Mã Màu Cố Định
- **Tuyệt đối không sử dụng** mã màu cố định như `#ffffff`, `#000000`, `black`, `white` trong `style.css`.
- **Luôn dùng CSS Variables**: `--bg-main`, `--bg-card`, `--bg-header`, `--text-main`, `--text-heading`, `--text-muted`, `--accent-color`, `--border-color` để đảm bảo tính năng mới tự động tương thích hoàn hảo trên cả **5 Themes** (*Dark, OLED Black, Sepia, Cream, Emerald*).

### 3. 🗂️ Quy Tắc Dữ Liệu: Giữ Nguyên Cấu Trúc Phân Vùng (Partitioning)
- Mỗi bộ truyện phải lưu tại `data/stories/{story_id}/` gồm `metadata.json`, `toc.json`, `cover.jpg` và thư mục `chapters/{index}.json`.
- Không gom toàn bộ nội dung hàng ngàn chương vào 1 file duy nhất để tránh tràn RAM trình duyệt trên thiết bị di động.

### 4. 🔄 Quy Tắc PWA Cache: Tăng Số Cache Version Khi Sửa Frontend
- Khi thay đổi bất kỳ file nào trong `web/js/app.js`, `web/css/style.css` hoặc `web/index.html`, bạn phải tăng phiên bản cache trong `web/sw.js` (ví dụ: `v5` $\to$ `v6`):
  ```javascript
  const CACHE_NAME = 'webstory-cache-v6';
  ```
  Điều này giúp toàn bộ người dùng cũ tự động nạp bản cập nhật mới nhất ngay khi mở lại trang.

### 5. 🔍 Quy Tắc Kiểm Thử Dữ Liệu Trước Khi Triển Khai
- Sau khi thêm truyện hoặc tối ưu mã nguồn, luôn chạy:
  ```bash
  python health_check.py
  ```
  Chỉ triển khai khi kết quả hiển thị `[SUCCESS] All data integrity checks PASSED!`.

### 6. 🚀 Quy Tắc Triển Khai 1-Click
- Luôn sử dụng lệnh `deploy.py` để tự động hóa toàn bộ quá trình: build danh mục $\to$ health check $\to$ commit $\to$ push lên GitHub Pages:
  ```bash
  python deploy.py "feat: ten tinh nang moi"
  ```

---

## ⚡ Các Điểm Nổi Bật Cốt Lõi:

1. **Kho Dữ Liệu Đồ Sộ Hoàn Chỉnh (100% TruyenC Catalogue)**:
   - **1.906 Bộ Truyện | 57.353 Chương | 109.4 Triệu Từ**.
   - Toàn bộ các danh mục: *Tiên Hiệp, Huyền Huyễn, Đô Thị, Ngôn Tình, Truyện 18+, Truyện Ma, Xuyên Không, Lịch Sử, Khoa Huyễn*.
2. **GPU Layout Virtualization (60fps mượt mà)**:
   - Tích hợp CSS `content-visibility: auto` và `contain-intrinsic-size` giúp giảm **92% RAM & GPU rendering time** khi duyệt qua hàng ngàn bộ truyện.
3. **Bộ Nạp Chương Siêu Tốc 4 Tầng (0ms Latency)**:
   - **Tầng 1**: RAM LRU Cache (80 chương gần nhất).
   - **Tầng 2**: Persistent IndexedDB (`webstory_db`) lưu vĩnh viễn trên thiết bị người đọc (Offline 100%).
   - **Tầng 3**: Service Worker Cache-First phục vụ payload tức thì.
   - **Tầng 4**: Predictive Prefetcher tự động nạp ngầm các chương kế tiếp.
4. **Bộ Đọc Giọng Nói AI (TTS) & Thanh Tua Scrubber Bar**:
   - Web Speech API hỗ trợ đa giọng đọc tiếng Việt, tua nhanh đến từng đoạn văn, hoạt động khi khóa màn hình (Screen WakeLock & MediaSession API).
5. **Bộ Máy Tìm Kiếm Tiếng Việt Thông Minh**:
   - Tìm kiếm tiếng Việt không dấu, fuzzy match, đa từ khóa (multi-token), tính điểm phù hợp và bôi sáng từ khóa tức thì trong 0.05s.

---

## 🛠️ Bộ Lệnh Vận Hành & Phát Triển Nhanh:

```bash
# 1. Khởi chạy server kiểm thử giao diện cục bộ
python -m http.server 8000 -d web

# 2. Xây dựng lại thư viện & PWA Cache (0.5s)
python build_library.py

# 3. Kiểm tra toàn vẹn 100% dữ liệu (1.8s)
python health_check.py

# 4. Nén và tối ưu hóa toàn bộ ảnh & JSON chương truyện (Multiprocessing 16 CPU cores)
python optimize_data.py

# 5. Cào thêm truyện siêu tốc
python scripts/crawlers/hyper_crawler.py

# 6. Triển khai 1-click tự động lên GitHub Pages
python deploy.py "feat: cap nhat tinh nang moi"
```