from collections import Counter, defaultdict  # 匯入 Counter 和 defaultdict：用來統計每日主要天氣與分組預報資料。
from datetime import datetime, timedelta, timezone  # 匯入 datetime 工具：用 OpenWeather 的 UTC 時間加上城市時區偏移。


MISSING_TEXT = "無資料"  # 統一設定缺少欄位時要顯示的文字，避免 Discord 看到 None 或錯誤 JSON。
WEEKLY_HEADERS = ["日期", "天氣狀況", "最高溫", "最低溫", "濕度", "降雨機率", "風速"]  # 設定整週天氣表格欄位。
HOURLY_HEADERS = ["時間", "天氣狀況", "實際溫度", "體感溫度", "濕度", "降雨機率", "風速"]  # 設定當天分時天氣表格欄位。
PERIOD_HEADERS = ["時段", "天氣", "實際溫度", "體感溫度", "濕度", "降雨機率", "風速"]  # 設定相似天氣時段表格欄位。
WEEKDAY_NAMES = ["一", "二", "三", "四", "五", "六", "日"]  # 設定繁體中文星期顯示。


def _as_dict(value) -> dict:  # 把外部傳入資料安全轉成 dict，避免 None 或其他型別讓程式崩潰。
    return value if isinstance(value, dict) else {}  # 只有 dict 直接回傳，其他型別用空 dict 代表沒有資料。


def _safe_float(value):  # 將 API 欄位安全轉成 float，缺值或格式錯誤時回傳 None。
    if value is None:  # 如果資料本來就是 None，就代表沒有資料。
        return None  # 回傳 None 讓格式化函式顯示「無資料」。
    try:  # 嘗試把 int、float 或數字字串轉成浮點數。
        return float(value)  # 成功時回傳浮點數。
    except (TypeError, ValueError):  # 如果資料型別或內容不能轉數字，就不要讓 bot 崩潰。
        return None  # 回傳 None 交給呼叫端處理缺值。


def _current_summary(weather_data: dict) -> dict:  # 從完整 weather_data 取出目前天氣摘要。
    data = _as_dict(weather_data)  # 先保證最外層是 dict。
    current = _as_dict(data.get("current"))  # 新流程會把目前天氣摘要放在 current。
    if current:  # 如果 current 有資料，就使用它。
        return current  # 回傳目前天氣摘要。
    return data  # 舊流程可能直接傳入 weather_summary，所以回傳最外層資料。


def _current_raw(weather_data: dict) -> dict:  # 從完整 weather_data 取出 OpenWeather current weather 原始 JSON。
    data = _as_dict(weather_data)  # 先保證最外層是 dict。
    current = _current_summary(data)  # 取得目前天氣摘要。
    raw = _as_dict(data.get("current_raw"))  # 新流程可能把原始 current JSON 放在 current_raw。
    if raw:  # 如果 current_raw 有資料，就使用它。
        return raw  # 回傳原始 current JSON。
    return _as_dict(current.get("raw_data"))  # 舊摘要格式會把原始 JSON 放在 raw_data。


def _forecast_data(weather_data: dict) -> dict:  # 從完整 weather_data 取出 OpenWeather forecast 原始 JSON。
    data = _as_dict(weather_data)  # 先保證最外層是 dict。
    hourly = _as_dict(data.get("hourly_forecast"))  # 新流程會優先把真正 hourly forecast JSON 放在 hourly_forecast。
    if hourly:  # 如果 hourly_forecast 有資料，就優先使用它。
        return hourly  # 回傳 hourly forecast JSON。
    forecast = _as_dict(data.get("forecast"))  # 新流程會把 forecast JSON 放在 forecast。
    if forecast:  # 如果 forecast 有資料，就使用它。
        return forecast  # 回傳 forecast JSON。
    return data if isinstance(data.get("list"), list) or isinstance(data.get("hourly"), list) else {}  # 如果直接傳入 forecast 或 onecall hourly JSON，就回傳最外層資料。


def _forecast_items(weather_data: dict) -> list[dict]:  # 取出 forecast list，並只保留 dict 項目。
    forecast = _forecast_data(weather_data)  # 取得 forecast JSON。
    items = forecast.get("hourly") if isinstance(forecast.get("hourly"), list) else forecast.get("list")  # OpenWeather hourly 可能在 hourly 或 list。
    if not isinstance(items, list):  # 如果 list 不存在或不是清單，就代表沒有 hourly/forecast 資料。
        return []  # 回傳空清單，讓公開函式給出清楚錯誤。
    return [item for item in items if isinstance(item, dict)]  # 只保留 dict 項目，避免壞資料讓後續欄位存取失敗。


def _require_forecast_items(weather_data: dict) -> list[dict]:  # 取得 forecast list，沒有資料時丟出清楚錯誤。
    items = _forecast_items(weather_data)  # 嘗試讀取分時預報資料。
    if not items:  # 如果沒有任何分時預報資料，就無法做表格或折線圖。
        raise ValueError("天氣 API 沒有 hourly/forecast list 資料，無法產生分時天氣表格或圖表。")  # 丟出給 Discord 顯示的人類可讀錯誤。
    return items  # 回傳可用的分時預報資料。


def _timezone_offset(weather_data: dict) -> int:  # 取得城市時區偏移秒數。
    forecast = _forecast_data(weather_data)  # 取得 forecast JSON。
    city = _as_dict(forecast.get("city"))  # forecast 的城市資訊放在 city。
    value = forecast.get("timezone_offset") if forecast.get("timezone_offset") is not None else city.get("timezone")  # onecall 使用 timezone_offset，forecast 使用 city.timezone。
    if value is None:  # 如果 forecast 沒有時區，就改看 current weather。
        value = _current_raw(weather_data).get("timezone")  # current weather 也可能有 timezone 欄位。
    try:  # 嘗試轉成整數秒數。
        return int(value or 0)  # 成功時回傳偏移秒數，缺值時用 0。
    except (TypeError, ValueError):  # 遇到異常格式時不要崩潰。
        return 0  # 用 UTC 當保底時區。


def _item_datetime(item: dict, weather_data: dict) -> datetime:  # 將 forecast 單筆資料轉成城市當地時間。
    offset = _timezone_offset(weather_data)  # 取得城市 UTC 偏移秒數。
    timestamp = _safe_float(_as_dict(item).get("dt"))  # OpenWeather forecast 單筆資料通常有 UTC epoch 秒數。
    if timestamp is not None:  # 如果有 dt，就優先使用它。
        return datetime.fromtimestamp(timestamp, timezone.utc).replace(tzinfo=None) + timedelta(seconds=offset)  # 轉成本地時間但保持 naive 方便格式化。
    raw_text = str(_as_dict(item).get("dt_txt") or "").strip()  # 如果沒有 dt，就嘗試使用 dt_txt。
    try:  # dt_txt 通常是 YYYY-MM-DD HH:MM:SS。
        return datetime.strptime(raw_text, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=offset)  # 將 UTC 文字時間加上時區偏移。
    except ValueError:  # 如果文字時間格式不合法，就用現在時間保底。
        return datetime.now()  # 回傳本機目前時間，避免整個報告失敗。


def _current_datetime(weather_data: dict) -> datetime | None:  # 取得目前天氣資料的城市當地時間。
    raw = _current_raw(weather_data)  # 取得 current weather 原始 JSON。
    timestamp = _safe_float(raw.get("dt"))  # OpenWeather current weather 的 dt 是 UTC epoch 秒數。
    if timestamp is None:  # 如果沒有 current dt，就無法判斷今天日期。
        return None  # 回傳 None 讓呼叫端改用 forecast 第一筆日期。
    return datetime.fromtimestamp(timestamp, timezone.utc).replace(tzinfo=None) + timedelta(seconds=_timezone_offset(weather_data))  # 轉成本地時間。


def _today_date(weather_data: dict, items: list[dict]) -> object:  # 決定「今天」要使用哪一天的日期。
    current_dt = _current_datetime(weather_data)  # 優先使用 current weather 的當地日期。
    if current_dt is not None:  # 如果 current weather 有時間，就用它當今天。
        return current_dt.date()  # 回傳 current weather 的日期部分。
    if items:  # 如果沒有 current dt 但有 forecast，就用第一筆 forecast 日期。
        return _item_datetime(items[0], weather_data).date()  # 回傳第一筆 forecast 的日期。
    return datetime.now().date()  # 完全沒有資料時用本機日期保底。


def _today_items(weather_data: dict) -> list[dict]:  # 取出今天的 forecast 分時資料。
    items = _require_forecast_items(weather_data)  # 取得分時預報，沒有就丟清楚錯誤。
    target_date = _today_date(weather_data, items)  # 決定要篩選的今天日期。
    rows = [item for item in items if _item_datetime(item, weather_data).date() == target_date]  # 篩出當天的 forecast 項目。
    if rows:  # 如果今天還有預報資料，就直接使用。
        return rows  # 回傳今天的分時資料。
    first_date = _item_datetime(items[0], weather_data).date()  # 如果 current 日期已經沒有 forecast，就改用第一個可用 forecast 日期。
    return [item for item in items if _item_datetime(item, weather_data).date() == first_date]  # 回傳第一個可用日期的分時資料。


def _forecast_points(weather_data: dict) -> list[tuple[datetime, dict]]:  # 將 forecast 資料整理成依時間排序的點位。
    items = _require_forecast_items(weather_data)  # 取得分時預報，沒有就丟清楚錯誤。
    points = [(_item_datetime(item, weather_data), item) for item in items]  # 將每筆資料轉成城市當地時間加原始項目。
    return sorted(points, key=lambda point: point[0])  # 依時間排序後回傳。


def _target_24h_start(weather_data: dict) -> datetime:  # 決定要輸出的完整 00:00 到 23:00 預報日期。
    points = _forecast_points(weather_data)  # 取得所有可用預報點位。
    first_dt = points[0][0]  # 取得第一筆可用預報時間。
    target_date = first_dt.date()  # 預設使用第一筆可用預報所在日期。
    if first_dt.hour != 0 or first_dt.minute != 0:  # 如果第一筆不是當天 00:00，就代表該日期不完整。
        target_date = target_date + timedelta(days=1)  # 改用下一個完整日期，避免只剩一個點。
    return datetime(target_date.year, target_date.month, target_date.day)  # 回傳該日期 00:00。


def _hourly_datetimes(weather_data: dict) -> list[datetime]:  # 建立固定 24 個小時時間點。
    start = _target_24h_start(weather_data)  # 取得完整日期的 00:00。
    return [start + timedelta(hours=hour) for hour in range(24)]  # 回傳 00:00 到 23:00 共 24 個時間點。


def _surrounding_points(points: list[tuple[datetime, dict]], target_dt: datetime) -> tuple[tuple[datetime, dict], tuple[datetime, dict]]:  # 找出目標時間前後最近預報點。
    before = points[0]  # 預設前一點使用第一筆資料。
    after = points[-1]  # 預設後一點使用最後一筆資料。
    for point in points:  # 逐一掃描所有預報點。
        if point[0] <= target_dt:  # 如果該點時間小於或等於目標時間，就更新前一點。
            before = point  # 保存目前最接近的前一點。
        if point[0] >= target_dt:  # 如果該點時間大於或等於目標時間，就找到後一點。
            after = point  # 保存目前最接近的後一點。
            break  # 找到第一個後一點就可以停止。
    return before, after  # 回傳前後兩個點位。


def _item_numeric_value(item: dict, field_name: str) -> float | None:  # 從單筆預報中取出指定數值。
    if field_name == "pop":  # 降雨機率放在 item.pop。
        return _safe_float(_as_dict(item).get("pop"))  # 回傳降雨機率。
    if field_name == "rain_mm":  # 雨量需要從 OpenWeather rain 區塊讀取。
        return _item_rain_mm(item)  # 回傳 rain.1h 或 rain.3h 的毫米數。
    if field_name == "wind_speed":  # 風速可能放在 wind.speed 或 wind_speed。
        return _safe_float(_wind_data(item).get("speed"))  # 回傳風速。
    return _safe_float(_main_data(item).get(field_name))  # 其他欄位從 main 取得。


def _interpolated_value(before: tuple[datetime, dict], after: tuple[datetime, dict], target_dt: datetime, field_name: str) -> float | None:  # 用前後預報點內插出每小時數值。
    before_value = _item_numeric_value(before[1], field_name)  # 取出前一點數值。
    after_value = _item_numeric_value(after[1], field_name)  # 取出後一點數值。
    if before_value is None and after_value is None:  # 如果兩邊都沒有資料，就無法內插。
        return None  # 回傳 None 讓格式化函式顯示無資料。
    if before_value is None:  # 如果只有後一點有資料，就使用後一點。
        return after_value  # 回傳後一點數值。
    if after_value is None:  # 如果只有前一點有資料，就使用前一點。
        return before_value  # 回傳前一點數值。
    total_seconds = (after[0] - before[0]).total_seconds()  # 計算前後點時間距離。
    if total_seconds <= 0:  # 如果兩點時間相同或順序異常，就不能算比例。
        return before_value  # 回傳前一點數值。
    ratio = (target_dt - before[0]).total_seconds() / total_seconds  # 計算目標時間在兩點之間的位置比例。
    ratio = max(0.0, min(1.0, ratio))  # 將比例限制在 0 到 1，避免超出資料範圍。
    return before_value + (after_value - before_value) * ratio  # 回傳線性內插後的數值。


def _nearest_item(points: list[tuple[datetime, dict]], target_dt: datetime) -> dict:  # 找出距離目標時間最近的預報項目。
    return min(points, key=lambda point: abs((point[0] - target_dt).total_seconds()))[1]  # 回傳最近時間點的原始項目。


def _hourly_snapshots(weather_data: dict) -> list[dict]:  # 建立完整 24 小時的每小時天氣快照。
    points = _forecast_points(weather_data)  # 取得可用 forecast 或 hourly 預報點。
    snapshots: list[dict] = []  # 建立每小時快照清單。
    for target_dt in _hourly_datetimes(weather_data):  # 逐一處理 00:00 到 23:00。
        before, after = _surrounding_points(points, target_dt)  # 找出目標時間前後最近的真實預報點。
        nearest = _nearest_item(points, target_dt)  # 找出最近點，用於描述、圖示等非連續資料。
        snapshots.append({  # 加入每小時整理後資料。
            "datetime": target_dt,  # 保存這個快照的當地時間。
            "description": _weather_description_from_item(nearest),  # 保存最接近時間點的天氣描述。
            "temp": _interpolated_value(before, after, target_dt, "temp"),  # 保存實際溫度。
            "feels_like": _interpolated_value(before, after, target_dt, "feels_like"),  # 保存體感溫度。
            "humidity": _interpolated_value(before, after, target_dt, "humidity"),  # 保存濕度。
            "pop": _interpolated_value(before, after, target_dt, "pop"),  # 保存降雨機率。
            "rain_mm": _interpolated_value(before, after, target_dt, "rain_mm"),  # 保存預估雨量毫米數，API 沒提供時保留 None。
            "wind_speed": _interpolated_value(before, after, target_dt, "wind_speed"),  # 保存風速。
        })  # 結束單筆快照。
    return snapshots  # 回傳 24 筆每小時快照。


def _main_data(item: dict) -> dict:  # 取出 forecast 單筆 main 區塊。
    source = _as_dict(item)  # 先確保單筆資料是 dict。
    main = dict(_as_dict(source.get("main")))  # OpenWeather forecast 的溫度、體感與濕度通常放在 main。
    for key in ("temp", "feels_like", "temp_min", "temp_max", "humidity", "pressure"):  # onecall hourly 會把這些欄位直接放在 item 上。
        if key in source and key not in main:  # 如果 main 沒有但外層有，就補進 main。
            main[key] = source.get(key)  # 保存外層欄位值。
    return main  # 回傳統一後的 main 資料。


def _wind_data(item: dict) -> dict:  # 取出 forecast 單筆 wind 區塊。
    source = _as_dict(item)  # 先確保單筆資料是 dict。
    wind = dict(_as_dict(source.get("wind")))  # OpenWeather forecast 的風速通常放在 wind.speed。
    if "wind_speed" in source and "speed" not in wind:  # onecall hourly 會把風速放在 wind_speed。
        wind["speed"] = source.get("wind_speed")  # 將 onecall wind_speed 統一成 speed。
    return wind  # 回傳統一後的 wind 資料。


def _weather_description_from_item(item: dict) -> str:  # 取出 forecast 單筆天氣描述。
    weather_list = _as_dict(item).get("weather")  # OpenWeather weather 是清單。
    if isinstance(weather_list, list) and weather_list:  # 如果清單有內容，就取第一個描述。
        first = _as_dict(weather_list[0])  # 取第一筆天氣狀況。
        description = str(first.get("description") or first.get("main") or "").strip()  # 優先使用本地化 description。
        if description:  # 如果有描述就回傳。
            return description  # 回傳天氣描述。
    return MISSING_TEXT  # 沒有描述時顯示無資料。


def _weather_description_from_current(weather_data: dict) -> str:  # 取出 current weather 的天氣描述。
    current = _current_summary(weather_data)  # 取得目前天氣摘要。
    description = str(current.get("description") or "").strip()  # 舊摘要格式會有 description。
    if description:  # 如果摘要有描述，就直接回傳。
        return description  # 回傳摘要描述。
    raw_weather = _current_raw(weather_data).get("weather")  # 原始 current JSON 的 weather 是清單。
    if isinstance(raw_weather, list) and raw_weather:  # 如果原始清單有內容，就取第一筆。
        return str(_as_dict(raw_weather[0]).get("description") or _as_dict(raw_weather[0]).get("main") or MISSING_TEXT).strip()  # 回傳描述或保底文字。
    return MISSING_TEXT  # 沒有任何描述時顯示無資料。


def _current_value(weather_data: dict, summary_key: str, raw_key: str):  # 從 current 摘要或 raw main 讀取指定數值。
    current = _current_summary(weather_data)  # 取得目前天氣摘要。
    if summary_key in current:  # 如果整理後摘要已有欄位，就優先使用。
        return current.get(summary_key)  # 回傳摘要欄位。
    return _as_dict(_current_raw(weather_data).get("main")).get(raw_key)  # 否則從 raw main 讀取 OpenWeather 欄位。


def _format_number(value, suffix: str = "", digits: int = 0) -> str:  # 將數值格式化成人類可讀文字。
    number = _safe_float(value)  # 先安全轉成 float。
    if number is None:  # 缺值時不能顯示 0 誤導使用者。
        return MISSING_TEXT  # 回傳無資料。
    text = f"{number:.{digits}f}" if digits > 0 else f"{round(number):.0f}"  # 依需要顯示小數或整數。
    return f"{text}{suffix}"  # 接上單位後回傳。


def _format_temp(value) -> str:  # 將溫度格式化成攝氏文字。
    return _format_number(value, "°C", 1)  # 溫度保留一位小數。


def _format_humidity(value) -> str:  # 將濕度格式化成百分比文字。
    return _format_number(value, "%", 0)  # 濕度顯示整數百分比。


def _format_probability(value) -> str:  # 將降雨機率格式化成百分比文字。
    number = _safe_float(value)  # OpenWeather pop 通常是 0 到 1。
    if number is None:  # 缺值時顯示無資料。
        return MISSING_TEXT  # 回傳無資料。
    if 0 <= number <= 1:  # 如果是 0 到 1，就轉成百分比。
        number *= 100  # 將 0.86 轉成 86。
    return f"{round(number):.0f}%"  # 回傳整數百分比。


def _format_rain_mm(value) -> str:  # 將雨量毫米數格式化成人類可讀文字。
    number = _safe_float(value)  # 先安全轉成 float。
    if number is None:  # 如果 API 沒提供雨量資料。
        return MISSING_TEXT  # 回傳無資料。
    return f"{number:.1f}mm"  # 雨量保留一位小數。


def _format_wind(value) -> str:  # 將風速格式化成 m/s。
    return _format_number(value, "m/s", 1)  # 風速保留一位小數，單位不留空白避免 PNG 表格自動換行。


def _time_label(dt: datetime) -> str:  # 將 datetime 格式化成 HH:MM。
    return dt.strftime("%H:%M")  # 回傳 24 小時制時間。


def _date_label(dt: datetime) -> str:  # 將 datetime 格式化成表格日期。
    weekday = WEEKDAY_NAMES[dt.weekday()]  # 取出繁體中文星期。
    return f"{dt.strftime('%m/%d')}（{weekday}）"  # 回傳月日與星期。


def _average(values: list) -> float | None:  # 計算忽略缺值的平均。
    numbers = [_safe_float(value) for value in values]  # 將所有值安全轉成 float 或 None。
    valid = [number for number in numbers if number is not None]  # 只留下真正有數字的資料。
    if not valid:  # 沒有任何有效值時不能算平均。
        return None  # 回傳 None 讓格式化函式顯示無資料。
    return sum(valid) / len(valid)  # 回傳平均值。


def _maximum(values: list) -> float | None:  # 計算忽略缺值的最大值。
    valid = [number for number in (_safe_float(value) for value in values) if number is not None]  # 只保留有效數字。
    return max(valid) if valid else None  # 有資料就回最大值，沒有就回 None。


def _minimum(values: list) -> float | None:  # 計算忽略缺值的最小值。
    valid = [number for number in (_safe_float(value) for value in values) if number is not None]  # 只保留有效數字。
    return min(valid) if valid else None  # 有資料就回最小值，沒有就回 None。


def _dominant_description(items: list[dict]) -> str:  # 從多筆 forecast 中挑出最常見天氣描述。
    descriptions = [_weather_description_from_item(item) for item in items]  # 取出每筆描述。
    descriptions = [description for description in descriptions if description and description != MISSING_TEXT]  # 移除空值與無資料。
    if not descriptions:  # 如果完全沒有描述，就回無資料。
        return MISSING_TEXT  # 回傳無資料。
    return Counter(descriptions).most_common(1)[0][0]  # 回傳出現次數最多的描述。


def _condition_family(text: str) -> str:  # 將詳細天氣描述整理成相似天氣類別。
    lowered = str(text or "").strip().lower()  # 轉成小寫方便比對英文 main。
    if any(word in lowered for word in ("thunder", "雷")):  # 辨識雷雨。
        return "雷雨"  # 回傳雷雨類別。
    if any(word in lowered for word in ("rain", "drizzle", "雨")):  # 辨識雨或毛毛雨。
        return "雨"  # 回傳雨類別。
    if any(word in lowered for word in ("snow", "雪")):  # 辨識雪。
        return "雪"  # 回傳雪類別。
    if any(word in lowered for word in ("cloud", "雲", "陰")):  # 辨識多雲或陰天。
        return "多雲"  # 回傳多雲類別。
    if any(word in lowered for word in ("clear", "晴")):  # 辨識晴天。
        return "晴"  # 回傳晴天類別。
    return lowered or MISSING_TEXT  # 其他描述用原文字當類別。


def _period_key(item: dict) -> tuple:  # 建立相似天氣分組 key。
    main = _main_data(item)  # 取得 main 區塊。
    description = _weather_description_from_item(item)  # 取得天氣描述。
    temp = _safe_float(main.get("temp"))  # 取得實際溫度。
    humidity = _safe_float(main.get("humidity"))  # 取得濕度。
    pop = _safe_float(_as_dict(item).get("pop"))  # 取得降雨機率。
    temp_bucket = round((temp or 0) / 3) if temp is not None else None  # 溫度每 3 度視為相似。
    humidity_bucket = round((humidity or 0) / 15) if humidity is not None else None  # 濕度每 15% 視為相似。
    pop_bucket = round((pop or 0) / 0.25) if pop is not None else None  # 降雨機率每 25% 視為相似。
    return (_condition_family(description), temp_bucket, humidity_bucket, pop_bucket)  # 回傳可比較的相似條件。


def _city_label(weather_data: dict) -> str:  # 取得城市顯示名稱。
    current = _current_summary(weather_data)  # 取得目前天氣摘要。
    forecast_city = _as_dict(_forecast_data(weather_data).get("city"))  # 取得 forecast city。
    name = current.get("city_name") or forecast_city.get("name") or _current_raw(weather_data).get("name") or "指定城市"  # 依序找城市名稱。
    country = current.get("country") or _as_dict(_current_raw(weather_data).get("sys")).get("country") or forecast_city.get("country") or ""  # 依序找國家代碼。
    return f"{name}, {country}".strip(" ,")  # 回傳城市與國家，並清掉多餘標點。


def _summary_descriptions(weather_data: dict, hourly_rows: list[dict]) -> list[str]:  # 整理摘要要參考的所有天氣描述。
    descriptions = [_weather_description_from_current(weather_data)]  # 先放入目前摘要描述。
    descriptions.extend(str(row.get("description") or "").strip() for row in hourly_rows)  # 加入 24 小時快照中的描述。
    return [description for description in descriptions if description and description != MISSING_TEXT]  # 移除空值和無資料。


def _contains_any_weather_word(descriptions: list[str], words: tuple[str, ...]) -> bool:  # 判斷描述中是否包含任一指定關鍵字。
    text = " ".join(descriptions).lower()  # 將所有描述合併並轉成小寫方便比對。
    return any(word.lower() in text for word in words)  # 只要任一關鍵字存在就回傳 True。


def _temperature_advice(max_temp: float | None, min_temp: float | None, rain_chance: float | None) -> str:  # 依溫度與降雨產生穿著建議。
    if max_temp is not None and max_temp >= 32:  # 高溫天氣要提醒透氣防曬。
        base = "穿著建議以輕薄透氣短袖、排汗材質和防曬外套為主，白天外出記得補水、防曬，避免長時間曝曬。"  # 建立炎熱天氣建議。
    elif min_temp is not None and min_temp <= 18:  # 偏涼天氣要提醒加外套。
        base = "穿著建議採洋蔥式穿搭，準備薄外套或長袖，早晚體感偏涼時可以加一層，白天再依體感調整。"  # 建立偏涼天氣建議。
    else:  # 一般溫度給出日常穿著建議。
        base = "穿著建議以短袖或薄長袖搭配輕便外套為主，若長時間在戶外活動，可以依體感溫度調整衣物。"  # 建立一般天氣建議。
    if rain_chance is not None and rain_chance >= 0.5:  # 降雨機率偏高時補上雨具提醒。
        base += " 降雨機率偏高，建議攜帶折疊傘、輕便雨衣或防水外套，鞋子盡量選防滑材質。"  # 加上雨具建議。
    return base  # 回傳完整穿著建議。


def _weather_warning_text(descriptions: list[str], rain_chance: float | None, wind_speed: float | None, humidity: float | None) -> str:  # 依預報產生災害與劇烈天氣警示。
    warnings: list[str] = []  # 建立警示清單。
    if _contains_any_weather_word(descriptions, ("typhoon", "hurricane", "tropical cyclone", "颱風", "台風", "熱帶氣旋")):  # 偵測颱風或熱帶氣旋。
        warnings.append("有颱風或熱帶氣旋訊號時，請避免前往海邊、山區和空曠強風處，固定門窗與陽台物品。")  # 加入颱風警示。
    if _contains_any_weather_word(descriptions, ("tornado", "龍捲風", "龍卷風")):  # 偵測龍捲風。
        warnings.append("若出現龍捲風或漏斗雲警訊，應立刻進入堅固建築物低樓層，遠離窗戶與大片玻璃。")  # 加入龍捲風警示。
    if _contains_any_weather_word(descriptions, ("thunder", "lightning", "雷", "閃電")):  # 偵測雷雨或閃電。
        warnings.append("有雷雨或閃電風險時，避免在樹下、空曠地、河堤或屋頂停留，暫停戶外運動。")  # 加入雷雨警示。
    if _contains_any_weather_word(descriptions, ("storm", "squall", "暴風", "暴風雨", "風暴", "狂風")):  # 偵測暴風雨或陣風。
        warnings.append("若有暴風雨或強陣風，請留意招牌、路樹、施工鷹架與機車騎乘穩定性。")  # 加入暴風雨警示。
    if rain_chance is not None and rain_chance >= 0.8:  # 降雨機率很高時提醒積淹水和山區。
        warnings.append("降雨機率很高，低窪地區要注意積淹水，山區、溪邊和邊坡地帶需留意落石、坍方與土石流風險。")  # 加入暴雨土石流警示。
    if wind_speed is not None and wind_speed >= 10.8:  # 蒲福風級約 6 級以上可視為強風提醒。
        warnings.append("預估風速偏強，外出請小心強風，騎車、撐傘和高架橋路段都要放慢速度。")  # 加入強風警示。
    if humidity is not None and humidity >= 85 and rain_chance is not None and rain_chance >= 0.6:  # 高濕加高降雨代表體感悶濕且雨勢可能持續。
        warnings.append("濕度偏高且有雨，衣物不易乾，外出請預留交通時間並留意濕滑路面。")  # 加入濕滑提醒。
    if warnings:  # 如果有警示，就組成警示段落。
        return "天氣警示：" + " ".join(warnings)  # 回傳所有警示。
    return "天氣警示：目前預報未顯示颱風、龍捲風、明顯雷雨或暴風雨訊號；仍建議持續留意中央氣象署、地方政府災防警報與即時雷達，山區活動需特別注意午後降雨和邊坡狀況。"  # 沒有明顯危險時仍提醒官方警報。


def _item_rain_mm(item: dict) -> float | None:  # 從 forecast 單筆資料估算雨量毫米數。
    rain = _as_dict(_as_dict(item).get("rain"))  # OpenWeather 的雨量通常放在 rain 區塊。
    one_hour = _safe_float(rain.get("1h"))  # 讀取 1 小時雨量。
    three_hour = _safe_float(rain.get("3h"))  # 讀取 3 小時雨量。
    if one_hour is not None:  # 如果有 1 小時雨量，就優先使用。
        return one_hour  # 回傳 1 小時雨量。
    if three_hour is not None:  # 如果只有 3 小時雨量，就用總量判斷大雨風險。
        return three_hour  # 回傳 3 小時雨量。
    return None  # 沒有雨量資料時回傳 None。


def get_weather_alert_messages(weather_data: dict) -> list[str]:  # 產生危險天氣風險訊息。
    items = _forecast_items(weather_data)  # 取得 forecast 或 hourly 預報資料。
    hourly_rows = _hourly_snapshots(weather_data) if items else []  # 有預報資料時整理成 24 小時快照。
    descriptions = _summary_descriptions(weather_data, hourly_rows)  # 整理所有天氣描述文字。
    descriptions.extend(_weather_description_from_item(item) for item in items)  # 同時掃原始 forecast 描述，避免內插快照漏掉颱風或龍捲風文字。
    rain_chance = _maximum([row.get("pop") for row in hourly_rows]) if hourly_rows else None  # 計算 24 小時最高降雨機率。
    wind_speed = _maximum([row.get("wind_speed") for row in hourly_rows]) if hourly_rows else None  # 計算 24 小時最大平均風速。
    wind_gust = _maximum([_wind_data(item).get("gust") for item in items]) if items else None  # 計算 forecast 原始資料中的最大陣風。
    rain_amount = _maximum([_item_rain_mm(item) for item in items]) if items else None  # 計算 forecast 原始資料中的最大雨量。
    alerts: list[str] = []  # 建立危險天氣風險訊息清單。
    has_rain = _contains_any_weather_word(descriptions, ("rain", "drizzle", "shower", "雨"))  # 判斷是否有雨相關描述。
    if _contains_any_weather_word(descriptions, ("typhoon", "hurricane", "tropical cyclone", "颱風", "台風", "熱帶氣旋")):  # 偵測颱風或熱帶氣旋。
        alerts.append("颱風或熱帶氣旋風險：請固定門窗與陽台物品，避免前往海邊、山區、河岸和空曠強風處。")  # 加入颱風通知。
    if _contains_any_weather_word(descriptions, ("tornado", "龍捲風", "龍卷風")):  # 偵測龍捲風。
        alerts.append("龍捲風風險：若看到漏斗雲或收到官方警報，請立刻進入堅固建築物低樓層並遠離窗戶。")  # 加入龍捲風通知。
    if _contains_any_weather_word(descriptions, ("thunder", "lightning", "雷", "閃電")):  # 偵測雷雨或閃電。
        alerts.append("雷雨或打雷風險：請暫停戶外運動，避免在樹下、空曠地、屋頂、河堤或水邊停留。")  # 加入雷雨通知。
    if _contains_any_weather_word(descriptions, ("storm", "squall", "暴風", "暴風雨", "風暴", "狂風", "暴雨", "豪雨")):  # 偵測暴風雨、暴雨或狂風描述。
        alerts.append("暴風雨風險：請留意招牌、路樹、施工鷹架與機車騎乘安全，必要時延後外出。")  # 加入暴風雨通知。
    if (rain_amount is not None and rain_amount >= 10) or (rain_chance is not None and rain_chance >= 0.8 and has_rain):  # 依雨量或高降雨機率判斷大雨。
        alerts.append("大雨風險：低窪地區請注意積淹水，外出攜帶雨具並預留交通時間。")  # 加入大雨通知。
    if (rain_amount is not None and rain_amount >= 15) or (rain_chance is not None and rain_chance >= 0.85 and has_rain):  # 大雨明顯時提醒山區災害。
        alerts.append("土石流與邊坡風險：山區、溪邊、邊坡道路請提高警覺，避免進入封閉步道或溪床。")  # 加入土石流通知。
    if (wind_speed is not None and wind_speed >= 10.8) or (wind_gust is not None and wind_gust >= 15):  # 依平均風或陣風判斷強風。
        alerts.append("強風風險：騎車、撐傘、高架橋路段與空曠處請放慢速度，陽台物品先收好。")  # 加入強風通知。
    return alerts  # 回傳危險天氣風險清單，沒有危險時回傳空清單。


def get_current_weather_summary(weather_data: dict) -> str:  # 產生當天天氣摘要文字。
    current = _current_summary(weather_data)  # 取得目前天氣摘要。
    description = _weather_description_from_current(weather_data)  # 取得目前天氣描述。
    hourly_rows = _hourly_snapshots(weather_data) if _forecast_items(weather_data) else []  # 有 forecast 時使用完整 24 小時資料。
    rain_chance = _maximum([row.get("pop") for row in hourly_rows]) if hourly_rows else None  # 取完整 24 小時最高降雨機率。
    max_hourly_temp = _maximum([row.get("temp") for row in hourly_rows]) if hourly_rows else None  # 取完整 24 小時最高溫。
    min_hourly_temp = _minimum([row.get("temp") for row in hourly_rows]) if hourly_rows else None  # 取完整 24 小時最低溫。
    max_wind_speed = _maximum([row.get("wind_speed") for row in hourly_rows]) if hourly_rows else None  # 取完整 24 小時最大風速。
    avg_humidity = _average([row.get("humidity") for row in hourly_rows]) if hourly_rows else None  # 取完整 24 小時平均濕度。
    descriptions = _summary_descriptions(weather_data, hourly_rows)  # 整理預報描述，供建議與警示使用。
    temp = current.get("temperature_celsius", _current_value(weather_data, "temperature_celsius", "temp"))  # 取得目前實際溫度。
    feels_like = current.get("feels_like", _current_value(weather_data, "feels_like", "feels_like"))  # 取得目前體感溫度。
    humidity = current.get("humidity", _current_value(weather_data, "humidity", "humidity"))  # 取得目前濕度。
    wind_speed = current.get("wind_speed", _as_dict(_current_raw(weather_data).get("wind")).get("speed"))  # 取得目前風速。
    temp_max = max_hourly_temp if max_hourly_temp is not None else current.get("temp_max", _current_value(weather_data, "temp_max", "temp_max"))  # 優先使用 24 小時最高溫。
    temp_min = min_hourly_temp if min_hourly_temp is not None else current.get("temp_min", _current_value(weather_data, "temp_min", "temp_min"))  # 優先使用 24 小時最低溫。
    summary_line = f"{_city_label(weather_data)} 今日天氣以{description}為主，預估溫度約 {_format_temp(temp_min)} 到 {_format_temp(temp_max)}，目前溫度 {_format_temp(temp)}、體感 {_format_temp(feels_like)}，濕度 {_format_humidity(humidity)}，今日最高降雨機率 {_format_probability(rain_chance)}，最大風速約 {_format_wind(max_wind_speed if max_wind_speed is not None else wind_speed)}。"  # 建立至少包含天氣、溫度、濕度、降雨與風速的長摘要。
    advice_line = _temperature_advice(_safe_float(temp_max), _safe_float(temp_min), _safe_float(rain_chance))  # 建立穿著與外出建議。
    warning_line = _weather_warning_text(descriptions, _safe_float(rain_chance), _safe_float(max_wind_speed if max_wind_speed is not None else wind_speed), _safe_float(avg_humidity if avg_humidity is not None else humidity))  # 建立劇烈天氣與災害警示。
    lines = [  # 建立摘要文字清單。
        summary_line,  # 第一段是完整天氣摘要。
        advice_line,  # 第二段是穿著和外出建議。
        warning_line,  # 第三段是災害與劇烈天氣警示。
    ]  # 結束摘要文字清單。
    return "\n".join(lines)  # 將摘要接成可放進 Discord Embed 的文字。


def get_weekly_weather_table(weather_data: dict) -> tuple[list[str], list[list[str]]]:  # 產生整週天氣表格資料。
    items = _require_forecast_items(weather_data)  # 取得 OpenWeather forecast 分時資料。
    grouped: dict[object, list[dict]] = defaultdict(list)  # 建立依日期分組的字典。
    for item in items:  # 逐筆處理 forecast 資料。
        grouped[_item_datetime(item, weather_data).date()].append(item)  # 依城市當地日期分組。
    rows: list[list[str]] = []  # 建立表格列資料。
    for day in sorted(grouped.keys())[:7]:  # 最多整理七個日期，forecast 不足七天時顯示 API 有提供的日期。
        day_items = grouped[day]  # 取出該日期所有分時資料。
        first_dt = _item_datetime(day_items[0], weather_data)  # 取得該日期第一筆時間，用來格式化日期。
        temps_max = [_main_data(item).get("temp_max", _main_data(item).get("temp")) for item in day_items]  # 收集最高溫候選值。
        temps_min = [_main_data(item).get("temp_min", _main_data(item).get("temp")) for item in day_items]  # 收集最低溫候選值。
        humidities = [_main_data(item).get("humidity") for item in day_items]  # 收集濕度值。
        pops = [_as_dict(item).get("pop") for item in day_items]  # 收集降雨機率值。
        winds = [_wind_data(item).get("speed") for item in day_items]  # 收集風速值。
        rows.append([_date_label(first_dt), _dominant_description(day_items), _format_temp(_maximum(temps_max)), _format_temp(_minimum(temps_min)), _format_humidity(_average(humidities)), _format_probability(_maximum(pops)), _format_wind(_average(winds))])  # 加入該日表格列。
    return WEEKLY_HEADERS, rows  # 回傳表頭與表格資料。


def get_today_hourly_table(weather_data: dict) -> tuple[list[str], list[list[str]]]:  # 產生當天每小時或每三小時表格資料。
    rows: list[list[str]] = []  # 建立表格列資料。
    for snapshot in _hourly_snapshots(weather_data):  # 逐筆處理完整 24 小時快照。
        rows.append([_time_label(snapshot["datetime"]), snapshot.get("description") or MISSING_TEXT, _format_temp(snapshot.get("temp")), _format_temp(snapshot.get("feels_like")), _format_humidity(snapshot.get("humidity")), _format_probability(snapshot.get("pop")), _format_wind(snapshot.get("wind_speed"))])  # 加入每小時表格列。
    return HOURLY_HEADERS, rows  # 回傳表頭與表格資料。


def get_today_rain_table(weather_data: dict) -> tuple[list[str], list[list[str]]]:  # 產生今天整天降雨量與降雨機率表格資料。
    headers = ["時間", "天氣", "降雨機率", "預估雨量", "濕度", "風速"]  # 設定降雨表格欄位。
    rows: list[list[str]] = []  # 建立表格列資料。
    for snapshot in _hourly_snapshots(weather_data):  # 逐筆處理完整 24 小時快照。
        pop_value = _safe_float(snapshot.get("pop"))  # 取出降雨機率，供雨量缺值時判斷。
        rain_value = _safe_float(snapshot.get("rain_mm"))  # 取出 API 提供或內插的雨量毫米數。
        if rain_value is None and pop_value is not None and pop_value <= 0:  # 如果降雨機率是 0 且沒有雨量資料。
            rain_value = 0.0  # 將無雨時段顯示成 0.0mm。
        rows.append([_time_label(snapshot["datetime"]), snapshot.get("description") or MISSING_TEXT, _format_probability(pop_value), _format_rain_mm(rain_value), _format_humidity(snapshot.get("humidity")), _format_wind(snapshot.get("wind_speed"))])  # 加入每小時降雨列。
    return headers, rows  # 回傳表頭與表格資料。


def group_today_weather_periods(weather_data: dict) -> tuple[list[str], list[list[str]]]:  # 將今天相似天氣整理成幾點到幾點格式。
    snapshots = _hourly_snapshots(weather_data)  # 取得完整 24 小時快照。
    rows: list[list[str]] = []  # 建立表格列資料。
    for start_hour in range(0, 24, 3):  # 固定整理成 00-03、03-06 到 21-24 共 8 列。
        group = snapshots[start_hour:start_hour + 3]  # 取出該三小時區間的快照。
        start_label = f"{start_hour:02d}:00"  # 建立區間開始時間。
        end_label = "24:00" if start_hour + 3 == 24 else f"{start_hour + 3:02d}:00"  # 建立區間結束時間。
        descriptions = [str(snapshot.get("description") or MISSING_TEXT) for snapshot in group]  # 收集該區間天氣描述。
        description = Counter([item for item in descriptions if item != MISSING_TEXT]).most_common(1)[0][0] if any(item != MISSING_TEXT for item in descriptions) else MISSING_TEXT  # 取該區間最常見天氣。
        rows.append([f"{start_label}-{end_label}", description, _format_temp(_average([snapshot.get("temp") for snapshot in group])), _format_temp(_average([snapshot.get("feels_like") for snapshot in group])), _format_humidity(_average([snapshot.get("humidity") for snapshot in group])), _format_probability(_maximum([snapshot.get("pop") for snapshot in group])), _format_wind(_average([snapshot.get("wind_speed") for snapshot in group]))])  # 加入固定三小時區間列。
    return PERIOD_HEADERS, rows  # 回傳表頭與表格資料。


def extract_today_temperature_series(weather_data: dict) -> tuple[list[str], list[float | None], list[float | None]]:  # 抽出今天溫度折線圖資料。
    times: list[str] = []  # 建立時間標籤清單。
    real_temps: list[float | None] = []  # 建立實際溫度清單。
    feels_like_temps: list[float | None] = []  # 建立體感溫度清單。
    for snapshot in _hourly_snapshots(weather_data):  # 逐筆處理完整 24 小時快照。
        times.append(_time_label(snapshot["datetime"]))  # 加入時間標籤。
        real_temps.append(_safe_float(snapshot.get("temp")))  # 加入實際溫度，缺值保留 None。
        feels_like_temps.append(_safe_float(snapshot.get("feels_like")))  # 加入體感溫度，缺值保留 None。
    return times, real_temps, feels_like_temps  # 回傳折線圖需要的三組資料。


def extract_today_humidity_series(weather_data: dict) -> tuple[list[str], list[float | None]]:  # 抽出今天濕度折線圖資料。
    times: list[str] = []  # 建立時間標籤清單。
    humidity_values: list[float | None] = []  # 建立濕度清單。
    for snapshot in _hourly_snapshots(weather_data):  # 逐筆處理完整 24 小時快照。
        times.append(_time_label(snapshot["datetime"]))  # 加入時間標籤。
        humidity_values.append(_safe_float(snapshot.get("humidity")))  # 加入濕度，缺值保留 None。
    return times, humidity_values  # 回傳折線圖需要的資料。
