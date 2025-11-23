# -*- coding: utf-8 -*-
"""提取水位測站和氣象測站資料"""
import pandas as pd
from pathlib import Path

def extract_stations():
    """提取水位和氣象測站資料"""

    xl = pd.ExcelFile('data/測站基本資料2025.xlsx')

    print(f"可用的工作表: {xl.sheet_names}")

    all_stations = []

    # 1. 讀取水位測站 (使用索引而非名稱)
    print("\n讀取水位測站...")
    df_water = pd.read_excel('data/測站基本資料2025.xlsx', sheet_name=0)  # 第一個工作表
    df_water['測站類型'] = '水位測站'
    all_stations.append(df_water)
    print(f"  水位測站: {len(df_water)} 個")

    # 2. 讀取氣象測站 (使用索引而非名稱)
    print("讀取氣象測站...")
    df_meteor = pd.read_excel('data/測站基本資料2025.xlsx', sheet_name=1)  # 第二個工作表
    df_meteor['測站類型'] = '氣象測站'
    all_stations.append(df_meteor)
    print(f"  氣象測站: {len(df_meteor)} 個")

    # 合併
    df_all = pd.concat(all_stations, ignore_index=True)
    print(f"\n總計: {len(df_all)} 個測站")

    # 清理文字欄位的空白（重要！測站資料的欄位後面有很多空白）
    print("\n清理資料（移除空白）...")
    text_columns = ['測站名稱', '水系', '河川', '管理單位', '地址']
    for col in text_columns:
        if col in df_all.columns:
            df_all[col] = df_all[col].apply(lambda x: str(x).strip() if pd.notna(x) and x != 'nan' else x)
            print(f"  已清理 {col} 欄位")

    return df_all

def analyze_stations(df):
    """分析測站資料"""

    print("\n" + "=" * 80)
    print("測站資料分析")
    print("=" * 80)

    print(f"\n欄位: {list(df.columns)}")

    # 統計測站類型
    print("\n測站類型分布:")
    print(df['測站類型'].value_counts())

    # 統計管理單位
    if '管理單位' in df.columns:
        print("\n管理單位統計:")
        print(df['管理單位'].value_counts())

    # 統計水系
    if '水系' in df.columns:
        print("\n水系分布 (前20):")
        print(df['水系'].value_counts().head(20))

        # 檢查與河川資料的對應
        print(f"\n唯一水系數量: {df['水系'].nunique()}")

    # 檢查有經緯度的測站
    if 'TWD97M2(X坐標)' in df.columns and 'TWD97M2(Y坐標)' in df.columns:
        has_coords = df['TWD97M2(X坐標)'].notna() & df['TWD97M2(Y坐標)'].notna()
        print(f"\n有經緯度座標的測站: {has_coords.sum()} / {len(df)} ({has_coords.sum()/len(df)*100:.1f}%)")

    # 隨機抽樣
    print("\n隨機抽樣 5 筆:")
    sample_cols = ['測站名稱', '測站類型', '水系', '河川', '管理單位', '高程(m)']
    sample_cols = [col for col in sample_cols if col in df.columns]
    print(df[sample_cols].sample(min(5, len(df))).to_string())

def save_stations(df, output_path):
    """儲存測站資料"""

    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True)

    # 儲存為 Excel
    df.to_excel(output_path, index=False, engine='openpyxl')

    # 設定凍結窗格
    from openpyxl import load_workbook
    wb = load_workbook(output_path)
    ws = wb.active
    ws.freeze_panes = 'A2'
    wb.save(output_path)

    print(f"\n已儲存至: {output_path}")
    print("已設定標題列凍結")

def main():
    print("=" * 80)
    print("提取水位與氣象測站資料")
    print("=" * 80)

    # 提取測站
    df = extract_stations()

    # 分析測站
    analyze_stations(df)

    # 儲存測站
    output_path = "data/測站資料_水位與氣象.xlsx"
    save_stations(df, output_path)

    print("\n" + "=" * 80)
    print("完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()
