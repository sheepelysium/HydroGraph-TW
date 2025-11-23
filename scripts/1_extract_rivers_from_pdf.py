# scripts/1_extract_rivers_from_pdf.py
"""從 PDF 提取台灣河川階層關係，並儲存為 Excel 檔案"""
import pdfplumber
import pandas as pd
from pathlib import Path

def extract_river_hierarchy(pdf_path):
    """從 PDF 提取河川階層關係"""

    all_rivers = []

    # 追蹤每個階層的最新河川（用於建立父子關係）
    last_river_at_level = {}

    with pdfplumber.open(pdf_path) as pdf:
        # 從第 6 頁開始（表格起始頁）
        for page_num in range(5, len(pdf.pages)):  # 第 6 頁 = index 5
            page = pdf.pages[page_num]
            
            # 提取表格
            tables = page.extract_tables()
            
            for table in tables:
                if not table:
                    continue
                    
                # 清理欄位的函數
                def clean_field(field):
                    """清理欄位：移除換行、回車、多餘空白"""
                    if not field:
                        return ""
                    return str(field).replace('\n', '').replace('\r', '').replace('  ', ' ').strip()

                # 合併多行的河川名稱
                merged_rows = []
                pending_row = None

                for row in table[1:]:
                    if not row or len(row) < 7:
                        continue

                    # 過濾掉標題列
                    row_str = str(row[0]) + str(row[1]) + str(row[2]) + str(row[3])
                    if any(keyword in row_str for keyword in ["序號", "序号", "主流名稱", "主流名称",
                                                                "支流名稱", "支流名称", "次支流",
                                                                "次次支流", "河川代碼", "河川代码",
                                                                "維基數據", "维基数据", "名稱", "名称"]):
                        continue

                    river_code = clean_field(row[6]) if len(row) > 6 else ""

                    # 如果河川代碼為空或 None，可能是延續上一行的名稱
                    if (not river_code or river_code == "None" or river_code == "nan") and pending_row:
                        # 合併到上一行
                        for i in range(1, 6):  # 合併主流、支流等欄位
                            if row[i]:
                                pending_row[i] = (pending_row[i] or "") + clean_field(row[i])
                        continue

                    # 如果有待處理的行，先保存
                    if pending_row:
                        merged_rows.append(pending_row)

                    # 儲存當前行作為待處理行
                    pending_row = row.copy()

                # 處理最後一行
                if pending_row:
                    merged_rows.append(pending_row)

                # 處理合併後的行
                for row in merged_rows:
                    seq_no = row[0]
                    main_river = clean_field(row[1])  # 主流名稱
                    tributary_1 = clean_field(row[2])  # 支流名稱
                    tributary_2 = clean_field(row[3])  # 次支流名稱
                    tributary_3 = clean_field(row[4])  # 次次支流名稱
                    tributary_4 = clean_field(row[5]) if len(row) > 5 else ""  # 次次次支流名稱
                    river_code = clean_field(row[6]) if len(row) > 6 else ""  # 河川代碼
                    
                    # 過濾空行
                    if not any([main_river, tributary_1, tributary_2, tributary_3, tributary_4]):
                        continue
                    
                    # 決定河川名稱和階層
                    if tributary_4:
                        river_name = tributary_4
                        level = 5
                    elif tributary_3:
                        river_name = tributary_3
                        level = 4
                    elif tributary_2:
                        river_name = tributary_2
                        level = 3
                    elif tributary_1:
                        river_name = tributary_1
                        level = 2
                    else:
                        river_name = main_river
                        level = 1

                    # 過濾無效資料
                    if not river_name or river_name == "None":
                        continue

                    # 過濾明顯錯誤的資料
                    # 1. 河川代碼為空或不合理
                    if not river_code or river_code == "None" or river_code == "nan":
                        continue
                    # 2. 河川名稱太短（少於3字，可能是提取錯誤）
                    if len(river_name) < 3:
                        continue
                    # 3. 河川名稱只有括號和符號
                    if river_name.startswith('(') and river_name.count('(') >= len(river_name) / 2:
                        continue

                    # 根據階層決定上游河川（父河川）
                    if level == 1:
                        parent_name = None
                        current_main_river = river_name  # 主流水系就是自己
                    else:
                        parent_name = last_river_at_level.get(level - 1, None)
                        current_main_river = last_river_at_level.get(1, main_river)  # 主流水系

                    # 更新此階層的最新河川
                    last_river_at_level[level] = river_name
                    # 清除更深階層的記錄（因為換了新的父河川）
                    for deeper_level in range(level + 1, 6):
                        last_river_at_level.pop(deeper_level, None)
                    
                    all_rivers.append({
                        "序號": seq_no,
                        "河川名稱": river_name,
                        "河川代碼": river_code,
                        "階層": level,
                        "上游河川": parent_name,
                        "主流水系": current_main_river
                    })
    
    return pd.DataFrame(all_rivers)

def main():
    # 路徑設定
    pdf_path = Path("file/台灣地區河川代碼(112年).pdf")
    output_path = Path("data/河川關係_完整版.xlsx")
    output_path.parent.mkdir(exist_ok=True)
    
    print("開始讀取 PDF...")
    df = extract_river_hierarchy(pdf_path)

    print(f"成功提取 {len(df)} 筆河川資料")
    print(f"\n階層分布：")
    print(df['階層'].value_counts().sort_index())

    # 存檔前再次清理所有文字欄位，確保沒有換行符號
    text_columns = ['河川名稱', '上游河川', '主流水系']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x).replace('\n', '').replace('\r', '').strip() if pd.notna(x) and x != 'None' else x)

    # 存檔
    df.to_excel(output_path, index=False, engine='openpyxl')

    # 設定凍結窗格（讓標題列固定）
    from openpyxl import load_workbook
    wb = load_workbook(output_path)
    ws = wb.active
    ws.freeze_panes = 'A2'  # 凍結第一列（標題列）
    wb.save(output_path)

    print(f"\n已儲存至：{output_path}")
    print("已設定標題列凍結，往下捲動時標題會保持在頂端")

    # 檢查是否有換行符號殘留
    has_newline = df['河川名稱'].astype(str).str.contains('\n|\r').any()
    if has_newline:
        print("\n警告：發現河川名稱中仍有換行符號！")
    else:
        print("\n已確認：所有河川名稱都已正確清理")

    # 顯示範例
    print("\n資料範例：")
    print(df.head(20).to_string())

if __name__ == "__main__":
    main()