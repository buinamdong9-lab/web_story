import os

def merge_specific_files(file_list, output_file="merged_output.txt"):
    """
    Gộp danh sách các file cụ thể theo thứ tự đã chỉ định.
    
    Args:
        file_list: List các tên file hoặc đường dẫn (theo thứ tự mong muốn)
        output_file: Tên file output
    Returns:
        File được gộp tại đường dẫn output_file   
    """
    
    print(f"Sẽ gộp {len(file_list)} file(s) theo thứ tự:")
    for i, f in enumerate(file_list, 1):
        print(f"  {i}. {f}")
    
    with open(output_file, "w", encoding="utf-8") as outfile:
        for i, txt_file in enumerate(file_list):
            if not os.path.exists(txt_file):
                print(f"\n File không tồn tại: {txt_file} - Bỏ qua")
                continue
                
            print(f"\nĐang xử lý: {txt_file}")
            
            try:
                with open(txt_file, "r", encoding="utf-8") as infile:
                    content = infile.read()
                    outfile.write(content)
                    
                    if not content.endswith("\n"):
                        outfile.write("\n")
                        
            except Exception as e:
                print(f"  ⚠ Lỗi khi đọc file {txt_file}: {e}")
                continue
    
    print(f"\n Hoàn tất! Đã gộp file vào: {output_file}")


if __name__ == "__main__":
    # ========== Gộp các file đã chọn theo thứ tự ==========
    selected_files = [
        r"D:\heheboi\Project\CrawlData\kq_lichamngay_com_nam_2025_thang_11_lich_am_ngay_29_1.txt",
        r"D:\heheboi\Project\CrawlData\kq_lichamngay_com_nam_2025_thang_11_lich_am_ngay_30_1.txt",
    ]
    
    merge_specific_files(selected_files, output_file="merged_selected.txt")
