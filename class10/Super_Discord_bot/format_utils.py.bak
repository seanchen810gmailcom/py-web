import discord  # 匯入 discord.py，讓格式工具可以建立 Discord Embed。


SUCCESS = "✅"  # 成功狀態符號。
WARNING = "⚠️"  # 警告狀態符號。
ERROR = "❌"  # 錯誤狀態符號。
ARROW_RIGHT = "→"  # 向右箭頭符號。
ARROW_LEFT = "←"  # 向左箭頭符號。
ARROW_UP = "↑"  # 向上箭頭符號。
ARROW_DOWN = "↓"  # 向下箭頭符號。
PI = "π"  # 圓周率符號。
SQUARE_ROOT = "√"  # 平方根符號。
APPROX = "≈"  # 約等於符號。
NOT_EQUAL = "≠"  # 不等於符號。
LESS_EQUAL = "≤"  # 小於等於符號。
GREATER_EQUAL = "≥"  # 大於等於符號。
WEATHER_SUN_CLOUD = "🌤️"  # 晴或晴時多雲的天氣符號。
WEATHER_CLOUD = "☁️"  # 多雲或陰天的天氣符號。
WEATHER_RAIN = "🌧️"  # 下雨的天氣符號。
WEATHER_THUNDER = "⛈️"  # 雷雨的天氣符號。
WEATHER_TEMP = "🌡️"  # 溫度欄位使用的天氣符號。
WEATHER_HUMIDITY = "💧"  # 濕度欄位使用的天氣符號。
WEATHER_WIND = "💨"  # 風速欄位使用的天氣符號。
WEATHER_UMBRELLA = "☔"  # 降雨機率欄位使用的天氣符號。


STATUS_SYMBOLS = {  # 建立狀態符號查詢表。
    "success": SUCCESS,  # 成功狀態對應打勾符號。
    "warning": WARNING,  # 警告狀態對應警告符號。
    "error": ERROR,  # 錯誤狀態對應叉叉符號。
}  # 結束狀態符號查詢表。


ARROW_SYMBOLS = {  # 建立箭頭符號查詢表。
    "right": ARROW_RIGHT,  # right 對應向右箭頭。
    "left": ARROW_LEFT,  # left 對應向左箭頭。
    "up": ARROW_UP,  # up 對應向上箭頭。
    "down": ARROW_DOWN,  # down 對應向下箭頭。
}  # 結束箭頭符號查詢表。


MATH_SYMBOLS = {  # 建立數學符號查詢表。
    "pi": PI,  # pi 對應圓周率符號。
    "sqrt": SQUARE_ROOT,  # sqrt 對應平方根符號。
    "approx": APPROX,  # approx 對應約等於符號。
    "not_equal": NOT_EQUAL,  # not_equal 對應不等於符號。
    "less_equal": LESS_EQUAL,  # less_equal 對應小於等於符號。
    "greater_equal": GREATER_EQUAL,  # greater_equal 對應大於等於符號。
}  # 結束數學符號查詢表。


WEATHER_SYMBOLS = {  # 建立天氣符號查詢表。
    "sun_cloud": WEATHER_SUN_CLOUD,  # 晴對應晴時多雲符號。
    "clear": WEATHER_SUN_CLOUD,  # clear 對應晴時多雲符號。
    "cloud": WEATHER_CLOUD,  # cloud 對應多雲符號。
    "rain": WEATHER_RAIN,  # rain 對應雨符號。
    "thunder": WEATHER_THUNDER,  # thunder 對應雷雨符號。
    "temperature": WEATHER_TEMP,  # temperature 對應溫度符號。
    "humidity": WEATHER_HUMIDITY,  # humidity 對應濕度符號。
    "wind": WEATHER_WIND,  # wind 對應風速符號。
    "rain_chance": WEATHER_UMBRELLA,  # rain_chance 對應降雨機率符號。
}  # 結束天氣符號查詢表。


SYMBOLS = {  # 建立全部符號查詢表，方便其他檔案一次匯入。
    **STATUS_SYMBOLS,  # 加入狀態符號。
    **ARROW_SYMBOLS,  # 加入箭頭符號。
    **MATH_SYMBOLS,  # 加入數學符號。
    **WEATHER_SYMBOLS,  # 加入天氣符號。
}  # 結束全部符號查詢表。


def weather_symbol_for_text(text: str) -> str:  # 依天氣描述挑選最合適的天氣符號。
    lowered = str(text or "").strip().lower()  # 整理文字並轉小寫，方便比對中英文描述。
    if any(word in lowered for word in ("thunder", "雷")):  # 描述包含雷或 thunder 時使用雷雨符號。
        return WEATHER_THUNDER  # 回傳雷雨符號。
    if any(word in lowered for word in ("rain", "drizzle", "雨")):  # 描述包含雨、rain 或 drizzle 時使用雨符號。
        return WEATHER_RAIN  # 回傳雨符號。
    if any(word in lowered for word in ("cloud", "雲", "陰")):  # 描述包含雲、陰或 cloud 時使用多雲符號。
        return WEATHER_CLOUD  # 回傳多雲符號。
    return WEATHER_SUN_CLOUD  # 其他狀況預設使用晴時多雲符號。


def _clean_table_cell(value) -> str:  # 清理 Markdown 表格儲存格文字。
    text = str(value if value is not None else "無資料").strip()  # 將資料轉成字串，缺值顯示無資料。
    text = text.replace("\n", " ")  # Markdown 表格儲存格內不能保留換行。
    text = text.replace("|", "／")  # 避免直線符號破壞 Markdown 表格欄位。
    return text or " "  # 空內容用空白代替，避免表格格式斷掉。


def make_markdown_table(headers, rows) -> str:  # 產生 Discord 可顯示的 Markdown 表格。
    if not isinstance(headers, (list, tuple)) or not headers:  # 表格必須有表頭。
        raise ValueError("headers must be a non-empty list")  # 主動丟出錯誤，讓呼叫端知道資料格式不正確。
    if not isinstance(rows, (list, tuple)):  # 表格列資料必須是 list 或 tuple。
        raise ValueError("rows must be a list")  # 主動丟出錯誤，讓呼叫端知道資料格式不正確。
    cleaned_headers = [_clean_table_cell(header) for header in headers]  # 清理表頭文字。
    cleaned_rows = []  # 建立整理後的資料列清單。
    for row in rows:  # 逐列整理資料。
        row_values = list(row) if isinstance(row, (list, tuple)) else [row]  # 將單列資料統一轉成 list。
        padded = (row_values + [""] * len(cleaned_headers))[:len(cleaned_headers)]  # 補齊或裁切欄位數，避免表格錯位。
        cleaned_rows.append([_clean_table_cell(cell) for cell in padded])  # 清理每個儲存格後加入結果。
    separator = ["---" for _header in cleaned_headers]  # 建立 Markdown 表格分隔列。
    lines = [  # 建立 Markdown 表格文字列。
        "| " + " | ".join(cleaned_headers) + " |",  # 第一列是表頭。
        "| " + " | ".join(separator) + " |",  # 第二列是 Markdown 分隔線。
    ]  # 結束初始表格列。
    lines.extend("| " + " | ".join(row) + " |" for row in cleaned_rows)  # 加入所有資料列。
    return "\n".join(lines)  # 回傳完整 Markdown 表格。


def split_long_message(text, limit: int = 1900) -> list[str]:  # 將長文字切成 Discord 可送出的多段。
    content = str(text or "").strip() or "（沒有內容）"  # 整理文字，避免送出空訊息。
    chunks: list[str] = []  # 建立分段結果清單。
    current = ""  # 保存目前累積中的分段。
    for line in content.splitlines(keepends=True):  # 逐行切分，保留換行讓表格格式維持。
        pieces = [line[index:index + limit] for index in range(0, len(line), limit)] or [""]  # 單行太長時硬切成安全長度。
        for piece in pieces:  # 逐片累積文字。
            if len(current) + len(piece) > limit and current:  # 如果加上這片會超過限制，就先收掉目前分段。
                chunks.append(current.rstrip())  # 加入目前分段並清掉尾端空白。
                current = ""  # 重新開始累積下一段。
            current += piece  # 加入目前片段。
    if current.strip():  # 如果最後還有內容，就加入結果。
        chunks.append(current.rstrip())  # 保存最後一段。
    return chunks or ["（沒有內容）"]  # 保證至少回傳一段。


def make_weather_embed(title: str, description: str, fields=None, thumbnail_url: str = "", color: str = "#1E90FF") -> discord.Embed:  # 建立天氣摘要 Embed。
    safe_title = str(title or "天氣摘要").strip()  # 整理 Embed 標題。
    safe_description = str(description or "（沒有天氣摘要）").strip()  # 整理 Embed 描述。
    shown_description = safe_description[:3900] + ("..." if len(safe_description) > 3900 else "")  # 控制描述長度，避免超過 Discord Embed 限制。
    embed = discord.Embed(title=safe_title, description=shown_description, color=discord.Colour.from_str(color))  # 建立 Discord Embed。
    if thumbnail_url:  # 如果呼叫端提供天氣圖示，就顯示在 Embed 右側。
        embed.set_thumbnail(url=str(thumbnail_url))  # 設定 Embed 縮圖。
    for field in fields or []:  # 逐一加入欄位。
        if isinstance(field, dict):  # 支援 dict 格式欄位。
            name = str(field.get("name") or "欄位").strip()  # 取得欄位名稱。
            value = str(field.get("value") or "無資料").strip()  # 取得欄位內容。
            inline = bool(field.get("inline", True))  # 取得欄位是否 inline。
        else:  # 支援 tuple 或 list 格式欄位。
            name = str(field[0] if len(field) > 0 else "欄位").strip()  # 取得欄位名稱。
            value = str(field[1] if len(field) > 1 else "無資料").strip()  # 取得欄位內容。
            inline = bool(field[2]) if len(field) > 2 else True  # 取得欄位是否 inline。
        embed.add_field(name=name[:256] or "欄位", value=(value[:1000] + "..." if len(value) > 1000 else value) or "無資料", inline=inline)  # 加入欄位並控制長度。
    return embed  # 回傳可直接交給 Discord 傳送的 Embed。


def status_line(status: str, text: str) -> str:  # 依狀態符號組出一行顯示文字。
    symbol = STATUS_SYMBOLS.get((status or "").strip().lower(), "")  # 依狀態名稱取得符號，找不到就用空字串。
    return f"{symbol} {text}".strip()  # 回傳符號加文字，並去除多餘空白。


def symbol_demo_text() -> str:  # 建立 /test_symbols 要顯示的符號測試文字。
    lines = [  # 建立多行測試文字清單。
        f"{SUCCESS} 成功",  # 顯示成功符號。
        f"{WARNING} 警告",  # 顯示警告符號。
        f"{ERROR} 錯誤",  # 顯示錯誤符號。
        f"箭頭：{ARROW_RIGHT} {ARROW_LEFT} {ARROW_UP} {ARROW_DOWN}",  # 顯示四種箭頭。
        f"數學：{PI} {SQUARE_ROOT} {APPROX} {NOT_EQUAL} {LESS_EQUAL} {GREATER_EQUAL}",  # 顯示指定數學符號。
        f"天氣：{WEATHER_SUN_CLOUD} 晴 {WEATHER_CLOUD} 多雲 {WEATHER_RAIN} 雨 {WEATHER_THUNDER} 雷雨 {WEATHER_TEMP} 溫度 {WEATHER_HUMIDITY} 濕度 {WEATHER_WIND} 風速 {WEATHER_UMBRELLA} 降雨機率",  # 顯示天氣報告需要的特殊符號。
    ]  # 結束測試文字清單。
    return "\n".join(lines)  # 將測試文字接成 Discord 可送出的多行字串。
