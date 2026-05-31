import io  # 匯入 io，讓圖表可以存進記憶體中的 BytesIO，而不是寫成本機檔案。
import math  # 匯入 math，讓折線圖遇到缺值時可以用 NaN 畫出斷線而不是崩潰。
import textwrap  # 匯入 textwrap，讓表格圖片的長文字可以自動換行。
import matplotlib  # 匯入 matplotlib，準備設定無視窗後端，讓 Discord Bot 在背景也能畫圖。
matplotlib.use("Agg")  # 使用 Agg 後端，避免 bot 需要開啟任何圖形視窗。
import matplotlib.pyplot as plt  # 匯入 pyplot，負責建立長條圖、折線圖和圓餅圖。


def _configure_chart_font() -> None:  # 設定圖表字型，讓繁體中文標題和標籤盡量正常顯示。
    plt.rcParams["font.sans-serif"] = [  # 設定 matplotlib 優先嘗試的無襯線字型清單。
        "PingFang TC",  # macOS 常見繁體中文字型。
        "Heiti TC",  # macOS 另一個常見繁體中文字型。
        "Noto Sans CJK TC",  # 常見跨平台繁體中文字型。
        "Arial Unicode MS",  # 常見 Unicode 備援字型。
        "DejaVu Sans",  # matplotlib 內建備援字型。
    ]  # 結束字型清單。
    plt.rcParams["axes.unicode_minus"] = False  # 避免負號因中文字型設定而顯示成方塊。


def _normalize_labels(labels) -> list[str]:  # 把外部傳入的 labels 統一整理成字串清單。
    if not isinstance(labels, (list, tuple)):  # 如果 labels 不是清單或 tuple，就視為格式錯誤。
        raise ValueError("labels must be a list")  # 主動丟出錯誤，讓呼叫端知道資料格式不正確。
    normalized = [str(label).strip() for label in labels]  # 將每個標籤轉成字串並清掉頭尾空白。
    if not normalized or any(not label for label in normalized):  # 如果沒有標籤或有空標籤，就不能畫圖。
        raise ValueError("labels must not be empty")  # 主動丟出錯誤，提醒標籤不可為空。
    return normalized  # 回傳整理後的標籤清單。


def _normalize_values(values) -> list[float]:  # 把外部傳入的 values 統一整理成浮點數清單。
    if not isinstance(values, (list, tuple)):  # 如果 values 不是清單或 tuple，就視為格式錯誤。
        raise ValueError("values must be a list")  # 主動丟出錯誤，讓呼叫端知道資料格式不正確。
    normalized: list[float] = []  # 建立整理後的數值清單。
    for value in values:  # 逐一處理每個數值。
        normalized.append(float(value))  # 將 int、float 或可轉數字的字串轉成 float。
    if not normalized:  # 如果沒有任何數值，就不能畫圖。
        raise ValueError("values must not be empty")  # 主動丟出錯誤，提醒數值不可為空。
    return normalized  # 回傳整理後的數值清單。


def _validate_chart_data(labels, values) -> tuple[list[str], list[float]]:  # 同時驗證並整理 labels 和 values。
    normalized_labels = _normalize_labels(labels)  # 整理圖表標籤。
    normalized_values = _normalize_values(values)  # 整理圖表數值。
    if len(normalized_labels) != len(normalized_values):  # 標籤數量必須和數值數量一致。
        raise ValueError("labels and values length mismatch")  # 主動丟出錯誤，避免畫出錯位圖表。
    return normalized_labels, normalized_values  # 回傳已驗證的標籤與數值。


def _normalize_optional_values(values, label: str) -> list[float]:  # 將可缺值的數值序列轉成 matplotlib 可接受的 float 或 NaN。
    if not isinstance(values, (list, tuple)):  # 如果傳入的不是清單或 tuple，就視為資料格式錯誤。
        raise ValueError(f"{label} must be a list")  # 主動丟出錯誤，讓呼叫端知道哪個序列格式不正確。
    normalized: list[float] = []  # 建立整理後的數值清單。
    for value in values:  # 逐一處理每個數值。
        if value is None:  # None 代表 API 缺少資料。
            normalized.append(math.nan)  # 用 NaN 讓 matplotlib 畫出空段，不讓程式崩潰。
            continue  # 跳到下一筆資料。
        text_value = str(value).strip()  # 將資料轉成字串，方便判斷「無資料」這類文字。
        if not text_value or text_value == "無資料":  # 空字串或無資料都視為缺值。
            normalized.append(math.nan)  # 用 NaN 表示缺值。
            continue  # 跳到下一筆資料。
        try:  # 嘗試把資料轉成 float。
            normalized.append(float(text_value))  # 成功時加入浮點數。
        except ValueError:  # 如果文字無法轉成數字，就當作缺值處理。
            normalized.append(math.nan)  # 用 NaN 避免圖表產生失敗。
    return normalized  # 回傳整理後的數值清單。


def _has_numeric_value(values: list[float]) -> bool:  # 判斷序列中是否至少有一個可畫的數字。
    return any(not math.isnan(value) for value in values)  # 只要有一個不是 NaN 的值就可以畫圖。


def _validate_same_length(labels: list[str], *series: list[float]) -> None:  # 檢查時間軸與每條資料線長度是否一致。
    for values in series:  # 逐一檢查每條資料線。
        if len(labels) != len(values):  # 如果長度不同，折線圖會對不上時間軸。
            raise ValueError("times and values length mismatch")  # 主動丟出錯誤，避免畫出錯位圖表。


def _finish_chart(fig) -> io.BytesIO:  # 將 matplotlib figure 輸出成 BytesIO 並關閉 figure。
    buffer = io.BytesIO()  # 建立記憶體緩衝區，不建立本機圖片檔。
    fig.tight_layout()  # 自動整理圖表邊距，避免標籤或標題被切掉。
    fig.savefig(buffer, format="png", dpi=160, bbox_inches="tight")  # 將圖表直接寫進 BytesIO，格式使用 PNG。
    plt.close(fig)  # 關閉 figure，避免 bot 長時間執行時累積記憶體。
    buffer.seek(0)  # 將讀取位置移回開頭，讓 discord.File 可以直接讀取。
    return buffer  # 回傳可交給 discord.File 的 BytesIO 物件。


def make_bar_chart(title, labels, values) -> io.BytesIO:  # 建立長條圖並回傳 BytesIO。
    _configure_chart_font()  # 每次畫圖前套用字型設定，確保背景執行也能使用。
    chart_title = str(title or "長條圖").strip()  # 整理圖表標題，沒有標題時使用預設名稱。
    normalized_labels, normalized_values = _validate_chart_data(labels, values)  # 驗證並整理圖表資料。
    fig, ax = plt.subplots(figsize=(8, 4.8))  # 建立適合 Discord 顯示的圖表尺寸。
    ax.bar(normalized_labels, normalized_values, color="#4C78A8")  # 根據資料繪製長條圖。
    ax.set_title(chart_title)  # 設定圖表標題。
    ax.set_ylabel("數值")  # 設定 Y 軸標籤。
    ax.grid(axis="y", alpha=0.28)  # 加上淡色水平格線，方便比較數值高低。
    ax.tick_params(axis="x", labelrotation=25)  # 讓 X 軸標籤微微旋轉，避免長文字重疊。
    return _finish_chart(fig)  # 將圖表輸出成 BytesIO 後回傳。


def make_line_chart(title, labels, values) -> io.BytesIO:  # 建立折線圖並回傳 BytesIO。
    _configure_chart_font()  # 每次畫圖前套用字型設定，確保背景執行也能使用。
    chart_title = str(title or "折線圖").strip()  # 整理圖表標題，沒有標題時使用預設名稱。
    normalized_labels, normalized_values = _validate_chart_data(labels, values)  # 驗證並整理圖表資料。
    fig, ax = plt.subplots(figsize=(8, 4.8))  # 建立適合 Discord 顯示的圖表尺寸。
    ax.plot(normalized_labels, normalized_values, marker="o", linewidth=2.2, color="#2A9D8F")  # 根據資料繪製折線圖。
    ax.set_title(chart_title)  # 設定圖表標題。
    ax.set_ylabel("數值")  # 設定 Y 軸標籤。
    ax.grid(alpha=0.28)  # 加上淡色格線，方便觀察趨勢。
    ax.tick_params(axis="x", labelrotation=25)  # 讓 X 軸標籤微微旋轉，避免長文字重疊。
    return _finish_chart(fig)  # 將圖表輸出成 BytesIO 後回傳。


def make_pie_chart(title, labels, values) -> io.BytesIO:  # 建立圓餅圖並回傳 BytesIO。
    _configure_chart_font()  # 每次畫圖前套用字型設定，確保背景執行也能使用。
    chart_title = str(title or "圓餅圖").strip()  # 整理圖表標題，沒有標題時使用預設名稱。
    normalized_labels, normalized_values = _validate_chart_data(labels, values)  # 驗證並整理圖表資料。
    if sum(normalized_values) <= 0:  # 圓餅圖的總和必須大於 0 才有比例意義。
        raise ValueError("pie chart values must sum above zero")  # 主動丟出錯誤，避免畫出無效圓餅圖。
    fig, ax = plt.subplots(figsize=(7, 5.2))  # 建立適合 Discord 顯示的圓餅圖尺寸。
    ax.pie(normalized_values, labels=normalized_labels, autopct="%1.1f%%", startangle=90)  # 根據資料繪製圓餅圖並顯示百分比。
    ax.set_title(chart_title)  # 設定圖表標題。
    ax.axis("equal")  # 讓圓餅圖維持正圓比例。
    return _finish_chart(fig)  # 將圖表輸出成 BytesIO 後回傳。


def make_temperature_line_chart(title, times, real_temps, feels_like_temps) -> io.BytesIO:  # 建立實際溫度與體感溫度雙線折線圖。
    _configure_chart_font()  # 每次畫圖前套用字型設定，確保繁體中文標題能正常顯示。
    chart_title = str(title or "當天氣溫折線圖").strip()  # 整理圖表標題，沒有標題時使用預設名稱。
    normalized_times = _normalize_labels(times)  # 整理時間軸標籤。
    normalized_real = _normalize_optional_values(real_temps, "real_temps")  # 整理實際溫度資料，缺值轉成 NaN。
    normalized_feels = _normalize_optional_values(feels_like_temps, "feels_like_temps")  # 整理體感溫度資料，缺值轉成 NaN。
    _validate_same_length(normalized_times, normalized_real, normalized_feels)  # 確認兩條線都能對上時間軸。
    if not _has_numeric_value(normalized_real) and not _has_numeric_value(normalized_feels):  # 如果兩條線都沒有任何數字，就不能畫圖。
        raise ValueError("temperature series has no numeric values")  # 主動丟出錯誤，讓 Discord 顯示清楚錯誤。
    fig, ax = plt.subplots(figsize=(9, 5.2))  # 建立適合 Discord 顯示的溫度折線圖尺寸。
    if _has_numeric_value(normalized_real):  # 有實際溫度資料時才畫第一條線。
        ax.plot(normalized_times, normalized_real, marker="o", linewidth=2.2, color="#E45756", label="實際溫度")  # 繪製實際溫度折線。
    if _has_numeric_value(normalized_feels):  # 有體感溫度資料時才畫第二條線。
        ax.plot(normalized_times, normalized_feels, marker="o", linewidth=2.2, color="#4C78A8", label="體感溫度")  # 繪製體感溫度折線。
    ax.set_title(chart_title)  # 設定圖表標題。
    ax.set_xlabel("時間")  # 設定 X 軸標籤。
    ax.set_ylabel("°C")  # 設定 Y 軸攝氏單位。
    ax.grid(alpha=0.28)  # 加上淡色格線，方便觀察溫度變化。
    ax.legend()  # 顯示圖例，讓使用者知道兩條線分別代表什麼。
    ax.tick_params(axis="x", labelrotation=25)  # 讓時間標籤微微旋轉，避免重疊。
    return _finish_chart(fig)  # 將圖表輸出成 BytesIO 後回傳。


def make_humidity_line_chart(title, times, humidity_values) -> io.BytesIO:  # 建立當天濕度折線圖。
    _configure_chart_font()  # 每次畫圖前套用字型設定，確保繁體中文標題能正常顯示。
    chart_title = str(title or "當天濕度折線圖").strip()  # 整理圖表標題，沒有標題時使用預設名稱。
    normalized_times = _normalize_labels(times)  # 整理時間軸標籤。
    normalized_humidity = _normalize_optional_values(humidity_values, "humidity_values")  # 整理濕度資料，缺值轉成 NaN。
    _validate_same_length(normalized_times, normalized_humidity)  # 確認濕度資料能對上時間軸。
    if not _has_numeric_value(normalized_humidity):  # 如果沒有任何濕度數字，就不能畫圖。
        raise ValueError("humidity series has no numeric values")  # 主動丟出錯誤，讓 Discord 顯示清楚錯誤。
    fig, ax = plt.subplots(figsize=(9, 5.2))  # 建立適合 Discord 顯示的濕度折線圖尺寸。
    ax.plot(normalized_times, normalized_humidity, marker="o", linewidth=2.2, color="#2A9D8F", label="濕度")  # 繪製濕度折線。
    ax.set_title(chart_title)  # 設定圖表標題。
    ax.set_xlabel("時間")  # 設定 X 軸標籤。
    ax.set_ylabel("濕度 (%)")  # 設定 Y 軸百分比單位。
    ax.set_ylim(0, 100)  # 濕度是百分比，固定 0 到 100 讓圖表更直覺。
    ax.grid(alpha=0.28)  # 加上淡色格線，方便觀察趨勢。
    ax.legend()  # 顯示圖例。
    ax.tick_params(axis="x", labelrotation=25)  # 讓時間標籤微微旋轉，避免重疊。
    return _finish_chart(fig)  # 將圖表輸出成 BytesIO 後回傳。


def _wrap_table_cell(value, width: int) -> str:  # 將表格儲存格文字依欄寬換行。
    text = str(value if value is not None else "無資料").strip()  # 將儲存格資料轉成安全文字。
    if not text:  # 如果文字是空的，就顯示空白。
        return " "  # 回傳空白避免 matplotlib table 出現奇怪高度。
    protected_text = text.replace(" m/s", "\u00a0m/s").replace(" °C", "\u00a0°C")  # 將單位前空白改成不換行空白，避免風速或溫度被拆成兩行。
    if len(protected_text) <= width:  # 如果文字本來就能放進欄位，就完全不要換行。
        return protected_text  # 回傳原文字，避免短數值欄位跳版。
    wrapped = textwrap.wrap(protected_text, width=max(8, width), break_long_words=False, replace_whitespace=False)  # 依欄寬換行並盡量不切中文字詞。
    return "\n".join(wrapped or [text])  # 將換行後文字接回儲存格內容。


def make_table_image(title, headers, rows) -> io.BytesIO:  # 建立表格圖片並回傳 BytesIO。
    _configure_chart_font()  # 每次畫表格前套用字型設定，確保繁體中文能正常顯示。
    table_title = str(title or "表格").strip()  # 整理表格標題，沒有標題時使用預設名稱。
    if not isinstance(headers, (list, tuple)) or not headers:  # 表格必須有表頭。
        raise ValueError("headers must be a non-empty list")  # 主動丟出錯誤，讓呼叫端知道資料格式不正確。
    if not isinstance(rows, (list, tuple)):  # 表格列資料必須是清單或 tuple。
        raise ValueError("rows must be a list")  # 主動丟出錯誤，讓呼叫端知道資料格式不正確。
    normalized_headers = [str(header).strip() or " " for header in headers]  # 整理表頭文字。
    normalized_rows = [list(row) if isinstance(row, (list, tuple)) else [row] for row in rows]  # 將每列資料統一成 list。
    column_count = len(normalized_headers)  # 記錄欄位數量。
    padded_rows = [(row + [""] * column_count)[:column_count] for row in normalized_rows]  # 補齊或裁切每列欄位數，避免表格錯位。
    wrap_width = max(12, int(84 / max(1, column_count)))  # 依欄位數估算每格可用文字寬度，至少讓 3.8 m/s 這類單位不換行。
    display_rows = [[_wrap_table_cell(cell, wrap_width) for cell in row] for row in padded_rows]  # 將每格文字換行，避免長文字溢出。
    row_count = max(1, len(display_rows))  # 至少保留一列高度，避免空表格太扁。
    font_size = max(8, min(11, int(13 - row_count / 14)))  # 依表格長度自動調整字體大小，最低仍保持可讀。
    figure_width = max(11.5, column_count * 1.75)  # 依欄位數自動調整圖片寬度，避免風速等短欄位被迫換行。
    figure_height = max(3.6, min(28.0, 1.8 + row_count * 0.52))  # 依列數自動調整圖片高度，避免內容壓到下一列。
    fig, ax = plt.subplots(figsize=(figure_width, figure_height))  # 建立表格圖片畫布。
    ax.axis("off")  # 表格圖片不需要座標軸。
    ax.set_title(table_title, pad=12)  # 設定表格標題。
    table = ax.table(cellText=display_rows or [[" "] * column_count], colLabels=normalized_headers, cellLoc="center", loc="center")  # 建立 matplotlib 表格。
    table.auto_set_font_size(False)  # 關閉自動字體大小，改用我們依列數算出的字體。
    table.set_fontsize(font_size)  # 套用自動計算後的字體大小。
    table.scale(1, 1.55)  # 放大列高，避免偶爾換行的儲存格壓到下一列。
    for (row_index, _column_index), cell in table.get_celld().items():  # 逐格調整表格樣式。
        cell.set_edgecolor("#D0D7DE")  # 設定淡色格線。
        if row_index == 0:  # 表頭列使用較深底色。
            cell.set_facecolor("#1E90FF")  # 設定表頭藍色背景。
            cell.get_text().set_color("white")  # 設定表頭白字。
            cell.get_text().set_weight("bold")  # 設定表頭粗體。
        else:  # 一般資料列使用淺色交錯背景。
            cell.set_facecolor("#F8FAFC" if row_index % 2 else "#FFFFFF")  # 設定交錯列底色，讓長表格更易讀。
    return _finish_chart(fig)  # 將表格圖片輸出成 BytesIO 後回傳。
