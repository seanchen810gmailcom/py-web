import re  # 匯入 re：用正規表達式解析圖表資料文字。


def _clean_chart_label(raw_label: str) -> str:  # 逐行註解：清理圖表資料標籤，避免把「畫一個」這類指令文字當成標籤。
    # 逐行註解：去掉標籤前後的空白與分隔符。
    label = (raw_label or "").strip(" -:：,，、;；")
    # 逐行註解：移除開頭的禮貌詞彙（如「請你」、「幫我」）。
    label = re.sub(r"^(?:請你|請|麻煩你|麻煩|幫我|幫忙|幫|替我)?\s*", "", label)
    # 逐行註解：移除開頭的動作詞彙（如「畫出」、「做出」、「產生」）。
    label = re.sub(r"^(?:畫出|畫一個|畫個|畫|做出|做一個|做個|做|產生|建立|生成|給我|用)\s*", "", label)
    # 逐行註解：移除開頭的數量詞彙（如「一個」、「一張」）。
    label = re.sub(r"^(?:一個|一張|張|個)\s*", "", label)
    # 逐行註解：再次去掉尾端空白與分隔符。
    label = label.strip(" -:：,，、;；")
    # 逐行註解：英文資料常見於「畫一個apple:3」，保留最後一段英文標籤。
    english_tail = re.search(r"([A-Za-z][A-Za-z0-9 _-]*)$", label)
    if english_tail:
        # 逐行註解：用英文部分替換整個標籤。
        label = english_tail.group(1).strip()
    # 逐行註解：回傳已清理的標籤。
    return label


def parse_chart_text(text: str) -> tuple[list[str], list[float]]:  # 逐行註解：用正則表達式從使用者原始輸入抓資料，支援多種格式。
    # 逐行註解：建立標籤清單。
    labels: list[str] = []
    # 逐行註解：建立數值清單。
    values: list[float] = []
    # 逐行註解：文字內容保險轉成字串。
    text = str(text or "").strip()
    # 逐行註解：空文字不能解析資料。
    if not text:
        return labels, values
    
    # 逐行註解：模式 1：「label：value、label：value」格式（中文標點）。
    # 逐行註解：支援「apple：3、orange：20、pineapple：90」。
    pattern1 = re.compile(r"([^：,，、;；\n\d]+?)\s*[:：]\s*([-+]?\d+(?:\.\d+)?)")
    # 逐行註解：模式 2：「label:value label:value」格式（英文標點加空白）。
    # 逐行註解：支援「apple:3 orange:20 pineapple:90」。
    pattern2 = re.compile(r"([A-Za-z0-9_-]+)\s*:\s*([-+]?\d+(?:\.\d+)?)")
    # 逐行註解：模式 3：「label value label value」格式（直接空白分隔）。
    # 逐行註解：支援「apple 3 orange 20 pineapple 90」。
    pattern3 = re.compile(r"([A-Za-z0-9_-]+)\s+([-+]?\d+(?:\.\d+)?)")
    
    # 逐行註解：先嘗試模式 1（中文標點分隔）。
    matches = list(pattern1.finditer(text))
    if matches:
        # 逐行註解：模式 1 成功匹配。
        for match in matches:
            # 逐行註解：取出標籤並清理。
            label = _clean_chart_label(match.group(1))
            # 逐行註解：忽略空標籤。
            if label:
                # 逐行註解：加入標籤清單。
                labels.append(label)
                # 逐行註解：加入數值清單。
                values.append(float(match.group(2)))
    else:
        # 逐行註解：模式 1 失敗，改嘗試模式 2（英文標點加空白）。
        matches = list(pattern2.finditer(text))
        if matches:
            # 逐行註解：模式 2 成功匹配。
            for match in matches:
                # 逐行註解：取出標籤（英文不需額外清理）。
                label = match.group(1).strip()
                # 逐行註解：忽略空標籤。
                if label:
                    # 逐行註解：加入標籤清單。
                    labels.append(label)
                    # 逐行註解：加入數值清單。
                    values.append(float(match.group(2)))
        else:
            # 逐行註解：模式 2 失敗，改嘗試模式 3（直接空白分隔）。
            matches = list(pattern3.finditer(text))
            if matches:
                # 逐行註解：模式 3 成功匹配。
                for match in matches:
                    # 逐行註解：取出標籤（英文不需額外清理）。
                    label = match.group(1).strip()
                    # 逐行註解：忽略空標籤。
                    if label:
                        # 逐行註解：加入標籤清單。
                        labels.append(label)
                        # 逐行註解：加入數值清單。
                        values.append(float(match.group(2)))
    
    # 逐行註解：回傳抽取出的標籤與數值。
    return labels, values
