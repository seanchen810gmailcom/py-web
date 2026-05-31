#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 逐行註解：測試腳本，用來驗證 chart_parser 和修改後的 AI.py 功能。

import sys  # 逐行註解：匯入 sys，用來添加路徑。
sys.path.insert(0, '/Users/seannb/Desktop/程式/py-web/class10/Super_Discord_bot')  # 逐行註解：添加 Super_Discord_bot 目錄到路徑。

from chart_parser import parse_chart_text  # 逐行註解：導入新的圖表文字解析工具。


def test_parser(user_input: str):  # 逐行註解：測試函式，用來測試單個輸入。
    # 逐行註解：打印測試輸入。
    print(f"\n{'='*60}")
    print(f"測試輸入：{user_input}")
    print(f"{'='*60}")
    
    # 逐行註解：調用 parse_chart_text 解析輸入。
    labels, values = parse_chart_text(user_input)
    
    # 逐行註解：打印解析結果。
    print(f"標籤 (labels)：{labels}")
    print(f"數值 (values)：{values}")
    
    # 逐行註解：檢查是否成功解析。
    if labels and values:
        # 逐行註解：如果有資料，打印成功訊息。
        print("✅ 解析成功！")
        # 逐行註解：打印每個標籤與數值的對應關係。
        for label, value in zip(labels, values):
            print(f"  - {label}: {value}")
    else:
        # 逐行註解：如果沒有資料，打印失敗訊息。
        print("❌ 解析失敗，沒有抓到資料")


# 逐行註解：定義測試用例。
test_cases = [
    "畫一個apple：3、orange：20、pineapple：90的圓餅圖，照比例",
    "apple:3 orange:20 pineapple:90 圓餅圖",
    "畫長條圖 apple 3 orange 20 pineapple 90",
]

# 逐行註解：打印測試開始訊息。
print("\n" + "="*60)
print("圖表文字解析功能測試")
print("="*60)

# 逐行註解：逐一執行每個測試用例。
for test_case in test_cases:
    test_parser(test_case)

# 逐行註解：打印測試結束訊息。
print(f"\n{'='*60}")
print("所有測試完成！")
print(f"{'='*60}\n")
