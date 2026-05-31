#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
圖表解析功能測試腳本
可在系統終端中直接執行：python3 simple_test.py
"""

import sys
import os

# 逐行註解：添加當前目錄到 Python 路徑。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 逐行註解：導入圖表解析工具。
from chart_parser import parse_chart_text


def test_case(description, user_input, expected_labels, expected_values):
    """
    逐行註解：執行單個測試用例。
    
    Args:
        逐行註解：description - 測試描述。
        逐行註解：user_input - 使用者輸入文字。
        逐行註解：expected_labels - 預期的標籤列表。
        逐行註解：expected_values - 預期的數值列表。
    
    Returns:
        逐行註解：成功時回傳 True，失敗時回傳 False。
    """
    # 逐行註解：打印測試標題。
    print(f"\n{'='*70}")
    print(f"測試：{description}")
    print(f"{'='*70}")
    print(f"輸入: {user_input}")
    
    # 逐行註解：調用解析函式。
    labels, values = parse_chart_text(user_input)
    
    # 逐行註解：打印解析結果。
    print(f"解析結果:")
    print(f"  標籤: {labels}")
    print(f"  數值: {values}")
    print(f"預期結果:")
    print(f"  標籤: {expected_labels}")
    print(f"  數值: {expected_values}")
    
    # 逐行註解：驗證結果是否正確。
    if labels == expected_labels and values == expected_values:
        # 逐行註解：通過測試。
        print("✅ 通過")
        return True
    else:
        # 逐行註解：失敗。
        print("❌ 失敗")
        return False


def main():
    """
    逐行註解：主測試函式。
    """
    # 逐行註解：定義所有測試用例。
    tests = [
        {
            "description": "中文標點格式（用冒號和頓號分隔）",
            "input": "畫一個apple：3、orange：20、pineapple：90的圓餅圖，照比例",
            "labels": ["apple", "orange", "pineapple"],
            "values": [3.0, 20.0, 90.0],
        },
        {
            "description": "英文標點格式（用冒號和空白分隔）",
            "input": "apple:3 orange:20 pineapple:90 圓餅圖",
            "labels": ["apple", "orange", "pineapple"],
            "values": [3.0, 20.0, 90.0],
        },
        {
            "description": "空白分隔格式",
            "input": "畫長條圖 apple 3 orange 20 pineapple 90",
            "labels": ["apple", "orange", "pineapple"],
            "values": [3.0, 20.0, 90.0],
        },
    ]
    
    # 逐行註解：打印測試開始訊息。
    print("\n" + "="*70)
    print("Discord Bot 圖表解析功能測試")
    print("="*70)
    
    # 逐行註解：計數器。
    passed = 0
    failed = 0
    
    # 逐行註解：逐一執行每個測試。
    for test in tests:
        # 逐行註解：執行測試。
        success = test_case(
            test["description"],
            test["input"],
            test["labels"],
            test["values"]
        )
        # 逐行註解：統計結果。
        if success:
            passed += 1
        else:
            failed += 1
    
    # 逐行註解：打印測試摘要。
    print(f"\n{'='*70}")
    print(f"測試總結: {passed} 通過，{failed} 失敗")
    print(f"{'='*70}\n")
    
    # 逐行註解：回傳測試結果。
    return failed == 0


if __name__ == "__main__":
    # 逐行註解：執行主函式。
    success = main()
    # 逐行註解：根據測試結果設置退出碼。
    sys.exit(0 if success else 1)
