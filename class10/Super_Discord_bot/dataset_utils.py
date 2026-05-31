import urllib.request as urlrequest  # 匯入 urllib.request：用來發送 HTTP 請求。
import urllib.parse as urlparse  # 匯入 urllib.parse：用來解析與合併 URL。
import io  # 匯入 io：用來處理記憶體中的位元組流，避免磁碟殘留。
import re  # 匯入 re：用來進行正則表達式比對。
import os  # 匯入 os：用來處理路徑與檔案名稱。
import pandas as pd  # 匯入 pandas：最強大的結構化資料處理工具。
import json  # 匯入 json：處理 JSON 格式資料。
import ssl  # 匯入 ssl：處理 HTTPS 憑證驗證問題。
from bs4 import BeautifulSoup  # 匯入 BeautifulSoup：解析 HTML 網頁。

# 設定常數限制，避免資源耗盡。
MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024  # 最大下載限制：20MB。
DOWNLOAD_TIMEOUT = 30  # 下載逾時：30秒。
MAX_DATA_LINKS_TO_TRY = 5  # 每個網頁最多嘗試下載前 5 個資料連結。

def fetch_html(url: str) -> str:
    """取得指定 URL 的 HTML 內容，支援逾時與 User-Agent。"""
    try:  # 嘗試執行網路請求。
        req = urlrequest.Request(  # 建立請求物件。
            url,  # 目標網址。
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},  # 模擬現代瀏覽器。
            method="GET",  # 使用 GET 方法。
        )
        with urlrequest.urlopen(req, timeout=12) as resp:  # 設定 12 秒逾時，避免卡死。
            return resp.read().decode("utf-8", errors="replace")  # 讀取並使用 UTF-8 解碼，錯誤時取代。
    except Exception as e:  # 捕捉連線、逾時或讀取錯誤。
        print(f"fetch_html 失敗 ({url})：{type(e).__name__}: {e}")  # 在後台印出錯誤日誌。
        return ""  # 失敗時回傳空字串。

def extract_data_links(html: str, base_url: str) -> list[dict]:
    """從 HTML 中擷取各類資料檔案（CSV, JSON, XLSX, XLS, ODS）的下載連結。"""
    if not html:  # 檢查輸入是否有效。
        return []
    soup = BeautifulSoup(html, "html.parser")  # 解析 HTML。
    links = []  # 存放結果的清單。
    seen_urls = set()  # 用來去重。

    # 定義目標副檔名與對應標記。
    data_exts = {
        ".csv": "CSV",
        ".json": "JSON",
        ".xlsx": "XLSX",
        ".xls": "XLS",
        ".ods": "ODS"
    }

    # 遍歷所有連結。
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()  # 取得連結。
        text = a.get_text().upper().strip()  # 取得連結文字。
        full_url = urlparse.urljoin(base_url, href)  # 轉換為絕對路徑。
        
        if full_url in seen_urls:  # 略過重複連結。
            continue

        file_type = None  # 偵測檔案類型。
        
        # 1. 根據副檔名判斷。
        parsed_path = urlparse.urlparse(full_url).path.lower()
        for ext, label in data_exts.items():
            if parsed_path.endswith(ext):
                file_type = label.lower()
                break
        
        # 2. 根據 a 標籤文字判斷。
        if not file_type:
            for label in data_exts.values():
                if label in text:
                    file_type = label.lower()
                    break
        
        # 3. 根據 URL Query 或關鍵字判斷。
        if not file_type:
            query = urlparse.urlparse(full_url).query.lower()
            if "format=csv" in query or "download" in text.lower() or "下載" in text:
                if "csv" in query or "csv" in text.lower(): file_type = "csv"
                elif "json" in query or "json" in text.lower(): file_type = "json"
                elif "xlsx" in query or "xlsx" in text.lower(): file_type = "xlsx"

        if file_type:
            links.append({"url": full_url, "type": file_type, "text": text})
            seen_urls.add(full_url)
            if len(links) >= 15:  # 限制抓取數量，避免單頁過多連結。
                break
                
    return links

def download_data_safely(url: str) -> tuple[bytes | None, str]:
    """安全下載資料檔，嚴格遵守大小與時間限制，支援 SSL 驗證失敗的 fallback。"""
    def _do_download(ctx=None) -> tuple[bytes | None, str]:  # 逐行註解：內部執行下載的輔助函式。
        try:  # 逐行註解：嘗試執行網路請求。
            req = urlrequest.Request(  # 逐行註解：建立請求物件。
                url,   # 逐行註解：目標下載網址。
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}  # 逐行註解：設定標頭。
            )
            with urlrequest.urlopen(req, timeout=DOWNLOAD_TIMEOUT, context=ctx) as resp:  # 逐行註解：開啟連線。
                content_length = resp.headers.get("Content-Length")  # 逐行註解：檢查回傳的長度。
                if content_length and int(content_length) > MAX_DOWNLOAD_SIZE:  # 逐行註解：若超過限制。
                    return None, f"資料檔超過限制 ({int(content_length)//1024//1024}MB > 20MB)"  # 逐行註解：回傳錯誤。
                
                content_type = resp.headers.get("Content-Type", "").lower()  # 逐行註解：取得檔案類型。
                buffer = io.BytesIO()  # 逐行註解：建立記憶體緩衝區。
                downloaded = 0  # 逐行註解：累計下載位元組。
                while True:  # 逐行註解：循環讀取資料區塊。
                    chunk = resp.read(1024 * 1024)  # 逐行註解：每次讀 1MB。
                    if not chunk: break  # 逐行註解：讀取完畢。
                    downloaded += len(chunk)  # 逐行註解：累計大小。
                    if downloaded > MAX_DOWNLOAD_SIZE: return None, "下載中偵測到資料檔超過 20MB 限制"  # 逐行註解：中途檢查。
                    buffer.write(chunk)  # 逐行註解：寫入緩衝區。
                return buffer.getvalue(), content_type  # 逐行註解：成功下載，回傳位元組與類型。
        except Exception as e:  # 逐行註解：捕捉下載過程的所有例外。
            return None, str(e)  # 逐行註解：回傳失敗原因。

    # 第一步：嘗試正常下載（驗證 SSL 憑證）。
    data, status = _do_download(ctx=None)  # 逐行註解：執行第一次嘗試。
    
    # 第二步：如果因為 SSL 憑證驗證失敗（常見於政府網站憑證過期或缺少中繼憑證）。
    ssl_errors = ["CERTIFICATE_VERIFY_FAILED", "SSLCertVerificationError"]  # 逐行註解：定義 SSL 相關關鍵字。
    if data is None and any(err in status for err in ssl_errors):  # 逐行註解：判斷是否為 SSL 錯誤。
        print(f"DEBUG: SSL 驗證失敗，改用不驗證 SSL fallback 重新下載：{url}")  # 逐行註解：輸出日誌。
        unverified_ctx = ssl._create_unverified_context()  # 逐行註解：建立不驗證憑證的 context。
        return _do_download(ctx=unverified_ctx)  # 逐行註解：改用不驗證模式重試下載。
        
    return data, status  # 逐行註解：回傳最後一次嘗試的結果。

def read_table_safely(data_bytes: bytes, file_type: str) -> pd.DataFrame | None:
    """從記憶體位元組讀取表格資料，支援多種格式與編碼。"""
    if not data_bytes:
        return None
    
    try:
        if file_type == "csv":
            encodings = ["utf-8-sig", "utf-8", "cp950", "big5"]
            for enc in encodings:
                try:
                    df = pd.read_csv(io.BytesIO(data_bytes), encoding=enc, on_bad_lines="skip")
                    if not df.empty: return df
                except: continue
        
        elif file_type == "json":
            try:
                # 嘗試直接讀取（可能是 list of dicts）。
                df = pd.read_json(io.BytesIO(data_bytes))
                if not df.empty: return df
            except:
                # 備援：手動解析看是否為特定的政府資料格式。
                data = json.loads(data_bytes.decode("utf-8", errors="replace"))
                if isinstance(data, dict):
                    # 找尋包含資料清單的 key。
                    for key in ["data", "records", "result", "items"]:
                        if key in data and isinstance(data[key], list):
                            return pd.DataFrame(data[key])
                elif isinstance(data, list):
                    return pd.DataFrame(data)
        
        elif file_type in ["xlsx", "xls"]:
            # 使用 pandas 讀取 Excel。
            return pd.read_excel(io.BytesIO(data_bytes))
            
        elif file_type == "ods":
            # 讀取 ODS 需要 odfpy。
            try:
                return pd.read_excel(io.BytesIO(data_bytes), engine="odf")
            except Exception as e:
                print(f"DEBUG: 讀取 ODS 失敗（可能缺套件）: {e}")
                return None
    except Exception as e:
        print(f"DEBUG: read_table_safely 發生錯誤: {e}")
        
    return None

def infer_columns(df: pd.DataFrame, user_query: str) -> dict:
    """根據 DataFrame 內容與使用者問題，動態推論關鍵欄位。"""
    cols = df.columns.tolist()
    norm_query = user_query.lower()
    res = {"time": None, "total": None, "young": None, "working": None, "old": None, "category": None}

    # 1. 識別時間欄位。
    time_kws = ["年度", "年份", "統計年", "統計期", "年月", "日期", "year", "date", "period"]
    for col in cols:
        if any(kw in str(col).lower() for kw in time_kws):
            res["time"] = col
            break

    # 2. 識別人口結構欄位。
    pop_struct = {
        "young": ["幼年", "兒童", "0至14", "0-14", "014"],
        "working": ["工作年齡", "青壯年", "15至64", "15-64", "1564"],
        "old": ["老年", "高齡", "65歲以上", "65+", "65及以上"]
    }
    for key, kws in pop_struct.items():
        for col in cols:
            if any(kw in str(col) for kw in kws):
                res[key] = col
                break

    # 3. 識別數值/總量欄位。
    total_kws = ["總計", "全國", "總人口", "合計", "人口數", "total", "population", "value"]
    for col in cols:
        col_s = str(col).lower()
        if any(kw in col_s for kw in total_kws) and "年齡" not in col_s and "比率" not in col_s:
            res["total"] = col
            break
            
    # 4. 識別分類欄位（如果不是人口資料，用來當圓餅圖的項目）。
    if not res["young"]:
        for col in cols:
            if any(kw in str(col).lower() for kw in ["類別", "項目", "種類", "category", "type"]):
                res["category"] = col
                break

    print(f"DEBUG: infer_columns 結果: {res}")
    return res

def filter_total_data(df: pd.DataFrame) -> pd.DataFrame:
    """篩選出代表「總計」或「全國」的資料列，避免重複計算。"""
    if df.empty: return df
    
    total_kws = ["總計", "全國", "臺灣地區", "台灣地區", "中華民國", "taiwan", "all"]
    # 檢查每一欄，看是否包含這些關鍵字。
    for col in df.columns:
        # 只檢查 object/string 類型的欄位。
        if df[col].dtype == object:
            mask = df[col].astype(str).str.contains("|".join(total_kws), case=False, na=False)
            if mask.any():
                print(f"DEBUG: 偵測到總計欄位: {col}")
                return df[mask]
    
    # 如果找不到明顯的總計列，且有時間欄位，則嘗試對時間進行 GroupBy 並加總。
    return df

def process_population_charts(df: pd.DataFrame, info: dict) -> list[dict]:
    """針對人口資料產出圓餅圖與折線圖的 payload。"""
    payloads = []
    
    # A. 圓餅圖：最新一期結構。
    if all(info.get(k) for k in ["young", "working", "old"]):
        # 取最新時間。
        df_target = df.copy()
        if info["time"]:
            df_target = df_target.sort_values(by=info["time"], ascending=False)
        
        # 篩選全國/總計資料。
        df_sum = filter_total_data(df_target)
        if not df_sum.empty:
            row = df_sum.iloc[0]
            labels = ["幼年人口 (0-14)", "工作年齡人口 (15-64)", "老年人口 (65+)"]
            try:
                vals = [
                    float(str(row[info["young"]]).replace(",", "")),
                    float(str(row[info["working"]]).replace(",", "")),
                    float(str(row[info["old"]]).replace(",", ""))
                ]
                if sum(vals) > 0:
                    payloads.append({
                        "type": "chart",
                        "chart_type": "pie",
                        "title": f"人口年齡結構 ({row[info['time']] if info['time'] else '最新一期'})",
                        "labels": labels,
                        "values": vals
                    })
            except: pass

    # B. 折線圖：人口總數趨勢。
    if info["time"] and info["total"]:
        df_trend = df.copy()
        # 清理數據。
        df_trend[info["total"]] = pd.to_numeric(df_trend[info["total"]].astype(str).str.replace(",", ""), errors="coerce")
        df_trend = df_trend.dropna(subset=[info["time"], info["total"]])
        
        # 篩選總計資料。
        df_trend = filter_total_data(df_trend)
        
        # 依照時間排序。
        df_trend = df_trend.sort_values(by=info["time"])
        
        # 限制筆數。
        if len(df_trend) > 80: df_trend = df_trend.tail(80)
        
        if len(df_trend) >= 2:
            payloads.append({
                "type": "chart",
                "chart_type": "line",
                "title": "人口總數趨勢圖",
                "labels": [str(x) for x in df_trend[info["time"]]],
                "values": [float(x) for x in df_trend[info["total"]]]
            })
            
    return payloads

def summarize_generic_data(df: pd.DataFrame, info: dict) -> str:
    """產生通用的資料摘要，供 AI 參考。"""
    summary = [
        f"資料成功下載並讀取（{df.shape[0]} 列 x {df.shape[1]} 欄）。",
        f"欄位：{', '.join(df.columns.tolist()[:20])}"
    ]
    # 提供前幾列範例（移除敏感或過長資料）。
    summary.append("\n範例數據：")
    summary.append(df.head(3).to_string(index=False))
    return "\n".join(summary)
