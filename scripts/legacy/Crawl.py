import os
import re
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from firecrawl import Firecrawl
from google import genai

load_dotenv()

# Cấu hình logging
logging.basicConfig(
    filename='crawl_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def clean_filename(url):
    """Tạo tên file an toàn từ URL và lưu vào thư mục output"""
    # Loại bỏ https://, thay thế ký tự lạ bằng gạch dưới
    clean = re.sub(r'https?://', '', url)
    clean = re.sub(r'[^a-zA-Z0-9]', '_', clean)
    
    # Đảm bảo thư mục output tồn tại
    if not os.path.exists('output'):
        os.makedirs('output')
        
    return os.path.join("output", f"kq_{clean[:50]}.txt")

def process_list_urls(url_list):
    """Xử lý danh sách URL: Crawl, gọi Gemini, lưu file.
    args:
        url_list: Danh sách URL cần xử lý
    returns:
        files được lưu trong thư mục output
    """
    # 1. Khởi tạo Client
    fc_key = os.getenv("FIRECRAWL_API_KEY")
    gem_key = os.getenv("GEMINI_API_KEY")
    
    if not fc_key or not gem_key:
        print("Thiếu API Key trong file .env")
        return

    fc_app = Firecrawl(api_key=fc_key)
    client = genai.Client(api_key=gem_key)

    print(f"--- Bắt đầu xử lý danh sách {len(url_list)} URL ---")

    # 2. Duyệt qua từng URL trong danh sách
    for index, url in enumerate(url_list):
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                print(f"\n[{index + 1}/{len(url_list)}] Đang xử lý (Lần {attempt + 1}): {url}")
                
                crawl_result = fc_app.crawl(
                    url=url,
                    limit=1,
                    scrape_options={'formats': ['markdown']}
                )

                if not hasattr(crawl_result, 'data') or not crawl_result.data:
                    raise ValueError(f"Không lấy được dữ liệu từ {url}")

                # Lấy nội dung markdown
                content_markdown = crawl_result.data[0].markdown
                if not content_markdown:
                    raise ValueError("Nội dung rỗng.")

                # Tạo prompt 
                final_prompt = f"""
                Vai trò:
                Bạn là chuyên gia xử lý dữ liệu văn bản. Nhiệm vụ của bạn là trích xuất thông tin từ nguồn dữ liệu lịch âm thành một bản báo cáo chi tiết dạng văn bản (Text File).
                Nguyên tắc xử lý:
                Định dạng: Sử dụng định dạng văn bản có cấu trúc (Structured Text) với các tiêu đề in hoa và gạch đầu dòng rõ ràng.
                Nội dung: Phải trích xuất đầy đủ, không được bỏ sót các chi tiết kỹ thuật (Ngũ hành, Sao, Giờ, Lời khuyên chi tiết).
                Thuật ngữ: Giữ nguyên các thuật ngữ chuyên môn (ví dụ: "Sát Cống", "Tốc Hỷ", "Sơn Đầu Hỏa").
                Trung thực: Không thêm bớt nội dung, chỉ trích xuất những gì có trong văn bản nguồn.
                Mẫu cấu trúc kết quả (Template):
                Hãy trả về kết quả tuân thủ chính xác cấu trúc mẫu dưới đây:
                === [Ngày/Tháng/Năm] DƯƠNG LỊCH ===
                I. THÔNG TIN ĐỊNH DANH
                - Dương lịch: [Ngày/Tháng/Năm] - [Thứ]
                - Âm lịch: [Ngày/Tháng/Năm]
                - Can Chi: Ngày [Tên Can Chi] - Tháng [Tên Can Chi] - Năm [Tên Can Chi]
                II. TỔNG QUAN CÁT HUNG
                - Loại ngày: [Hoàng Đạo/Hắc Đạo - Tên cụ thể]
                - Đánh giá chung: [Nội dung đánh giá tổng quan]
                III. PHÂN TÍCH NGŨ HÀNH & XUNG KHẮC
                - Tuổi xung kỵ: [Danh sách tuổi bị xung]
                IV. HỆ THỐNG SAO (THẦN SÁT)
                - Sao Tốt (Cát tinh):
                + [Tên Sao]: [Ý nghĩa/Tác dụng]
                + ...
                - Sao Xấu (Hung tinh):
                + [Tên Sao]: [Điều kiêng kỵ]
                + ...
                V. CÁC HỆ QUY CHIẾU KHÁC
                - Thập Nhị Trực: Trực [Tên] - [Ý nghĩa]
                - Nhị Thập Bát Tú: Sao [Tên] - [Ý nghĩa]
                - Bành Tổ Bách Kỵ:
                + Kỵ Can [Tên]: [Nội dung]
                + Kỵ Chi [Tên]: [Nội dung]
                - Ngày kỵ đặc biệt: [Có phạm Tam Nương/Nguyệt Kỵ/Dương Công Kỵ không?]
                VI. THỜI GIAN KHỞI SỰ (GIỜ TỐT - XẤU)
                - Danh sách Giờ Hoàng Đạo (Tốt): [Liệt kê các giờ]
                - Danh sách Giờ Hắc Đạo (Xấu): [Liệt kê các giờ]
                - Luận giải chi tiết từng khung giờ tốt:
                + Giờ [Tên chi] ([Khung giờ]) - Giờ [Tên sao/loại giờ]: [Mô tả chi tiết về sao chiếu và việc nên làm]
                + ... (Liệt kê hết các giờ có mô tả chi tiết trong văn bản)
                VII. XUẤT HÀNH (HƯỚNG & GIỜ LÝ THUẦN PHONG)
                - Đánh giá ngày xuất hành: [Tên ngày theo Khổng Minh] - [Lời khuyên]
                - Hướng xuất hành:
                + Tài Thần: [Hướng]
                + Hỷ Thần: [Hướng]
                + Hạc Thần (Xấu): [Hướng]
                - Giờ xuất hành Lý Thuần Phong:
                + [Khung giờ 1] - Giờ [Tên]: [Đánh giá Tốt/Xấu] - [Lời khuyên chi tiết]
                + [Khung giờ 2] - Giờ [Tên]: [Đánh giá Tốt/Xấu] - [Lời khuyên chi tiết]
                + ... (Liệt kê đủ 6 khung giờ)
                =========================================

                
                PHÍA TRÊN LÀ PROMPT ĐÂY LÀ DỮ LIỆU ĐẦU VÀO:
                ---
                {content_markdown}
                ---
                """

                # Gọi Gemini
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=final_prompt
                )

                # Xử lý nội dung: Loại bỏ markdown code block ```text ... ```
                content_to_save = response.text.strip()
                content_to_save = re.sub(r"^```[a-zA-Z]*\n", "", content_to_save)
                # Loại bỏ ``` ở cuối
                if content_to_save.endswith("```"):
                    content_to_save = content_to_save[:-3].strip()

                # 3. Lưu ra file riêng biệt
                filename = clean_filename(url)
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content_to_save)

                print(f"   -> Thành công! Đã lưu file: {filename}")
                
                # Nghỉ 5 giây để tránh spam API quá nhanh
                time.sleep(5)
                break 

            except Exception as e:
                print(f"   -> Lỗi tại URL này (Lần {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"   -> Đang thử lại sau {retry_delay} giây...")
                    time.sleep(retry_delay)
                else:
                    print("   -> Đã hết số lần thử lại. Bỏ qua URL này.")
                    logging.error(f"Failed URL: {url} | Error: {str(e)}")

if __name__ == "__main__":
    # Danh sách các URL cần xử lý
    my_urls = [
        "https://lichamngay.com/nam-2025/thang-11/lich-am-ngay-29-11-2025.html",
        "https://lichamngay.com/nam-2025/thang-11/lich-am-ngay-30-11-2025.html",
    ]

    process_list_urls(my_urls)