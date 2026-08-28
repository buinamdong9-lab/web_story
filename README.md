# 📚 WebStory - Nền Tảng Đọc & Nghe Truyện Tự Động Siêu Tốc (1.200+ Bộ Truyện)

Hệ sinh thái ứng dụng web đọc truyện đa nền tảng (PWA), tích hợp bộ máy đọc giọng nói AI (TTS), bộ nạp chương siêu tốc 4 tầng (IndexedDB 0ms) và hệ thống cào - phân vùng dữ liệu tối ưu băng thông từ `https://truyenc.com/`.

- **🌐 Live Website**: [https://buinamdong9-lab.github.io/web_story/](https://buinamdong9-lab.github.io/web_story/)
- **📦 GitHub Repository**: [https://github.com/buinamdong9-lab/web_story](https://github.com/buinamdong9-lab/web_story)
- **🏛️ Tài Liệu Kiến Trúc Chi Tiết**: [ARCHITECTURE.md](file:///d:/Crawl_Data/ARCHITECTURE.md)

---

## ⚡ Các Điểm Nổi Bật Cốt Lõi:

1. **Hơn 1.200+ Bộ Truyện Hoàn Chỉnh**:
   - Toàn bộ các danh mục: *Truyện Ma / Kinh Dị, Truyện 18+ / Ngôn Tình, Tiên Hiệp / Huyền Huyễn, Truyện Cười, Truyện Audio*.
2. **Bộ Nạp Chương Siêu Tốc 4 Tầng (0ms Latency)**:
   - **Tầng 1**: RAM LRU Cache (80 chương gần nhất).
   - **Tầng 2**: Persistent IndexedDB (`webstory_idb`) lưu trữ vĩnh viễn trên thiết bị người đọc.
   - **Tầng 3**: Service Worker Cache-First phục vụ payload tức thì không qua mạng.
   - **Tầng 4**: Predictive Prefetcher tự động nạp ngầm 5-10 chương kế tiếp khi đang đọc.
3. **Bộ Đọc Giọng Nói AI (TTS) & Thanh Tua Scrubber Bar**:
   - Tự động bắt đúng dòng đang đọc, hỗ trợ đa giọng đọc tiếng Việt, điều chỉnh tốc độ/cao độ và hoạt động khi khóa màn hình (Screen WakeLock & MediaSession API).
4. **Kiến Trúc Cào Dữ Liệu Eco-Bandwidth**:
   - Nén đường truyền Gzip/Brotli (-85% dung lượng), Zero-byte Cache Check, bóc tách văn bản bằng C (`lxml`) và Incremental Build Cache (`.build_cache.json`).

---

## 🛠️ Hướng Dẫn Sử Dụng Nhanh:

### 1. Cào Truyện Tiết Kiệm Băng Thông:
```bash
python scripts/crawlers/eco_crawler.py
```

### 2. Cào Siêu Tốc Tối Đa Hóa 20 Core CPU:
```bash
python scripts/crawlers/hyper_crawler.py
```

### 3. Tối Ưu Nén Dữ Liệu Toàn Diện:
```bash
python scripts/pipelines/optimize_data.py
```

### 4. Kiểm Thử Toàn Vẹn & Triển Khai 1-Click Lên GitHub Pages:
```bash
python scripts/pipelines/deploy.py "feat: update stories"
```