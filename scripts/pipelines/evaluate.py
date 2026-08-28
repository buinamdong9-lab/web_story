import os
import re
import glob

# Cấu hình đường dẫn
OUTPUT_DIR = "output"

# Định nghĩa bộ tiêu chí dựa trên Prompt yêu cầu
# Format: (Pattern Regex, Tên tiêu chí hiển thị)
CRITERIA_LIST = [
    (r"===\s+.*\s+DƯƠNG LỊCH\s+===", "Header Tiêu đề"),
    (r"I\.\s+THÔNG TIN ĐỊNH DANH", "I. Thông tin định danh"),
    (r"II\.\s+TỔNG QUAN CÁT HUNG", "II. Tổng quan cát hung"),
    (r"III\.\s+PHÂN TÍCH NGŨ HÀNH.*XUNG KHẮC", "III. Ngũ hành & Xung khắc"),
    (r"IV\.\s+HỆ THỐNG SAO.*THẦN SÁT", "IV. Hệ thống sao"),
    (r"V\.\s+CÁC HỆ QUY CHIẾU KHÁC", "V. Các hệ quy chiếu khác"),
    (r"VI\.\s+THỜI GIAN KHỞI SỰ.*GIỜ TỐT - XẤU", "VI. Thời gian khởi sự"),
    (r"VII\.\s+XUẤT HÀNH.*HƯỚNG.*LÝ THUẦN PHONG", "VII. Xuất hành"),
    # Kiểm tra chi tiết nội dung quan trọng
    (r"Dương lịch:", "Thông tin Dương lịch"),
    (r"Âm lịch:", "Thông tin Âm lịch"),
    (r"Can Chi:", "Thông tin Can Chi"),
    (r"Loại ngày:", "Loại ngày"),
    (r"Đánh giá chung:", "Đánh giá chung"),
    (r"Tuổi xung kỵ:", "Tuổi xung kỵ"),
    (r"Sao Tốt \(Cát tinh\):", " Sao Tốt"),
    (r"Sao Xấu \(Hung tinh\):", " Sao Xấu"),
    (r"Thập Nhị Trực:", " Thập Nhị Trực"),
    (r"Nhị Thập Bát Tú:", " Nhị Thập Bát Tú"),
    (r"Bành Tổ Bách Kỵ:", " Bành Tổ Bách Kỵ"),
    (r"Ngày kỵ đặc biệt:", "Thông tin Ngày kỵ đặc biệt"),
    (r"Danh sách Giờ Hoàng Đạo \(Tốt\):", " Giờ Hoàng Đạo"),
    (r"Danh sách Giờ Hắc Đạo \(Xấu\):", " Giờ Hắc Đạo"),
    (r"Luận giải chi tiết từng khung giờ tốt:", " Luận giải chi tiết từng khung giờ tốt"),
    (r"Đánh giá ngày xuất hành:", "Đánh giá ngày xuất hành"),
    (r"Hướng xuất hành:", " Hướng xuất hành"),
    (r"Giờ xuất hành Lý Thuần Phong:", " Giờ xuất hành Lý Thuần Phong")
]

def evaluate_file(filepath):
    """Đọc file và kiểm tra các tiêu chí.
    args:
        filepath: Đường dẫn file cần đánh giá
    returns dict với cấu trúc: 
        "filename": Tên file,
        "score": Số tiêu chí đạt,
        "total": Tổng số tiêu chí,
        "missing": Danh sách tiêu chí thiếu
    """        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        passed_criteria = []
        missing_criteria = []
        
        for pattern, name in CRITERIA_LIST:
            # Sử dụng re.search để tìm pattern trong nội dung
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                passed_criteria.append(name)
            else:
                missing_criteria.append(name)
                
        return {
            "filename": os.path.basename(filepath),
            "score": len(passed_criteria),
            "total": len(CRITERIA_LIST),
            "missing": missing_criteria
        }
    except Exception as e:
        return {"filename": os.path.basename(filepath), "error": str(e)}

def main():
    # Lấy danh sách file txt trong thư mục output
    txt_files = glob.glob(os.path.join(OUTPUT_DIR, "*.txt"))
    
    if not txt_files:
        print(f"Không tìm thấy file .txt nào trong thư mục '{OUTPUT_DIR}'")
        return

    print(f"--- BẮT ĐẦU ĐÁNH GIÁ ({len(txt_files)} files) ---\n")
    
    total_files = 0
    perfect_files = 0
    
    for filepath in txt_files:
        result = evaluate_file(filepath)
        total_files += 1
        
        # Logic hiển thị kết quả
        if "error" in result:
            print(f"[ERROR] {result['filename']}: {result['error']}")
            continue
            
        score_str = f"{result['score']}/{result['total']}"
        status = "ĐẠT CHUẨN" if result['score'] == result['total'] else "THIẾU TIÊU CHÍ"
        
        if result['score'] == result['total']:
            perfect_files += 1
            
        print(f"File: {result['filename']}")
        print(f" - Đánh giá: {score_str} criteria -> {status}")
        
        if result['missing']:
            print(f" - Tiêu chí thiếu: {', '.join(result['missing'])}")
        print("-" * 40)

    # Tổng kết
    print(f"\nTỔNG KẾT:")
    print(f"Tổng số file: {total_files}")
    print(f"Số file đạt chuẩn tuyệt đối (100% tiêu chí): {perfect_files}")
    print(f"Tỷ lệ hoàn thành: {(perfect_files/total_files)*100:.1f}%")

if __name__ == "__main__":
    main()