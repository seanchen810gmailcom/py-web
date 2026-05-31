#######################模組#######################
# 下面每個 import 都是這支 Discord bot 會用到的工具，右邊註解寫它負責哪一塊。
import sys  # 匯入 sys：用來調整 Python 模組搜尋路徑。
from pathlib import Path  # 匯入 Path：用比較安全、清楚的方式處理資料夾與檔案路徑。
# 調整 sys.path 以便能導入上級目錄的 myfunction 模組
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio  # 匯入 asyncio：負責非同步等待，例如等 Discord、網頁、Ollama 回應時不讓整個 bot 卡死。
import discord  # 匯入 discord.py：負責連線 Discord、收訊息、發訊息、建立 slash 指令和 Modal。
import os  # 匯入 os：負責讀取環境變數，例如 .env 裡載入的 Discord token、密碼、允許使用者 ID。
from dotenv import load_dotenv  # 匯入 load_dotenv：把 .env 檔案讀進環境變數，讓 os.getenv 可以拿到設定。
import textwrap  # 匯入 textwrap：把太長的 AI 回覆切成多段，避免超過 Discord 單則訊息長度限制。
import json  # 匯入 json：把 Python dict 轉成 JSON，或把 Ollama HTTP API 回傳的 JSON 轉回 Python 資料。
import io  # 匯入 io：讓 PDF bytes 可以像檔案一樣交給 pdfplumber 讀取。
import zipfile  # 匯入 zipfile：讀取 docx、pptx、xlsx 這類本質是 zip 的 Office 檔案。
import xml.etree.ElementTree as ET  # 匯入 ElementTree：解析 Office 檔案內部 XML 文字內容。
import base64  # 匯入 base64：把圖片 bytes 編碼成 Ollama vision API 可以接收的文字格式。
import uuid  # 匯入 uuid：產生不重複的圖片檔名，避免不同圖片輸出時互相覆蓋。
from datetime import datetime  # 匯入 datetime：產生永久記憶建立時間與暫存檔時間戳。
from urllib import request as urlrequest  # 匯入 urllib.request 並命名為 urlrequest：負責發 HTTP 請求、搜尋網頁、讀網頁內容。
from urllib import parse as urlparse  # 匯入 urllib.parse 並命名為 urlparse：負責處理網址編碼、query string、DuckDuckGo 轉址還原。
from urllib.error import URLError, HTTPError  # 匯入 URLError/HTTPError：辨識網路請求失敗或 HTTP 錯誤時的例外類型。
from html.parser import HTMLParser  # 匯入 HTMLParser：解析 DuckDuckGo 搜尋結果 HTML，也把一般網頁 HTML 轉成純文字。
import time  # 匯入 time：用 time.monotonic 計算搜尋、讀網頁、Ollama 回覆總共花了幾秒。
import re  # 匯入 re：用正規表達式清掉 ANSI 控制碼、thinking process，以及抽取文字規則。
import signal  # 匯入 signal：攔截 Ctrl+C / SIGTERM，讓 bot 關閉前可以先送下線私訊。
import subprocess  # 匯入 subprocess：執行 macOS 指令，例如 pmset、powermetrics、istats，但每次都會設定 timeout。
import shutil  # 匯入 shutil：檢查 istats、osx-cpu-temp、smc 這類外部工具是否存在。
import shlex  # 匯入 shlex：把檔名或路徑安全包成 shell command 可以使用的字串。
import tempfile  # 匯入 tempfile：暫存使用者上傳的舊 Office 檔，交給 macOS textutil 嘗試轉文字。
import traceback  # 匯入 traceback：圖表 JSON 或繪圖流程失敗時印出完整錯誤堆疊。
import requests  # 匯入 requests：用來查詢天氣 API 和其他 HTTP 請求。
from myfunction.myfunction import WwatherAPI  # 匯入 WwatherAPI：天氣查詢工具類別。

from chart_utils import make_bar_chart, make_line_chart, make_pie_chart, make_temperature_line_chart, make_humidity_line_chart, make_table_image  # 匯入圖表工具：用 matplotlib 在記憶體產生 PNG BytesIO。
from chart_parser import parse_chart_text  # 匯入圖表文字解析工具：從使用者輸入用正規表達式抓出標籤與數值。
from format_utils import SUCCESS, ERROR, symbol_demo_text, WEATHER_TEMP, WEATHER_HUMIDITY, WEATHER_WIND, WEATHER_UMBRELLA, WEATHER_CLOUD, make_markdown_table, split_long_message, make_weather_embed as make_weather_summary_embed, weather_symbol_for_text  # 匯入格式工具：提供狀態符號、天氣符號、表格分段與天氣 Embed。
from weather_utils import get_current_weather_summary, get_weekly_weather_table, get_today_hourly_table, get_today_rain_table, group_today_weather_periods, extract_today_temperature_series, extract_today_humidity_series, get_weather_alert_messages  # 匯入天氣資料整理工具：把 OpenWeather current/forecast 轉成摘要、表格、圖表序列和主動警報。
import dataset_utils  # 匯入資料集工具：負責處理 data.gov.tw 資料集頁面與 CSV 下載。

#######################初始化#######################
def find_env_file():
    current_dir = Path(__file__).resolve().parent
    for folder in [current_dir, *current_dir.parents]:
        candidate = folder / ".env"
        if candidate.exists():
            return candidate
    return None

ENV_PATH = find_env_file()
if ENV_PATH:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    load_dotenv(override=True)

print(f"目前讀取的 .env：{ENV_PATH if ENV_PATH else '未找到 .env'}") # 讀取.env檔案Ｍ讓程式可以拿到DC_BOT_TOKEN這類資料


def load_env_list(name):  # 逐行註解：從指定環境變數讀取逗點分隔清單，統一給權限系統使用。
    raw_value = os.getenv(name, "")  # 逐行註解：只讀指定變數名稱，不把敏感值印到終端機。
    normalized_items: list[str] = []  # 逐行註解：準備保存整理後的清單。
    for item in (raw_value or "").split(","):  # 逐行註解：依逗點切開 .env 內容，逐一整理每個項目。
        normalized_item = normalize_user_key(item)  # 逐行註解：套用統一身分格式，避免大小寫或空白造成誤判。
        if normalized_item:  # 逐行註解：忽略空字串，避免 .env 尾端逗點產生空白權限。
            normalized_items.append(normalized_item)  # 逐行註解：把有效項目加入權限清單。
    return normalized_items  # 逐行註解：回傳已整理、可直接比對的清單。


def normalize_user_key(value):  # 逐行註解：把 email、Discord 名稱或 ID 統一成可比對的文字 key。
    if value is None:  # 逐行註解：空值不能參與權限比對。
        return ""  # 逐行註解：用空字串表示無效 key。
    return str(value).strip().lower()  # 逐行註解：統一去掉前後空白並轉小寫，避免大小寫誤判。


def split_env_list(value: str) -> list[str]:  # 逐行註解：保留非權限設定可用的逗點切分工具，例如天氣警報 ID 清單。
    return [item.strip() for item in (value or "").split(",") if item.strip()]  # 逐行註解：非權限清單保留原字串大小寫，只去除空白與空項目。


def unique_env_items(items: list[str]) -> list[str]:  # 逐行註解：保留原順序並移除重複項目，避免同一個人收到重複通知。
    unique_items: list[str] = []  # 逐行註解：建立最後要回傳的不重複清單。
    seen_items: set[str] = set()  # 逐行註解：建立已看過項目的集合，用來快速判斷是否重複。
    for item in items:  # 逐行註解：逐一檢查傳進來的每個項目。
        normalized_item = normalize_user_key(item)  # 逐行註解：去重時使用小寫 key，避免同名大小寫不同造成重複通知。
        if not normalized_item:  # 逐行註解：忽略空項目。
            continue  # 逐行註解：空項目不加入結果。
        if normalized_item in seen_items:  # 逐行註解：如果這個項目已經出現過，就不要再加入一次。
            continue  # 逐行註解：跳過這個重複項目，繼續檢查下一個項目。
        seen_items.add(normalized_item)  # 逐行註解：記錄已出現的標準化 key。
        unique_items.append(item)  # 逐行註解：保留第一次出現時的原始文字。
    return unique_items  # 逐行註解：回傳已去重且保留原順序的清單。


SUPER_USER_LIST = load_env_list("SUPER_USERS")  # 逐行註解：讀取超級使用者清單，所有敏感與管理功能都以這份為準。
ALLOWED_USER_LIST = load_env_list("ALLOWED_USERS")  # 逐行註解：讀取一般允許使用者清單，聊天與一般指令都以這份為準。
SUPER_USER_KEYS = set(SUPER_USER_LIST)  # 逐行註解：建立超級使用者集合，讓每次權限判斷能快速查找。
ALLOWED_USER_KEYS = set(ALLOWED_USER_LIST)  # 逐行註解：建立一般允許使用者集合，讓每次權限判斷能快速查找。
CONFIGURED_PERMISSION_EMAIL_ALIASES = {key.split("@", 1)[0]: key for key in (SUPER_USER_KEYS | ALLOWED_USER_KEYS) if "@" in key and key.split("@", 1)[0]}  # 逐行註解：把設定中的 email local-part 對應回完整 email，支援 Discord 名稱對應 email。
SENSITIVE_COMMAND_NAMES = {"agent", "state", "run", "quit", "restart", "shell", "shutdown", "reload", "eval", "exec", "debug", "admin", "web_search"}  # 逐行註解：集中列出所有只能 SUPER_USERS 使用的敏感指令名稱，包含 web_search 以觸發 Sean 審核流程。
WEATHER_ALERT_DM_USER_IDS_RAW = os.getenv("WEATHER_ALERT_DM_USER_IDS", "").strip()  # 逐行註解：天氣警報仍可另外設定 Discord 數字 ID；沒設定時會改通知允許使用者。
WEATHER_ALERT_DM_USER_IDS = unique_env_items(split_env_list(WEATHER_ALERT_DM_USER_IDS_RAW))  # 逐行註解：整理天氣警報專用 ID 清單，避免同一 ID 收到重複警報。
WEATHER_ALERT_CITY = os.getenv("WEATHER_ALERT_CITY", "Taipei").strip() or "Taipei"  # 逐行註解：設定要監控的城市，預設台北。
WEATHER_ALERT_CHECK_SECONDS = max(60, int(os.getenv("WEATHER_ALERT_CHECK_SECONDS", "300")))  # 逐行註解：設定天氣警報檢查間隔，預設 5 分鐘且最低 60 秒。
DISCORD_BOT_QUIT_PASSWORD = os.getenv("DISCORD_BOT_QUIT_PASSWORD", "").strip()  # 逐行註解：設定 DISCORD_BOT_QUIT_PASSWORD 這個變數，供後面的流程使用。
NO_PERMISSION_MESSAGE = "You're not allowed to use this bot."  # 逐行註解：統一設定未在 ALLOWED_USERS 或 SUPER_USERS 時的拒絕文字。
SENSITIVE_PERMISSION_MESSAGE = "Not super user, asking Sean"  # 逐行註解：統一設定非 SUPER_USERS 使用敏感功能時的拒絕文字，同時表示已通知 Sean 審核。
STOP_AI_MESSAGE = "⏹️ Stop Thinking"  # 逐行註解：統一設定 /stop 成功停止 AI 任務時要顯示的文字。
startup_dm_sent = False  # 逐行註解：設定 startup_dm_sent 這個變數，供後面的流程使用。
shutdown_dm_sent = False  # 逐行註解：設定 shutdown_dm_sent 這個變數，供後面的流程使用。
weather_alert_monitor_task: asyncio.Task | None = None  # 逐行註解：保存天氣警報背景監控 task，避免 Discord 重連時重複啟動。
weather_alert_last_sent: dict[str, float] = {}  # 逐行註解：保存每種天氣警報最近傳送時間，用來去重避免洗訊息。

# 預設文字聊天模型：用 qwen2.5-coder:1.5b 套繁中聊天 Modelfile。
DEFAULT_CHAT_MODEL = "qwen2.5-coder:1.5b_chat"  # 逐行註解：設定 DEFAULT_CHAT_MODEL 這個變數，供後面的流程使用。
AI_IDENTITY_NAME = "Smart_Sean"  # 逐行註解：設定 AI 自己的固定身份名稱，讓 Smart_Sean 在回答身份問題時思考這個角色，而不是直接回傳硬寫的文字。

# 天氣 API 初始化
def get_env_value(*names):
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""

def mask_key(value):
    if not value:
        return "未讀到"
    return "已讀到，但不顯示內容"  # 逐行註解：只回報狀態，不印出 API key 的任何片段。

weather_api_key = get_env_value(
    "API_KEY",
    "WEATHER_API_KEY",
    "OPENWEATHER_API_KEY",
    "OPENWEATHERMAP_API_KEY",
)

print(f"天氣 API Key 狀態：{mask_key(weather_api_key)}")  # 逐行註解：從環境變數取得天氣 API 金鑰。
weather_api = WwatherAPI(weather_api_key) if weather_api_key else None  # 逐行註解：如果有 API 金鑰就初始化天氣 API，沒有的話就設定為 None。
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"  # 逐行註解：OpenWeather 5 day / 3 hour forecast API，提供可用的分時預報資料。
OPENWEATHER_HOURLY_FORECAST_URLS = (  # 逐行註解：OpenWeather hourly forecast 可能依方案使用不同 host，所以依序嘗試。
    "https://api.openweathermap.org/data/2.5/forecast/hourly",  # 逐行註解：一般文件或部分方案可能使用的 hourly forecast endpoint。
    "https://pro.openweathermap.org/data/2.5/forecast/hourly",  # 逐行註解：OpenWeather Pro hourly forecast endpoint。
)  # 逐行註解：結束 hourly forecast endpoint 清單。

# DM 模式下，每個使用者可以選擇目前要用的模型
DM_MODELS = (  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
    DEFAULT_CHAT_MODEL,  # 逐行註解：這行是跨行資料或參數的一個項目。
    "qwen2.5:7b",  # 逐行註解：加入 qwen2.5:7b 文字模型，讓使用者可在模型選單中選擇。
    "gemma4_thinking",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "gemma4_Instant",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "gemma4_happy",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "gemma4_angry",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "gemma4_sad",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "x/flux2-klein:latest",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
)  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
THINKING_MODELS = {"gemma4_thinking"}  # 逐行註解：設定 THINKING_MODELS 這個變數，供後面的流程使用。
NO_THINKING_MODELS = {"gemma4_Instant", "gemma4_happy", "gemma4_angry", "gemma4_sad", "gemma4_agent_discord-bot"}  # 逐行註解：設定 NO_THINKING_MODELS 這個變數，供後面的流程使用。
dm_user_model: dict[int, str] = {}  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。

# /run 終端模式會話管理
terminal_sessions: dict[int, dict] = {}  # 逐行註解：追蹤活躍的終端會話，key 是使用者 ID，value 是會話資訊（訊息、頻道、輸出等）。
agent_sessions: dict[int, dict] = {}  # 逐行註解：追蹤活躍的 AI Agent 模式，key 是使用者 ID，value 是任務歷史、指令歷史和目前頻道。

# ===== Sean 審核系統用 =====
# key 格式：(user_id, command_name) -> {request_id, timestamp, interaction, command_name, user}
PENDING_SENSITIVE_APPROVALS: dict[tuple[int, str], dict] = {}  # 逐行註解：儲存等待 Sean 審核的請求，避免重複發送 DM。
ONE_TIME_SENSITIVE_GRANTS: dict[tuple[int, str], float] = {}  # 逐行註解：儲存 Sean 批准後的一次性授權，value 為過期時間戳記（5 分鐘），不寫入檔案。
SEAN_APPROVAL_EMAIL = "seanchen810@gmail.com"  # 逐行註解：唯一 SUPER_USER 的 email，用來查找 Sean 的 Discord 帳號並發送審核 DM。
SEAN_APPROVAL_GRANT_SECONDS = 300  # 逐行註解：授權有效期 5 分鐘，經過後即失效。
active_ai_runs: dict[int, dict] = {}  # 逐行註解：追蹤每位使用者目前正在思考的 AI 任務，讓 /stop 可以取消。
AGENT_MAX_RETRIES = 5  # 逐行註解：Agent 每個任務最多修正/重試 5 次，避免無限 loop。
AGENT_COMMAND_TIMEOUT_SECONDS = 90  # 逐行註解：Agent 執行 shell command 的 timeout，避免長時間指令卡死 Discord bot。
AGENT_MODEL = "gemma4_agent_discord-bot"  # 逐行註解：Agent 模式固定使用這個專用模型，不讀使用者目前在聊天模式選的模型。

# 對話記憶有三層：
# 1. Summary memory：整理後的長期記憶，會優先放進 prompt，讓小模型也容易理解。
# 2. 共享記憶：同一個使用者的 /web_search 結果會存在這裡，讓不同模型都看得到。
# 3. 模型記憶：同一個使用者在某個模型下的一般聊天會存在這裡，避免不同模型互相污染風格。
# /summary_memory 會強制用 gemma4_thinking 整理全部記憶，使用者確認後更新 summary；/clear 只清空聊天記錄。
# 這裡用字元數粗估 token；如果想調整總記憶量，可以在 .env 設 CONVERSATION_MEMORY_MAX_CHARS。
# 如果想調整單筆訊息保留多長，可以在 .env 設 CONVERSATION_MEMORY_ENTRY_MAX_CHARS。
SUMMARY_MEMORY_MODEL = "__summary_user_memory__"  # 逐行註解：整理後 summary memory 的特殊 key，不是真正的 Ollama 模型名稱。
SUMMARY_MEMORY_OLLAMA_MODEL = "gemma4_thinking"  # 逐行註解：summary memory 固定用 gemma4_thinking 產生，不能由使用者切換。
SHARED_MEMORY_MODEL = "__shared_user_memory__"  # 逐行註解：建立一個共享記憶用的特殊名稱，讓 web_search 結果可以被所有文字模型看到。
CONVERSATION_MEMORY_MAX_CHARS = int(os.getenv("CONVERSATION_MEMORY_MAX_CHARS", "12000"))  # 逐行註解：設定 CONVERSATION_MEMORY_MAX_CHARS 這個變數，供後面的流程使用。
CONVERSATION_MEMORY_ENTRY_MAX_CHARS = int(os.getenv("CONVERSATION_MEMORY_ENTRY_MAX_CHARS", "6000"))  # 逐行註解：設定單筆對話最多保存幾個字，避免 web_search 長回答被 1200 字切太短。
SUMMARY_MEMORY_SOURCE_MAX_CHARS = int(os.getenv("SUMMARY_MEMORY_SOURCE_MAX_CHARS", "30000"))  # 逐行註解：summary memory 整理時最多拿多少 raw memory 給 gemma4_thinking。
SUMMARY_MEMORY_ENTRY_MAX_CHARS = int(os.getenv("SUMMARY_MEMORY_ENTRY_MAX_CHARS", "9000"))  # 逐行註解：整理後的 summary memory 最多保存幾個字。
conversation_memory: dict[tuple[int, str], list[dict[str, str]]] = {}  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。

# 圖片只存到這個資料夾，送出後會刪掉（避免誤刪其他地方的檔案）
IMAGE_DIR = (Path.home() / "discord_bot_generated_images").resolve()  # 逐行註解：設定 IMAGE_DIR 這個變數，供後面的流程使用。
IMAGE_DIR.mkdir(parents=True, exist_ok=True)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
BOT_DIR = Path(__file__).resolve().parent  # 逐行註解：取得 AI.py 所在資料夾，讓新增資料都放在 Discord bot 專案內。
MEMORIES_DIR = (BOT_DIR / "memories").resolve()  # 逐行註解：設定永久記憶資料夾，每位 Discord 使用者會有自己的 JSON 檔。
MEMORIES_DIR.mkdir(parents=True, exist_ok=True)  # 逐行註解：啟動時自動建立 memories 資料夾，資料夾已存在時不會報錯。
DISCORD_TEXT_LIMIT = 1900  # 逐行註解：保守低於 Discord 單則 2000 字上限，所有新增文字回覆都用它分段。
DISCORD_EMBED_DESCRIPTION_LIMIT = 3600  # 逐行註解：保守低於 Embed description 4096 字上限，永久記憶分頁會用它切頁。
PDF_TEXT_MAX_CHARS = int(os.getenv("PDF_TEXT_MAX_CHARS", "18000"))  # 逐行註解：限制送進 Ollama 的 PDF 文字量，避免太長拖垮本機模型。
YOUTUBE_TRANSCRIPT_MAX_CHARS = int(os.getenv("YOUTUBE_TRANSCRIPT_MAX_CHARS", "18000"))  # 逐行註解：限制送進 Ollama 的 YouTube 字幕量，避免字幕過長。
PERMANENT_MEMORY_MAX_CHARS = int(os.getenv("PERMANENT_MEMORY_MAX_CHARS", "8000"))  # 逐行註解：限制永久記憶送進 Ollama 的總字數，避免記憶太多時 prompt 過長。
MEMORY_SUGGESTION_MAX_CHARS = int(os.getenv("MEMORY_SUGGESTION_MAX_CHARS", "1000"))  # 逐行註解：限制 AI 建議寫入永久記憶的單筆內容長度。
PDF_IMAGE_AREA_THRESHOLD = float(os.getenv("PDF_IMAGE_AREA_THRESHOLD", "0.05"))  # 逐行註解：PDF 頁面圖片面積超過 5% 時就視為需要 Gemma4 視覺分析。
PDF_VISION_MAX_PAGES = int(os.getenv("PDF_VISION_MAX_PAGES", "8"))  # 逐行註解：限制一次 PDF 視覺分析最多渲染幾頁，避免圖片頁太多拖垮 Ollama。
PDF_VISION_RENDER_DPI = int(os.getenv("PDF_VISION_RENDER_DPI", "150"))  # 逐行註解：設定 PDF 頁面轉圖片時的 DPI，兼顧清晰度與本機模型速度。
PDF_GEMMA4_VISION_MODEL = os.getenv("PDF_GEMMA4_VISION_MODEL", "gemma4_thinking").strip() or "gemma4_thinking"  # 逐行註解：非 Gemma4 模型遇到圖片 PDF 時，預設改用這個 Gemma4 視覺模型。
UPLOADED_FILE_TEXT_MAX_CHARS = int(os.getenv("UPLOADED_FILE_TEXT_MAX_CHARS", "18000"))  # 逐行註解：限制一般附件文字送進 Ollama 的最大字數，避免檔案太大卡住模型。
OFFICE_XML_TEXT_MAX_CHARS = int(os.getenv("OFFICE_XML_TEXT_MAX_CHARS", "18000"))  # 逐行註解：限制 Office 檔案解析出的文字量，避免大型簡報或試算表過長。
READABLE_TEXT_EXTENSIONS = {  # 逐行註解：定義可直接當文字或程式碼讀取的副檔名集合。
    ".txt",  # 逐行註解：純文字檔。
    ".md",  # 逐行註解：Markdown 文件。
    ".markdown",  # 逐行註解：Markdown 另一種常見副檔名。
    ".py",  # 逐行註解：Python 程式碼。
    ".js",  # 逐行註解：JavaScript 程式碼。
    ".jsx",  # 逐行註解：React JavaScript 程式碼。
    ".ts",  # 逐行註解：TypeScript 程式碼。
    ".tsx",  # 逐行註解：React TypeScript 程式碼。
    ".html",  # 逐行註解：HTML 文件。
    ".htm",  # 逐行註解：HTML 舊副檔名。
    ".css",  # 逐行註解：CSS 樣式檔。
    ".scss",  # 逐行註解：SCSS 樣式檔。
    ".json",  # 逐行註解：JSON 資料檔。
    ".csv",  # 逐行註解：CSV 表格檔。
    ".log",  # 逐行註解：log 紀錄檔。
    ".xml",  # 逐行註解：XML 文件。
    ".yaml",  # 逐行註解：YAML 設定檔。
    ".yml",  # 逐行註解：YAML 設定檔短副檔名。
    ".toml",  # 逐行註解：TOML 設定檔。
    ".ini",  # 逐行註解：INI 設定檔。
    ".env",  # 逐行註解：環境設定文字檔。
    ".java",  # 逐行註解：Java 程式碼。
    ".c",  # 逐行註解：C 程式碼。
    ".h",  # 逐行註解：C/C++ 標頭檔。
    ".cpp",  # 逐行註解：C++ 程式碼。
    ".hpp",  # 逐行註解：C++ 標頭檔。
    ".cs",  # 逐行註解：C# 程式碼。
    ".go",  # 逐行註解：Go 程式碼。
    ".rs",  # 逐行註解：Rust 程式碼。
    ".swift",  # 逐行註解：Swift 程式碼。
    ".kt",  # 逐行註解：Kotlin 程式碼。
    ".rb",  # 逐行註解：Ruby 程式碼。
    ".php",  # 逐行註解：PHP 程式碼。
    ".sql",  # 逐行註解：SQL 腳本。
    ".sh",  # 逐行註解：Shell 腳本。
    ".bash",  # 逐行註解：Bash 腳本。
    ".zsh",  # 逐行註解：Zsh 腳本。
    ".svg",  # 逐行註解：SVG 圖檔本質是 XML 文字，也可以直接閱讀。
    ".rtf",  # 逐行註解：RTF 文件可嘗試文字化。
}  # 逐行註解：結束可讀文字副檔名集合。
OFFICE_ATTACHMENT_EXTENSIONS = {".doc", ".docx", ".word", ".ppt", ".pptx", ".xls", ".xlsx", ".rtf", ".odt"}  # 逐行註解：定義常見 Word、PowerPoint、Excel 與文件格式副檔名。
IMAGE_ATTACHMENT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}  # 逐行註解：定義可交給 Gemma4 vision 分析的圖片副檔名。
VIDEO_ATTACHMENT_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}  # 逐行註解：定義目前無法直接分析的影片副檔名。

# event loop 可以想成「非同步任務的轉盤」：
# 哪個工作先做、哪個工作要等一下，會由這個轉盤幫忙安排。
# Python 3.10+ 在主程式裡不一定會先自動準備好這個轉盤，
# 所以我們自己先建立一個給Discord使用。
asyncio.set_event_loop(asyncio.new_event_loop())  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
# 建立一個新的 event loop，給Discord使用
# Intent 可以想成「先跟Discord勾選：我想收到哪些類型的通知」
# 如果沒有先打開某個 Intent，Discord就不會把那種資酪送給機器人。
intents = discord.Intents.default()  # 逐行註解：設定 intents 這個變數，供後面的流程使用。
intents.message_content = True # 允許機器人看到訊息真正的文字內容，這樣她才知道有人是不是輸入了Hello
intents.members = True  # 逐行註解：允許 bot 取得目前 guild members，才能用 username、display_name 或 email alias 解析通知收件人。

bot = discord.Client(intents=intents) # 建立機器人本體，並把 intents 交給它
tree = discord.app_commands.CommandTree(bot) # 建立一個「指令樹」，讓我們可以在裡面登記指令


def get_discord_user_keys(user) -> set[str]:  # 逐行註解：從 Discord user/member 物件整理所有可比對身分 key。
    if user is None:  # 逐行註解：沒有使用者物件時不能通過任何權限判斷。
        return set()  # 逐行註解：回傳空集合，讓呼叫端自然判斷失敗。
    raw_keys = [getattr(user, "name", ""), getattr(user, "display_name", ""), getattr(user, "global_name", ""), str(getattr(user, "id", "")), str(user)]  # 逐行註解：支援 username、display_name、global_name、Discord ID 與完整字串。
    user_keys: set[str] = set()  # 逐行註解：建立不重複的標準化身分 key 集合。
    for raw_key in raw_keys:  # 逐行註解：逐一整理 Discord 物件上的候選身分。
        normalized_key = normalize_user_key(raw_key)  # 逐行註解：套用統一大小寫與空白處理。
        if not normalized_key:  # 逐行註解：空 key 不參與比對。
            continue  # 逐行註解：略過空 key。
        user_keys.add(normalized_key)  # 逐行註解：加入原始標準化 key。
        if "#" in normalized_key:  # 逐行註解：相容舊版 name#0000 字串。
            discriminator_name = normalize_user_key(normalized_key.split("#", 1)[0])  # 逐行註解：拆出 # 前面的使用者名稱。
            if discriminator_name:  # 逐行註解：確保拆出的名稱不是空字串。
                user_keys.add(discriminator_name)  # 逐行註解：加入不含 discriminator 的名稱。
    for key in list(user_keys):  # 逐行註解：針對已知 key 補上 email 與 local-part 對應。
        email_alias = CONFIGURED_PERMISSION_EMAIL_ALIASES.get(key)  # 逐行註解：如果 Discord 名稱等於設定中 email 的 local-part，就補成完整 email。
        if email_alias:  # 逐行註解：找到 email 對應時才加入。
            user_keys.add(email_alias)  # 逐行註解：讓 seanchen810 可以命中 seanchen810@gmail.com。
        if "@" in key:  # 逐行註解：如果 Discord 端本來就是 email 字串，也補上 local-part。
            local_part = normalize_user_key(key.split("@", 1)[0])  # 逐行註解：拆出 email @ 前面的文字。
            if local_part:  # 逐行註解：避免加入空 local-part。
                user_keys.add(local_part)  # 逐行註解：讓 email 和 Discord 名稱可以互相對應。
    return user_keys  # 逐行註解：回傳完整可比對身分集合。


def is_super_user(user) -> bool:  # 逐行註解：判斷使用者是否屬於 SUPER_USERS。
    return bool(SUPER_USER_KEYS & get_discord_user_keys(user))  # 逐行註解：任一 Discord key 命中 SUPER_USERS 就是超級使用者。


def is_allowed_user(user) -> bool:  # 逐行註解：判斷使用者是否屬於可使用 bot 的使用者。
    if is_super_user(user):  # 逐行註解：SUPER_USERS 自動也是 ALLOWED_USERS。
        return True  # 逐行註解：超級使用者可以使用一般 bot 功能。
    return bool(ALLOWED_USER_KEYS & get_discord_user_keys(user))  # 逐行註解：一般使用者任一 key 命中 ALLOWED_USERS 即可使用。


def require_allowed_user(user) -> bool:  # 逐行註解：一般功能入口使用的權限檢查包裝。
    return is_allowed_user(user)  # 逐行註解：符合 ALLOWED_USERS 或 SUPER_USERS 時回傳 True。


def require_super_user(user) -> bool:  # 逐行註解：敏感與管理功能入口使用的權限檢查包裝。
    return is_super_user(user)  # 逐行註解：只有 SUPER_USERS 會回傳 True。


def is_dm_context(guild) -> bool:  # 逐行註解：集中判斷目前事件是否來自 Discord 私訊 DM。
    return guild is None  # 逐行註解：discord.py 在私訊中沒有 guild，伺服器頻道才會有 guild。


def is_allowed_message_user(message: discord.Message) -> bool:  # 逐行註解：集中判斷一般訊息作者是否可使用 bot。
    return require_allowed_user(message.author)  # 逐行註解：一般訊息不再分 DM/伺服器名單，統一走 ALLOWED_USERS 與 SUPER_USERS。


def is_allowed_interaction_user(interaction: discord.Interaction) -> bool:  # 逐行註解：集中判斷 slash command 使用者是否可使用一般 bot 功能。
    return require_allowed_user(interaction.user)  # 逐行註解：slash command 不再分 DM/伺服器名單，統一走 ALLOWED_USERS 與 SUPER_USERS。


def sensitive_permission_message() -> str:  # 逐行註解：集中管理敏感功能沒有權限時的回覆文字。
    return SENSITIVE_PERMISSION_MESSAGE  # 逐行註解：回傳需求指定的敏感功能拒絕訊息。


def interaction_command_name(interaction: discord.Interaction) -> str:  # 逐行註解：從 slash interaction 取出指令名稱，供全域權限閘門判斷敏感指令。
    command = getattr(interaction, "command", None)  # 逐行註解：優先使用 discord.py 解析後的 command 物件。
    command_name = normalize_user_key(getattr(command, "name", ""))  # 逐行註解：整理 command 物件上的名稱。
    if command_name:  # 逐行註解：如果拿得到名稱就直接使用。
        return command_name  # 逐行註解：回傳標準化指令名稱。
    data = getattr(interaction, "data", {}) or {}  # 逐行註解：command 物件不可用時改讀原始 interaction data。
    if isinstance(data, dict):  # 逐行註解：確認 data 是字典才讀取 name 欄位。
        return normalize_user_key(data.get("name", ""))  # 逐行註解：回傳原始 data 裡的標準化指令名稱。
    return ""  # 逐行註解：無法判斷指令名稱時回傳空字串。


async def send_interaction_permission_denied(interaction: discord.Interaction, message: str) -> None:  # 逐行註解：統一處理 slash command 權限拒絕回覆。
    if not interaction.response.is_done():  # 逐行註解：如果 interaction 還沒回覆，就用第一則 response。
        await interaction.response.send_message(message, ephemeral=True)  # 逐行註解：拒絕訊息只回覆給執行者。
        return  # 逐行註解：第一則回覆已送出，結束函式。
    await interaction.followup.send(message, ephemeral=True)  # 逐行註解：如果已回覆過，就改用 followup 傳同一套拒絕訊息。


async def permission_interaction_check(interaction: discord.Interaction) -> bool:  # 逐行註解：CommandTree 全域權限檢查，所有 slash command 都先經過這裡。
    command_name = interaction_command_name(interaction)  # 逐行註解：取得目前指令名稱，判斷是否屬於敏感功能。
    if command_name in SENSITIVE_COMMAND_NAMES:  # 逐行註解：敏感指令必須是 SUPER_USERS。
        if require_super_user(interaction.user):  # 逐行註解：超級使用者可以繼續執行敏感指令。
            return True  # 逐行註解：回傳 True 讓 command body 執行。
        if command_name == "web_search":  # 逐行註解：只有 web_search 可以走 Sean Approval 流程。
            if has_one_time_sensitive_grant(interaction.user.id, command_name):  # 逐行註解：檢查是否有 Sean 批准的一次性授權。
                consume_one_time_sensitive_grant(interaction.user.id, command_name)  # 逐行註解：消耗授權，只能用一次。
                return True  # 逐行註解：授權有效，讓 command body 執行。
            asyncio.create_task(request_sensitive_approval(interaction, command_name))  # 逐行註解：异步觸發 Sean 審核，不阻塌其他事件。
            return False  # 逐行註解：阻止 command body 執行。
        await send_interaction_permission_denied(interaction, "Not super user")  # 逐行註解：非 SUPER_USER 使用其他敏感功能，直接拒絕。
        return False  # 逐行註解：阻止 command body 執行。
    if require_allowed_user(interaction.user):  # 逐行註解：一般指令允許 ALLOWED_USERS 與 SUPER_USERS 使用。
        return True  # 逐行註解：權限通過，讓 command body 執行。
    await send_interaction_permission_denied(interaction, NO_PERMISSION_MESSAGE)  # 逐行註解：不在兩層權限名單的人不能使用 bot。
    return False  # 逐行註解：阻止 command body 執行.


tree.interaction_check = permission_interaction_check  # 逐行註解：把統一權限閘門掛到所有 slash command 前面。


# ===== Sean 審核系統 Helpers =====

async def _find_sean_user() -> discord.User | None:
    """用 SEAN_APPROVAL_EMAIL 從 SUPER_USER_LIST 找 Sean 的 Discord 帳號。"""
    # 先看看 SUPER_USER_LIST 裡有沒有數字 ID，有就直接 fetch_user
    for key in SUPER_USER_LIST:  # 逐行註解：逐一檢查 SUPER_USER_LIST 裡的每一個 key。
        if key.isdigit():  # 逐行註解：數字 key 就是 Discord user ID。
            try:  # 逐行註解：嘗試用 Discord API 取得使用者物件。
                user = bot.get_user(int(key)) or await bot.fetch_user(int(key))  # 逐行註解：先讀本地快取，沒有才 fetch。
                if user:  # 逐行註解：找到使用者就回傳。
                    return user  # 逐行註解：回傳 Sean 的 Discord 使用者物件。
            except Exception:  # 逐行註解：預防 fetch 失敗時崩潰。
                pass  # 逐行註解：找不到就繼續找下一個 key。
    # 如果沒有數字 ID，就嘗試從 guild members 比對 email
    for guild in bot.guilds:  # 逐行註解：逐一檢查 bot 所在的所有伺服器。
        for member in guild.members:  # 逐行註解：逐一檢查伺服器成員。
            if SEAN_APPROVAL_EMAIL in get_discord_user_keys(member):  # 逐行註解：檢查 email 是否屬於這个成員。
                return member  # 逐行註解：找到 Sean 就回傳。
    return None  # 逐行註解：完全找不到就回傳 None。


def has_one_time_sensitive_grant(user_id: int, command_name: str) -> bool:
    """檢查使用者對指定指令是否有未過期的一次性授權。"""
    key = (user_id, command_name)  # 逐行註解：用 (user_id, command_name) 組成查詢 key。
    if key not in ONE_TIME_SENSITIVE_GRANTS:  # 逐行註解：如果根本沒有授權就回傳 False。
        return False  # 逐行註解：沒有授權。
    if time.monotonic() > ONE_TIME_SENSITIVE_GRANTS[key]:  # 逐行註解：檢查授權是否已過期。
        print(f"DEBUG: one-time grant expired user_id={user_id} command={command_name}")  # 逐行註解：後台 log 授權過期。
        del ONE_TIME_SENSITIVE_GRANTS[key]  # 逐行註解：清除過期授權避免占空間。
        return False  # 逐行註解：授權已過期。
    return True  # 逐行註解：授權有效。


def consume_one_time_sensitive_grant(user_id: int, command_name: str) -> bool:
    """消耗一次性授權，成功就刪除并回傳 True。"""
    key = (user_id, command_name)  # 逐行註解：組成 key。
    if not has_one_time_sensitive_grant(user_id, command_name):  # 逐行註解：沒授權或已過期就不能消耗。
        return False  # 逐行註解：回傳失敗。
    print(f"DEBUG: one-time grant consumed user_id={user_id} command={command_name}")  # 逐行註解：後台 log 授權被使用。
    del ONE_TIME_SENSITIVE_GRANTS[key]  # 逐行註解：立刻刪除授權，确保只能用一次。
    return True  # 逐行註解：成功消耗授權。


class SensitiveApprovalPasswordModal(discord.ui.Modal, title="Approve sensitive request"):
    """輸入審核密碼用的 Modal。"""
    password = discord.ui.TextInput(  # 逐行註解：密碼欄位。
        label="請輸入敏感功能密碼",  # 逐行註解：讓 Sean 知道要輸入哪一層密碼。
        placeholder="DISCORD_BOT_QUIT_PASSWORD",  # 逐行註解：提示使用現有密碼環境變數。
        required=True,  # 逐行註解：密碼必填。
        max_length=200,  # 逐行註解：限制密碼長度。
    )  # 逐行註解：結束 TextInput。

    def __init__(self, pending_key: tuple, request_id: str, requester: discord.User | discord.Member, approval_msg: discord.Message):
        super().__init__()  # 逐行註解：呼叫父類建構式。
        self.pending_key = pending_key  # 逐行註解：保存 (user_id, command_name) key，審核後用來查找 pending 審核記錄。
        self.request_id = request_id  # 逐行註解：保存此次審核的唯一 ID。
        self.requester = requester  # 逐行註解：保存請求使用者物件，稍後用來通知。
        self.approval_msg = approval_msg  # 逐行註解：保存 Sean DM 裡的審核訊息物件，審核後用來更新内容。

    async def on_submit(self, interaction: discord.Interaction):  # 逐行註解：處理 Sean 送出密碼表單。
        if not require_super_user(interaction.user):  # 逐行註解：審核密碼對話框只限 SUPER_USER 操作。
            await interaction.response.send_message(SENSITIVE_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：非超級使用者不能操作。
            return  # 逐行註解：停止流程。
        entered_password = self.password.value.strip()  # 逐行註解：取得 Sean 輸入的密碼，不印到 log。
        if not DISCORD_BOT_QUIT_PASSWORD or entered_password != DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：比對現有敏感密碼環境變數，不印密碼。
            # 密碼錯誤：清除 pending，通知原使用者和 Sean
            PENDING_SENSITIVE_APPROVALS.pop(self.pending_key, None)  # 逐行註解：審核失敗就清除 pending 記錄。
            await interaction.response.send_message("密碼錯誤。Request denied.", ephemeral=True)  # 逐行註解：向 Sean 顮認密碼錯誤。
            print(f"DEBUG: sensitive approval denied request_id={self.request_id}")  # 逐行註解：後台 log。
            try:  # 逐行註解：嘗試更新 Sean DM 裡的審核訊息。
                await self.approval_msg.edit(content="Password wrong. Request denied.", view=None)  # 逐行註解：更新 Sean DM 訊息內容。
            except Exception:  # 逐行註解：編輯失敗不崩潰。
                pass  # 逐行註解：忽略編輯失敗。
            try:  # 逐行註解：嘗試從 pending 記錄找到原使用者 channel 并通知。
                pending = PENDING_SENSITIVE_APPROVALS.get(self.pending_key)  # 逐行註解：安全取得 pending 記錄。
                channel = pending["channel"] if pending else None  # 逐行註解：決定要回魏哪個頻道。
                if channel:  # 逐行註解：有頻道才發送通知。
                    await channel.send(f"<@{self.requester.id}> Sean approval password was wrong. Request denied.")  # 逐行註解：通知原使用者密碼錯誤。
            except Exception:  # 逐行註解：通知失敗不崩潰。
                pass  # 逐行註解：忽略通知失敗。
            return  # 逐行註解：結束函式。
        # 密碼正確：建立一次性授權
        cmd_name = self.pending_key[1]  # 逐行註解：取得指令名稱。
        ONE_TIME_SENSITIVE_GRANTS[self.pending_key] = time.monotonic() + SEAN_APPROVAL_GRANT_SECONDS  # 逐行註解：建立五分鐘授權時間。
        PENDING_SENSITIVE_APPROVALS.pop(self.pending_key, None)  # 逐行註解：清除 pending。
        print(f"DEBUG: sensitive approval approved request_id={self.request_id}")  # 逐行註解：後台 log。
        await interaction.response.send_message(f"已允許這次請求。使用者可在 5 分鐘內重新執行一次。", ephemeral=True)  # 逐行註解： Sean 看到成功訊息。
        try:  # 逐行註解：嘗試更新 Sean DM 裡的審核訊息。
            await self.approval_msg.edit(content=f"已允許這次請求。使用者可在 5 分鐘內重新執行一次。", view=None)  # 逐行註解：更新審核訊息。
        except Exception:  # 逐行註解：編輯失敗不崩潰。
            pass  # 逐行註解：忽略失敗。
        try:  # 逐行註解：嘗試從 pending 記錄或直接用 requester 找到頻道并通知。
            pending = PENDING_SENSITIVE_APPROVALS.get(self.pending_key)  # 逐行註解：安全取得 pending，清除前可能已沒有。
            channel = pending["channel"] if pending else None  # 逐行註解：找到原使用者頻道。
            if channel:  # 逐行註解：有頻道才發送。
                await channel.send(f"<@{self.requester.id}> Sean approved this request. Please run the command again within 5 minutes.")  # 逐行註解：通知原使用者可以重新執行。
            else:  # 逐行註解：找不到頻道時嘗試發送 DM。
                await self.requester.send(f"Sean approved your `/{cmd_name}` request. Please run the command again within 5 minutes.")  # 逐行註解：直接 DM 通知原使用者。
        except Exception:  # 逐行註解：通知失敗不崩潰。
            pass  # 逐行註解：忽略通知失敗。


class SensitiveApprovalView(discord.ui.View):
    """發給 Sean 的審核按鈕：允許 / 不允許。"""

    def __init__(self, pending_key: tuple, request_id: str, requester: discord.User | discord.Member, channel):
        super().__init__(timeout=600)  # 逐行註解：10 分鐘超時，避免審核 View 永遠占著。
        self.pending_key = pending_key  # 逐行註解：保存 (user_id, command_name) key。
        self.request_id = request_id  # 逐行註解：保存審核唯一 ID。
        self.requester = requester  # 逐行註解：保存請求使用者物件。
        self.channel = channel  # 逐行註解：保存請求來源頻道，拒絕時用來通知。
        self.approval_msg: discord.Message | None = None  # 逐行註解：稍後由 request_sensitive_approval 設定，讓 Modal 可以更新訊息。

    async def interaction_check(self, interaction: discord.Interaction) -> bool:  # 逐行註解：限制只有 SUPER_USER 可以按。
        if require_super_user(interaction.user):  # 逐行註解：檢查按鈕的使用者是否為 SUPER_USER。
            return True  # 逐行註解： SUPER_USER 可以按。
        await interaction.response.send_message(SENSITIVE_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：非 SUPER_USER 按審核按鈕會看到該訊息。
        return False  # 逐行註解：阻止非 SUPER_USER 操作按鈕。

    @discord.ui.button(label="允許", style=discord.ButtonStyle.success)  # 逐行註解：綠色允許按鈕。
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):  # 逐行註解：處理 Sean 按「允許」。
        modal = SensitiveApprovalPasswordModal(  # 逐行註解：跟出密碼 Modal。
            pending_key=self.pending_key,  # 逐行註解：傳入 pending key。
            request_id=self.request_id,  # 逐行註解：傳入審核 ID。
            requester=self.requester,  # 逐行註解：傳入請求使用者。
            approval_msg=self.approval_msg,  # 逐行註解：傳入審核訊息物件，密碼正確後 Modal 會更新它。
        )  # 逐行註解：結束 Modal 建構。
        await interaction.response.send_modal(modal)  # 逐行註解：發送密碼 Modal。

    @discord.ui.button(label="不允許", style=discord.ButtonStyle.danger)  # 逐行註解：紅色不允許按鈕。
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):  # 逐行註解：處理 Sean 按「不允許」。
        PENDING_SENSITIVE_APPROVALS.pop(self.pending_key, None)  # 逐行註解：清除 pending 記錄。
        print(f"DEBUG: sensitive approval denied request_id={self.request_id}")  # 逐行註解：後台 log。
        await interaction.response.edit_message(content="已拒絕這次請求。", view=None)  # 逐行註解： Sean DM 訊息更新為已拒絕。
        try:  # 逐行註解：嘗試通知原使用者被拒絕。
            if self.channel:  # 逐行註解：有原頻道就在那裡發送。
                await self.channel.send(f"<@{self.requester.id}> Sean declined this request.")  # 逐行註解：通知原使用者被拒絕。
            else:  # 逐行註解：沒有頻道就 DM。
                await self.requester.send("Sean declined this request.")  # 逐行註解：直接 DM 請求使用者。
        except Exception:  # 逐行註解：通知失敗不崩潰。
            pass  # 逐行註解：忽略。


async def request_sensitive_approval(interaction: discord.Interaction, command_name: str) -> None:
    """非 SUPER_USER 使用敏感功能時，發送 DM 請 Sean 審核。"""
    user = interaction.user  # 逐行註解：取得請求使用者。
    user_id = user.id  # 逐行註解：取得使用者 ID。
    pending_key = (user_id, command_name)  # 逐行註解：組成審核 dict key。
    print(f"DEBUG: sensitive approval requested user_id={user_id} command={command_name}")  # 逐行註解：後台 log。
    # --- 避免重複發送 ---
    if pending_key in PENDING_SENSITIVE_APPROVALS:  # 逐行註解：如果同一 user + command 已經有審核中，不重複發 DM。
        await send_interaction_permission_denied(  # 逐行註解：回覆請求者易已有審核中。
            interaction,
            SENSITIVE_PERMISSION_MESSAGE + "\nApproval request already pending."
        )  # 逐行註解：結束回覆。
        return  # 逐行註解：結束函式。
    # --- 找 Sean 的 Discord 帳號 ---
    sean_user = await _find_sean_user()  # 逐行註解：查找 Sean 的 Discord 使用者物件。
    if not sean_user:  # 逐行註解：找不到 Sean 就 log 并回覆。
        print(f"DEBUG: cannot notify Sean for sensitive approval")  # 逐行註解：後台 log。
        await send_interaction_permission_denied(interaction, SENSITIVE_PERMISSION_MESSAGE)  # 逐行註解：件回覆請求者。
        return  # 逐行註解：找不到 Sean 就結束。
    # --- 對請求者回覆拒絕訊息 ---
    await send_interaction_permission_denied(interaction, SENSITIVE_PERMISSION_MESSAGE)  # 逐行註解：先回覆請求者。
    # --- 組對 DM 內容 ---
    request_id = str(uuid.uuid4())[:8]  # 逐行註解：產生簡短唯一 ID。
    guild_name = interaction.guild.name if interaction.guild else "DM"  # 逐行註解：取得來源伺服器名稱。
    channel_name = getattr(interaction.channel, "name", "DM")  # 逐行註解：取得頻道名稱。
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 逐行註解：目前時間。
    # 審核訊息內容
    dm_content = (
        f"有人要求使用 SUPER_USER 功能\n\n"
        f"使用者名稱：{user.display_name}\n"
        f"使用者帳號：{user.name}\n"
        f"使用者 ID：{user_id}\n\n"
        f"要求功能：/{command_name}\n"
        f"要求時間：{now_str}\n"
        f"要求來源：{guild_name}\n"
        f"頻道：{channel_name}\n\n"
        f"請選擇是否允許這一次操作。"
    )  # 逐行註解：組對審核 DM 內容。
    # --- 建立審核 View ---
    source_channel = interaction.channel  # 逐行註解：保存來源頻道，審核後用來通知。
    view = SensitiveApprovalView(  # 逐行註解：建立審核 View。
        pending_key=pending_key,  # 逐行註解：傳入 key。
        request_id=request_id,  # 逐行註解：傳入審核 ID。
        requester=user,  # 逐行註解：傳入請求使用者。
        channel=source_channel,  # 逐行註解：傳入來源頻道。
    )  # 逐行註解：結束 View 建構。
    # --- 發送 Sean DM ---
    try:  # 逐行註解：嘗試發送 DM。
        approval_msg = await sean_user.send(dm_content, view=view)  # 逐行註解：發送審核訊息給 Sean。
        view.approval_msg = approval_msg  # 逐行註解：需要把 approval_msg 回寫進 view，讓 Modal 可以更新它。
        # --- 存入 pending ---
        PENDING_SENSITIVE_APPROVALS[pending_key] = {  # 逐行註解：存入 pending dict。
            "request_id": request_id,  # 逐行註解：保存唯一 ID。
            "timestamp": time.monotonic(),  # 逐行註解：審核發出時間。
            "channel": source_channel,  # 逐行註解：來源頻道。
            "user": user,  # 逐行註解：請求使用者。
        }  # 逐行註解：結束 pending dict。
        print(f"DEBUG: sensitive approval sent to Sean request_id={request_id}")  # 逐行註解：後台 log。
    except Exception as e:  # 逐行註解：發送 DM 失敗不崩潰。
        print(f"DEBUG: cannot notify Sean for sensitive approval (send failed): {e}")  # 逐行註解：後台 log。


def should_reply_no_permission_to_message(message: discord.Message) -> bool:  # 逐行註解：定義函式 should_reply_no_permission_to_message，決定一般訊息沒權限時要不要回覆。
    """DM 一定回覆；伺服器只在使用者提到 bot 時回覆，避免一般聊天被洗版。"""  # 逐行註解：說明這個函式的白名單拒絕回覆策略。
    if message.guild is None:  # 逐行註解：判斷這則訊息是不是私訊，私訊代表使用者正在直接找 bot。
        return True  # 逐行註解：私訊不是白名單時要明確回覆沒有權限。
    return bot.user is not None and bot.user in (message.mentions or [])  # 逐行註解：伺服器裡只有提到 bot 時才回覆沒有權限。


def ollama_cli_thinking_flags(model: str) -> list[str]:  # 逐行註解：定義函式 ollama_cli_thinking_flags，把一段會重複使用的流程包起來。
    """依模型名稱決定 `ollama run` 要不要開 thinking。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if model in THINKING_MODELS:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return ["--think=true"]  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    if model in NO_THINKING_MODELS:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return ["--think=false", "--hidethinking"]  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    return []  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def ollama_api_think_value(model: str) -> bool | None:  # 逐行註解：定義函式 ollama_api_think_value，把一段會重複使用的流程包起來。
    """依模型名稱決定 Ollama HTTP API 的 think 值。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if model in THINKING_MODELS:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return True  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    if model in NO_THINKING_MODELS:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return False  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    return None  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

# Ollama 有時會把終端機控制碼或 thinking process 一起吐出來。
# 這三個 regex 是「輸出清理器」：使用者端與後台都會先經過它們過濾。
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")  # 逐行註解：設定 ANSI_ESCAPE_RE 這個變數，供後面的流程使用。
THINK_TAG_RE = re.compile(r"(?is)<think>.*?</think>")  # 逐行註解：設定 THINK_TAG_RE 這個變數，供後面的流程使用。
THINKING_PROCESS_RE = re.compile(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
    r"(?is)^\s*(?:thinking\.\.\.\s*)?(?:thinking process|thought process)\s*:.*?(?:\.\.\.done thinking\.|done thinking\.)\s*"  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
)  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
THINKING_INTRO_RE = re.compile(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
    r"(?is)^\s*thinking\.\.\..*?(?:\.\.\.done thinking\.|done thinking\.)\s*"  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
)  # 逐行註解：結束上一個跨行函式呼叫或資料結構。

def strip_thinking_process(text: str) -> str:  # 逐行註解：定義函式 strip_thinking_process，把一段會重複使用的流程包起來。
    """
    避免把 Ollama 的 thinking process（長長英文/推理過程）顯示在使用者/後台。
    常見格式是 <think>...</think>，這裡直接移除。
    """
    _, final_reply = split_thinking_process(text)  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    return final_reply  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def split_thinking_process(text: str) -> tuple[str, str]:  # 逐行註解：定義函式 split_thinking_process，把一段會重複使用的流程包起來。
    """
    把 Ollama 回覆拆成「thinking process」和「正式回答」。
    使用者端會先暫時顯示 thinking，再自動編輯成正式回答。
    """
    t = (text or "").strip()  # 逐行註解：設定 t 這個變數，供後面的流程使用。
    if not t:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return "", ""  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    t = ANSI_ESCAPE_RE.sub("", t)  # 逐行註解：設定 t 這個變數，供後面的流程使用。
    thinking_parts: list[str] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。

    for pattern in (THINK_TAG_RE, THINKING_PROCESS_RE, THINKING_INTRO_RE):  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        while True:  # 逐行註解：只要條件還成立，就持續重複執行下面的程式。
            match = pattern.search(t)  # 逐行註解：設定 match 這個變數，供後面的流程使用。
            if match is None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                break  # 逐行註解：提前跳出目前這個迴圈。
            thinking_parts.append(match.group(0).strip())  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            t = (t[:match.start()] + t[match.end():]).strip()  # 逐行註解：設定 t 這個變數，供後面的流程使用。

    return "\n\n".join(thinking_parts).strip(), t.strip()  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


THINKING_FRAMES = [  # 逐行註解：設定 Thinking 動畫每一格要顯示的方塊圖案。
    "■■□□□□",  # 逐行註解：第一格動畫，亮前兩個方塊。
    "□■■□□□",  # 逐行註解：第二格動畫，亮第二、第三個方塊。
    "□□■■□□",  # 逐行註解：第三格動畫，亮第三、第四個方塊。
    "□□□■■□",  # 逐行註解：第四格動畫，亮第四、第五個方塊。
    "□□□□■■",  # 逐行註解：第五格動畫，亮最後兩個方塊。
    "□□□■■□",  # 逐行註解：第六格動畫，往回亮第四、第五個方塊。
    "□□■■□□",  # 逐行註解：第七格動畫，往回亮第三、第四個方塊。
    "□■■□□□",  # 逐行註解：第八格動畫，往回亮第二、第三個方塊。
]  # 逐行註解：結束 Thinking 動畫清單。
THINKING_EDIT_DELAY = 0.55  # 逐行註解：設定 Thinking 動畫每 0.55 秒更新一次 Discord 訊息。
STREAM_EDIT_DELAY = 1.8  # 逐行註解：設定正式回答每 1.8 秒更新一次，避免每個 token 都 edit。
THINKING_PROCESS_DISPLAY_SECONDS = 3.0  # 逐行註解：設定 thinking process code box 顯示 3 秒後被正式回答覆蓋。


def display_model_name(model_name: str) -> str:  # 逐行註解：定義函式 display_model_name，把模型原始名稱轉成 Discord 上顯示的名稱。
    """把實際模型名稱整理成比較適合顯示在 Thinking 訊息上的文字。"""  # 逐行註解：說明這個函式只負責顯示文字，不改真正呼叫的模型。
    cleaned = (model_name or "model").strip()  # 逐行註解：先把空白清掉，如果沒有模型名就用 model 當備用。
    if cleaned == "gemma4_thinking":  # 逐行註解：如果實際模型是 gemma4_thinking，就用比較短的 Gemma4 顯示名稱。
        return "Gemma4"  # 逐行註解：回傳使用者要求範例中的 Gemma4 顯示格式。
    if cleaned.endswith("_chat"):  # 逐行註解：如果模型名稱尾巴是 _chat，就把這個內部標記拿掉。
        cleaned = cleaned[:-5]  # 逐行註解：移除最後五個字元，也就是 _chat。
    return cleaned  # 逐行註解：回傳整理後的模型顯示名稱。


def thinking_animation_text(model_name: str, frame: str) -> str:  # 逐行註解：定義函式 thinking_animation_text，組出 Discord Thinking 動畫文字。
    """依目前實際使用模型組出 `🤖 {model} Thinking frame`。"""  # 逐行註解：說明這裡會自動使用目前模型名，不寫死單一模型。
    return f"🤖 {display_model_name(model_name)} Thinking {frame}"  # 逐行註解：回傳使用者指定格式的 Thinking 顯示文字。


def format_thinking_process_code_box(thinking_text: str) -> str:  # 逐行註解：定義函式 format_thinking_process_code_box，把模型 thinking process 包成 Discord code box。
    """把 thinking process 包成 code box，並限制長度避免超過 Discord 單則訊息上限。"""  # 逐行註解：這個文字會短暫顯示 3 秒，之後由正式回答覆蓋。
    cleaned = (thinking_text or "").strip().replace("```", "'''")  # 逐行註解：清理空白並避免模型輸出的反引號破壞 code box。
    if len(cleaned) > 1700:  # 逐行註解：如果 thinking process 太長，就截斷，避免 Discord edit 失敗。
        cleaned = cleaned[:1700].rstrip() + "\n（thinking process 太長，只暫時顯示前面）"  # 逐行註解：保留前段並標記已截斷。
    return f"thinking process：\n```text\n{cleaned}\n```"  # 逐行註解：回傳使用者要求的 code box 顯示格式。


def discord_retry_after(exc: Exception) -> float | None:  # 逐行註解：定義函式 discord_retry_after，從 Discord rate limit 錯誤裡取出要等幾秒。
    """從 discord.py 例外或錯誤文字中找 retry_after 秒數。"""  # 逐行註解：說明這是為了遇到 HTTP 429 時尊重 Discord 要求的等待時間。
    retry_after = getattr(exc, "retry_after", None)  # 逐行註解：discord.py 的 rate limit 錯誤有時會直接帶 retry_after 屬性。
    if retry_after is not None:  # 逐行註解：如果有拿到 retry_after，就直接使用它。
        return float(retry_after)  # 逐行註解：把等待秒數轉成 float 後回傳。
    match = re.search(r"retry_after['\"]?\s*:\s*([0-9.]+)", str(exc))  # 逐行註解：如果屬性沒有，就從錯誤文字裡用 regex 找 retry_after。
    if match:  # 逐行註解：如果錯誤文字裡有找到秒數，就走這個分支。
        return float(match.group(1))  # 逐行註解：回傳 regex 找到的秒數。
    return None  # 逐行註解：找不到 retry_after 時回傳 None。


async def safe_edit_message(message: discord.Message, content: str, *, max_retries: int = 2) -> bool:  # 逐行註解：定義安全 edit 函式，集中處理 Discord edit 失敗與 429。
    """安全編輯 Discord 訊息；遇到 429 會等 retry_after，但不無限重試。"""  # 逐行註解：說明這裡不會用 except pass 硬吃錯誤。
    shown = (content or " ")[:1900]  # 逐行註解：Discord 單則訊息接近 2000 字上限，這裡保守截到 1900 字。
    for attempt in range(max_retries + 1):  # 逐行註解：最多嘗試第一次加上 max_retries 次重試。
        try:  # 逐行註解：開始嘗試 edit Discord 訊息。
            await message.edit(content=shown)  # 逐行註解：真正更新同一則 Discord 訊息內容。
            return True  # 逐行註解：edit 成功就回傳 True。
        except discord.HTTPException as exc:  # 逐行註解：捕捉 Discord HTTP 錯誤，例如 rate limit。
            if getattr(exc, "status", None) == 429 and attempt < max_retries:  # 逐行註解：只有 HTTP 429 且還有重試次數時才等待後重試。
                await asyncio.sleep(discord_retry_after(exc) or 1.0)  # 逐行註解：尊重 retry_after，沒有秒數時至少等 1 秒。
                continue  # 逐行註解：等待完回到下一輪重試。
            print(f"Discord 訊息 edit 失敗：{type(exc).__name__}: {exc}")  # 逐行註解：非可重試錯誤要印到後台，方便排查。
            return False  # 逐行註解：edit 失敗且不能再重試時回傳 False。
        except Exception as exc:  # 逐行註解：捕捉其他非預期錯誤，不讓 bot 整個崩潰。
            print(f"Discord 訊息 edit 非預期失敗：{type(exc).__name__}: {exc}")  # 逐行註解：把錯誤印到後台，不用 pass 吃掉。
            return False  # 逐行註解：遇到非預期錯誤就安全停止這次 edit。
    return False  # 逐行註解：理論上不會走到這裡，保留保險回傳值。


def register_active_ai_run(user_id: int, label: str, task: asyncio.Task | None, *, status_message=None, stop_event=None) -> dict:  # 逐行註解：登記一個可被 /stop 停止的 AI 任務。
    run = {  # 逐行註解：建立任務狀態字典，集中保存取消時需要的物件。
        "user_id": user_id,  # 逐行註解：保存 Discord 使用者 ID，作為 active_ai_runs 的 key。
        "label": label,  # 逐行註解：保存任務來源，例如 DM、/ask 或 /web_search。
        "task": task,  # 逐行註解：保存目前 coroutine task，/stop 會對它 cancel。
        "status_message": status_message,  # 逐行註解：保存 Thinking 或進度訊息，/stop 會把它改成停止文字。
        "stop_event": stop_event,  # 逐行註解：保存 Thinking 動畫事件，/stop 會先讓動畫停止。
        "created_at": time.monotonic(),  # 逐行註解：保存開始時間，方便後台或之後除錯使用。
    }  # 逐行註解：結束任務狀態字典。
    active_ai_runs[user_id] = run  # 逐行註解：用使用者 ID 登記目前最新的 AI 任務。
    return run  # 逐行註解：回傳這次登記的任務物件，收尾時可確認是不是同一個任務。


def finish_active_ai_run(user_id: int, run: dict | None) -> None:  # 逐行註解：移除已完成或已取消的 AI 任務登記。
    if run is None:  # 逐行註解：沒有任務物件時不需要處理。
        return  # 逐行註解：直接結束收尾。
    if active_ai_runs.get(user_id) is run:  # 逐行註解：只有目前登記仍是同一個任務時才移除，避免誤刪新任務。
        active_ai_runs.pop(user_id, None)  # 逐行註解：移除這位使用者的活躍 AI 任務。


async def stop_active_ai_run(user_id: int) -> bool:  # 逐行註解：停止指定使用者目前正在執行的 AI 任務。
    run = active_ai_runs.get(user_id)  # 逐行註解：從全域狀態取出該使用者目前的 AI 任務。
    if not run:  # 逐行註解：如果沒有登記中的任務，就代表目前沒有可停止的 AI 思考。
        return False  # 逐行註解：回傳 False 讓 /stop 告知使用者沒有任務。
    stop_event = run.get("stop_event")  # 逐行註解：取出 Thinking 動畫停止事件。
    if stop_event is not None:  # 逐行註解：如果這個任務有 Thinking 動畫事件，就先通知動畫停止。
        stop_event.set()  # 逐行註解：停止 Thinking 動畫，避免 /stop 後訊息繼續跳動。
    task = run.get("task")  # 逐行註解：取出真正執行 AI 的 asyncio task。
    if task is not None and not task.done():  # 逐行註解：如果任務還在跑，就發出取消請求。
        task.cancel()  # 逐行註解：取消任務，ask_ollama_text 會收到 CancelledError 並 kill Ollama subprocess。
    status_message = run.get("status_message")  # 逐行註解：取出可以編輯的 Thinking 或進度訊息。
    if status_message is not None:  # 逐行註解：如果有狀態訊息，就直接改成停止提示。
        await safe_edit_message(status_message, STOP_AI_MESSAGE)  # 逐行註解：在原本 Thinking 訊息位置顯示已停止。
    active_ai_runs.pop(user_id, None)  # 逐行註解：立即移除活躍任務，避免重複 /stop。
    return True  # 逐行註解：回傳 True 表示已送出停止請求。


def resolve_thinking_model_name(model_source) -> str:  # 逐行註解：從固定字串或可變狀態 dict 取得目前 Thinking 要顯示的模型名稱。
    if isinstance(model_source, dict):  # 逐行註解：如果呼叫端傳入 dict，代表模型可能會在流程中切換。
        return str(model_source.get("model") or DEFAULT_CHAT_MODEL)  # 逐行註解：從 dict 讀最新模型，沒有就回預設模型。
    return str(model_source or DEFAULT_CHAT_MODEL)  # 逐行註解：固定字串或空值時回傳可用模型名稱。


def resolve_progress_text(progress_state) -> str:  # 逐行註解：從附件分析進度狀態讀取目前要顯示的進度文字。
    if isinstance(progress_state, dict):  # 逐行註解：如果呼叫端有傳進度 dict，就讀取最新進度。
        return str(progress_state.get("text") or "").strip()  # 逐行註解：回傳整理後進度文字。
    return ""  # 逐行註解：沒有進度狀態時回空字串。


async def run_thinking_animation(message: discord.Message, stop_event: asyncio.Event, model_name, progress_state=None):  # 逐行註解：定義 Thinking 動畫 coroutine，會反覆 edit 同一則訊息。
    """在 AI 正式回答前循環顯示模型名稱 Thinking 動畫。"""  # 逐行註解：正式回答開始前會先 stop，避免兩個 coroutine 同時 edit。
    frame_index = 0  # 逐行註解：記錄目前要顯示第幾格動畫。
    while not stop_event.is_set():  # 逐行註解：只要外部還沒有要求停止，就持續播放動畫。
        frame = THINKING_FRAMES[frame_index % len(THINKING_FRAMES)]  # 逐行註解：用取餘數方式讓動畫清單循環。
        current_model_name = resolve_thinking_model_name(model_name)  # 逐行註解：每一格都重新讀模型名稱，讓按鈕切換後能即時更新成 gemma4_thinking。
        progress_text = resolve_progress_text(progress_state)  # 逐行註解：每一格都重新讀附件分析進度。
        shown_text = thinking_animation_text(current_model_name, frame)  # 逐行註解：先建立原本的 Thinking 動畫文字。
        if progress_text:  # 逐行註解：如果目前有附件分析進度，就顯示在 Thinking 動畫下一行。
            shown_text = f"{shown_text}\n{progress_text}"  # 逐行註解：把進度接到同一則 Thinking 訊息中。
        ok = await safe_edit_message(message, shown_text)  # 逐行註解：安全更新同一則訊息成目前動畫格與最新進度。
        if not ok:  # 逐行註解：如果 edit 失敗，就停止動畫，避免無限重試。
            stop_event.set()  # 逐行註解：通知外部這個動畫已經停止。
            return  # 逐行註解：離開動畫 coroutine。
        frame_index += 1  # 逐行註解：下一輪換下一格動畫。
        try:  # 逐行註解：等待指定秒數，期間如果 stop_event 被觸發就會提早醒來。
            await asyncio.wait_for(stop_event.wait(), timeout=THINKING_EDIT_DELAY)  # 逐行註解：用 0.55 秒作為動畫更新頻率。
        except TimeoutError:  # 逐行註解：時間到代表該顯示下一格動畫。
            continue  # 逐行註解：回到 while 開頭更新下一格。


async def show_temporary_thinking_process(message: discord.Message, thinking_text: str):  # 逐行註解：定義暫時顯示 thinking process 的函式。
    """把 thinking process 顯示在 code box 裡 3 秒，下一步正式回答會 edit 掉它。"""  # 逐行註解：沒有 thinking process 時不做任何事。
    if not (thinking_text or "").strip():  # 逐行註解：如果模型沒有回傳 thinking process，就直接跳過。
        return  # 逐行註解：不顯示空 code box。
    ok = await safe_edit_message(message, format_thinking_process_code_box(thinking_text))  # 逐行註解：把同一則 Thinking 訊息改成 thinking process code box。
    if ok:  # 逐行註解：只有成功顯示時才等待 3 秒。
        await asyncio.sleep(THINKING_PROCESS_DISPLAY_SECONDS)  # 逐行註解：讓使用者看 3 秒，之後由正式回答覆蓋。


def streaming_lines(text: str) -> list[str]:  # 逐行註解：定義函式 streaming_lines，把完整回答拆成適合逐行顯示的清單。
    """把 AI 回答依換行與寬度拆成多行，讓 Discord 像 terminal 一樣慢慢長出來。"""  # 逐行註解：這裡只做切行，不做任何百分比或進度條。
    raw_lines = (text or "").splitlines() or [text or "（我沒有產生任何回覆）"]  # 逐行註解：先依照原本換行切開，空回答則放入預設文字。
    output_lines: list[str] = []  # 逐行註解：建立最後要逐行顯示的清單。
    for raw_line in raw_lines:  # 逐行註解：逐一處理 AI 回答中的每一行。
        if not raw_line.strip():  # 逐行註解：如果這行是空白行，仍要保留下來讓段落有空隙。
            output_lines.append("")  # 逐行註解：加入空白行。
            continue  # 逐行註解：跳到下一行。
        wrapped = textwrap.wrap(raw_line, width=110, break_long_words=False, replace_whitespace=False)  # 逐行註解：太長的行先包成多行，避免單行太長不好讀。
        output_lines.extend(wrapped or [raw_line])  # 逐行註解：把包好的行加入輸出清單。
    return output_lines  # 逐行註解：回傳適合逐行顯示的文字清單。


async def stream_lines_to_message(message: discord.Message, text: str, send_extra=None):  # 逐行註解：定義一次性顯示函式，正式回答開始後直接 edit 訊息。
    """把正式回答一次全部 edit 到 Discord，不分批顯示。"""  # 逐行註解：send_extra 可用來發送超過單則上限後的下一則 followup。
    text_to_show = (text or "").strip() or "（我沒有產生任何回覆）"  # 逐行註解：如果沒有文字就用預設訊息。
    chart_payload = parse_chart_reply(text_to_show)  # 逐行註解：正式送文字前先檢查是不是圖表 JSON，避免 JSON 被直接送到 Discord。
    if chart_payload:  # 逐行註解：如果偵測到圖表 JSON，就改成傳送圖表 PNG。
        await send_chart_payload_to_message_channel(message.channel, chart_payload, status_message=message)  # 逐行註解：用 BytesIO 和 discord.File 把圖表送到原頻道。
        return  # 逐行註解：圖表已送出，不再進入文字分段流程。
    if looks_like_chart_json_response(text_to_show):  # 逐行註解：如果像圖表 JSON 但解析失敗，也不能把原始 JSON 送到 Discord。
        await safe_edit_message(message, CHART_PARSE_FAILED_MESSAGE)  # 逐行註解：把 Thinking 訊息改成安全錯誤提示，不洩漏 JSON。
        return  # 逐行註解：已攔截疑似圖表 JSON，停止文字流程。
    current_message = message  # 逐行註解：目前正在 edit 的 Discord 訊息。

    if len(text_to_show) > 1850:  # 逐行註解：如果文字超過 Discord 單則上限，要分拆成多則。
        chunks = textwrap.wrap(text_to_show, width=1850, break_long_words=False, replace_whitespace=False)  # 逐行註解：把超長文字切成多則。
        ok = await safe_edit_message(current_message, chunks[0] or " ")  # 逐行註解：第一則用 edit 原訊息。
        if not ok:  # 逐行註解：如果 edit 失敗，就停止。
            return  # 逐行註解：離開函式。
        for chunk in chunks[1:]:  # 逐行註解：後續chunks用新訊息送出。
            if send_extra is not None:  # 逐行註解：slash 指令可以傳入 followup.send 當作下一則訊息建立方式。
                current_message = await send_extra(chunk or " ")  # 逐行註解：用呼叫端提供的方法送下一則訊息。
            else:  # 逐行註解：一般 DM 或頻道訊息就直接用 channel.send。
                current_message = await current_message.channel.send(chunk or " ")  # 逐行註解：送出新訊息。
    else:  # 逐行註解：如果沒超過限制，直接 edit 成完整文字。
        ok = await safe_edit_message(current_message, text_to_show or " ")  # 逐行註解：安全 edit 訊息，遇到 rate limit 會有限重試。
        if not ok:  # 逐行註解：如果 edit 失敗，就停止。
            return  # 逐行註解：離開函式。


async def send_chunks_with_temporary_thinking(channel: discord.abc.Messageable, chunks: list[str], thinking_text: str = ""):  # 逐行註解：保留舊函式名稱，避免其他呼叫點壞掉。
    """舊相容函式：現在只直接送出文字，不再顯示 thinking process。"""  # 逐行註解：新的 Thinking 動畫由 run_thinking_animation 負責。
    joined_text = "\n".join(chunks or []).strip()  # 逐行註解：先把分段文字接回完整回答，避免 JSON 被切段後漏判。
    chart_payload = parse_chart_reply(joined_text)  # 逐行註解：送出文字前先檢查是否為圖表 JSON。
    if chart_payload:  # 逐行註解：如果是圖表 JSON，就送圖表檔案而不是 JSON 文字。
        await send_chart_payload_to_message_channel(channel, chart_payload)  # 逐行註解：用 BytesIO 和 discord.File 把圖表送到原頻道。
        return  # 逐行註解：圖表已送出，不再傳文字。
    if looks_like_chart_json_response(joined_text):  # 逐行註解：解析失敗但看起來是圖表 JSON 時，禁止把 JSON 當文字送出。
        await channel.send(CHART_PARSE_FAILED_MESSAGE)  # 逐行註解：改送安全錯誤提示。
        return  # 逐行註解：已攔截疑似圖表 JSON，停止文字流程。
    for chunk in chunks:  # 逐行註解：逐段送出切好的文字。
        await channel.send(chunk)  # 逐行註解：把這一段文字送到 Discord。


async def send_followup_chunks_with_temporary_thinking(  # 逐行註解：定義非同步函式 send_followup_chunks_with_temporary_thinking，可以搭配 await 處理 Discord 或網路等待。
    interaction: discord.Interaction,  # 逐行註解：這行是跨行資料或參數的一個項目。
    chunks: list[str],  # 逐行註解：這行是跨行資料或參數的一個項目。
    *,  # 逐行註解：這行是跨行資料或參數的一個項目。
    ephemeral: bool,  # 逐行註解：這行是跨行資料或參數的一個項目。
    thinking_text: str = "",  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    first_message=None,  # 逐行註解：設定 first_message 這個變數，供後面的流程使用。
):  # 逐行註解：這行開啟一個程式區塊，下面縮排內容會一起執行。
    """Slash 指令 followup 相容函式；web_search 會用它把進度訊息改成正式回答。"""  # 逐行註解：這裡不顯示新的 Thinking 動畫，避免影響 /web_search 原本進度。
    if not chunks:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    joined_text = "\n".join(chunks or []).strip()  # 逐行註解：先把分段文字接回完整回答，避免 JSON 被切段後漏判。
    chart_payload = parse_chart_reply(joined_text)  # 逐行註解：slash followup 送出文字前先檢查是否為圖表 JSON。
    if chart_payload:  # 逐行註解：如果是圖表 JSON，就送圖表檔案而不是 JSON 文字。
        await send_chart_payload_to_interaction_channel(interaction, chart_payload, status_message=first_message, ephemeral=ephemeral)  # 逐行註解：用 BytesIO 和 discord.File 把圖表送到原頻道。
        return  # 逐行註解：圖表已送出，不再傳文字。
    if looks_like_chart_json_response(joined_text):  # 逐行註解：解析失敗但看起來是圖表 JSON 時，禁止把 JSON 當文字送出。
        if first_message is not None:  # 逐行註解：如果有進度訊息，就直接改成安全錯誤提示。
            await safe_edit_message(first_message, CHART_PARSE_FAILED_MESSAGE)  # 逐行註解：避免進度訊息變成原始 JSON。
        else:  # 逐行註解：沒有進度訊息時，用 followup 送安全錯誤提示。
            await interaction.followup.send(CHART_PARSE_FAILED_MESSAGE, ephemeral=ephemeral)  # 逐行註解：用 slash followup 傳送安全錯誤提示。
        return  # 逐行註解：已攔截疑似圖表 JSON，停止文字流程。
    if first_message is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await safe_edit_message(first_message, chunks[0])  # 逐行註解：把 /web_search 的進度訊息改成正式回答第一段。
        for chunk in chunks[1:]:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
            await interaction.followup.send(chunk, ephemeral=ephemeral)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    for chunk in chunks:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        await interaction.followup.send(chunk, ephemeral=ephemeral)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。


CHART_TYPE_NAMES = {  # 逐行註解：建立圖表類型顯示名稱查詢表。
    "bar": "長條圖",  # 逐行註解：bar 對應長條圖。
    "line": "折線圖",  # 逐行註解：line 對應折線圖。
    "pie": "圓餅圖",  # 逐行註解：pie 對應圓餅圖。
}  # 逐行註解：結束圖表類型顯示名稱查詢表。
CHART_PARSE_FAILED_MESSAGE = f"{ERROR} 圖表 JSON 解析失敗，後台已印出完整 traceback。"  # 逐行註解：圖表資料壞掉時給 Discord 使用者看的安全訊息，不顯示原始 JSON。
CHART_TYPE_ALIASES = {  # 逐行註解：建立圖表類型別名表，避免模型輸出中文或底線格式時解析失敗。
    "bar": "bar",  # 逐行註解：標準 bar 對應長條圖。
    "bar_chart": "bar",  # 逐行註解：bar_chart 也視為長條圖。
    "bar chart": "bar",  # 逐行註解：bar chart 也視為長條圖。
    "長條圖": "bar",  # 逐行註解：中文長條圖轉成 bar。
    "柱狀圖": "bar",  # 逐行註解：中文柱狀圖轉成 bar。
    "line": "line",  # 逐行註解：標準 line 對應折線圖。
    "line_chart": "line",  # 逐行註解：line_chart 也視為折線圖。
    "line chart": "line",  # 逐行註解：line chart 也視為折線圖。
    "折線圖": "line",  # 逐行註解：中文折線圖轉成 line。
    "pie": "pie",  # 逐行註解：標準 pie 對應圓餅圖。
    "pie_chart": "pie",  # 逐行註解：pie_chart 也視為圓餅圖。
    "pie chart": "pie",  # 逐行註解：pie chart 也視為圓餅圖。
    "圓餅圖": "pie",  # 逐行註解：中文圓餅圖轉成 pie。
    "餅圖": "pie",  # 逐行註解：中文餅圖轉成 pie。
}  # 逐行註解：結束圖表類型別名表。


def chart_output_rules_prompt() -> str:  # 逐行註解：建立給 Ollama 的圖表 JSON 輸出規則。
    lines = [  # 逐行註解：用清單組規則，避免多行字串難以維護。
        "如果使用者要求圖表、趨勢、比較、比例、統計、成績、排名、資料視覺化，且你能整理出 labels 與 values，請只輸出 JSON。",  # 逐行註解：告訴模型何時要產生圖表 JSON。
        "如果使用者明確說長條圖、折線圖、圓餅圖，chart_type 必須分別使用 bar、line、pie。",  # 逐行註解：把中文圖表名稱固定映射到程式支援的 chart_type。
        "像「小明80」「星期一10」「蘋果40」這種標籤和數字黏在一起的資料，也要拆成 label 與 value。",  # 逐行註解：避免模型因沒有空白就誤以為資料不足。
        "不要輸出 Markdown code block，不要輸出解釋文字，不要把 JSON 包在其他句子裡。",  # 逐行註解：避免模型在 JSON 外加文字導致解析失敗。
        "JSON 格式必須完全符合：",  # 逐行註解：提示下面是固定格式。
        '{"type":"chart","chart_type":"bar","title":"成績比較","labels":["小明","小華","小美"],"values":[80,92,75]}',  # 逐行註解：提供可解析的圖表 JSON 範例。
        '{"type":"chart","chart_type":"line","title":"折線圖","labels":["星期一","星期二","星期三"],"values":[10,20,15]}',  # 逐行註解：提供折線圖 JSON 範例，讓模型知道 line 要怎麼輸出。
        '{"type":"chart","chart_type":"pie","title":"圓餅圖","labels":["蘋果","香蕉","橘子"],"values":[40,30,30]}',  # 逐行註解：提供圓餅圖 JSON 範例，讓模型知道 pie 要怎麼輸出。
        "chart_type 只能是 bar、line、pie。",  # 逐行註解：限制圖表種類，方便程式端對應 matplotlib 函式。
        "labels 必須是字串陣列，values 必須是數字陣列，兩者長度必須相同。",  # 逐行註解：限制資料型別，避免產生無法繪圖的內容。
        "如果不需要圖表，就正常用繁體中文回答，不要輸出 JSON。",  # 逐行註解：避免一般聊天被誤轉成圖表。
    ]  # 逐行註解：結束規則清單。
    return "\n".join(lines).strip()  # 逐行註解：回傳完整圖表規則。


def debug_ai_response(response: str) -> None:  # 逐行註解：集中印出 AI 原始回覆，方便確認模型到底吐了什麼。
    print("=== AI RESPONSE ===")  # 逐行註解：除錯標題，標記下面是 AI 回覆原文。
    print(response)  # 逐行註解：印出完整 AI 回覆內容。


def debug_json_parsed(chart_data: dict) -> None:  # 逐行註解：集中印出已解析出的圖表資料。
    print("=== JSON PARSED ===")  # 逐行註解：除錯標題，標記下面是標準化後的圖表 dict。
    print(chart_data)  # 逐行註解：印出圖表資料，確認 labels、values、chart_type 都正確。


def debug_chart_type(chart_type: str) -> None:  # 逐行註解：集中印出圖表類型，方便確認分支會走 bar、line 或 pie。
    print("=== CHART TYPE ===")  # 逐行註解：除錯標題，標記下面是圖表類型。
    print(chart_type)  # 逐行註解：印出標準化後的 chart_type。


def print_chart_traceback(reason: str) -> None:  # 逐行註解：圖表解析或繪圖失敗時完整印出 traceback。
    try:  # 逐行註解：刻意建立例外，讓非例外型格式錯誤也能有完整 traceback。
        raise ValueError(reason)  # 逐行註解：把失敗原因包成 ValueError。
    except ValueError:  # 逐行註解：立刻捕捉剛建立的錯誤以便印 traceback。
        print(f"圖表處理失敗：{reason}")  # 逐行註解：先印出人類可讀的失敗原因。
        traceback.print_exc()  # 逐行註解：印出完整 traceback，方便追到解析流程。


def normalize_chart_type_name(raw_chart_type) -> str:  # 逐行註解：把模型輸出的 chart_type 統一轉成 bar、line 或 pie。
    chart_type_text = str(raw_chart_type or "").strip().lower()  # 逐行註解：先轉字串、去空白並小寫化。
    chart_type_text = chart_type_text.replace("-", "_")  # 逐行註解：把 dash 格式轉成底線格式。
    chart_type = CHART_TYPE_ALIASES.get(chart_type_text, chart_type_text)  # 逐行註解：套用別名表取得標準 chart_type。
    debug_chart_type(chart_type)  # 逐行註解：依需求印出目前圖表類型。
    return chart_type  # 逐行註解：回傳標準化圖表類型。


def looks_like_chart_json_response(raw_text: str) -> bool:  # 逐行註解：判斷一段文字是否像圖表 JSON，避免解析失敗後把 JSON 洩漏到 Discord。
    response = str(raw_text or "")  # 逐行註解：把輸入安全轉成字串。
    lowered = response.lower()  # 逐行註解：小寫化方便搜尋英文 key。
    has_json_shape = "{" in response and "}" in response  # 逐行註解：至少要看起來像 JSON object。
    has_chart_marker = "chart" in lowered or "chart_type" in lowered  # 逐行註解：需要包含 chart 或 chart_type 才視為圖表候選。
    has_type_marker = "type" in lowered or "chart_type" in lowered  # 逐行註解：需要包含 type 或 chart_type 才像目標格式。
    return has_json_shape and has_chart_marker and has_type_marker  # 逐行註解：三個條件都成立才攔截解析失敗的圖表 JSON。


def requested_chart_type_from_text(user_text: str) -> str:  # 逐行註解：從使用者原始訊息判斷想要哪一種圖表。
    text = (user_text or "").strip().lower()  # 逐行註解：整理訊息並小寫化，方便比對英文關鍵字。
    if any(keyword in text for keyword in ("長條圖", "柱狀圖", "bar chart", "bar")):  # 逐行註解：辨識長條圖需求。
        return "bar"  # 逐行註解：回傳 bar 給 matplotlib 長條圖分支。
    if any(keyword in text for keyword in ("折線圖", "折线图", "line chart", "line")):  # 逐行註解：辨識折線圖需求。
        return "line"  # 逐行註解：回傳 line 給 matplotlib 折線圖分支。
    if any(keyword in text for keyword in ("圓餅圖", "圆饼图", "餅圖", "饼图", "pie chart", "pie")):  # 逐行註解：辨識圓餅圖需求。
        return "pie"  # 逐行註解：回傳 pie 給 matplotlib 圓餅圖分支。
    return ""  # 逐行註解：沒有明確圖表需求時回傳空字串。


def clean_stable_chart_label(raw_label: str) -> str:  # 逐行註解：清理穩定圖表 parser 抓到的標籤，避免把指令詞當成資料名稱。
    label = str(raw_label or "").strip(" \t\r\n-:：,，、;；")  # 逐行註解：先把標籤轉成字串並移除常見分隔符。
    label = re.split(r"[，,、;；]", label)[-1].strip(" \t\r\n-:：,，、;；")  # 逐行註解：若標籤前面混到指令文字，就保留最後一段候選標籤。
    prefix_patterns = (  # 逐行註解：建立可重複移除的指令前綴規則。
        r"^(?:請你|請|麻煩你|麻煩|幫我|幫忙|幫|替我)\s*",  # 逐行註解：移除禮貌或請求開頭。
        r"^(?:畫出|畫一個|畫個|畫|做出|做一個|做個|做|產生|建立|生成|給我|用)\s*",  # 逐行註解：移除畫圖或產生圖表的動作詞。
        r"^(?:一個|一張|張|個)\s*",  # 逐行註解：移除中文數量詞。
        r"^(?:圓餅圖|圆饼图|餅圖|饼图|長條圖|柱狀圖|折線圖|折线图|bar chart|pie chart|line chart|bar|pie|line|chart|graph|plot)\s*",  # 逐行註解：移除圖表類型詞。
    )  # 逐行註解：結束前綴規則清單。
    previous_label = None  # 逐行註解：保存上一輪清理結果，用來判斷是否還有前綴可移除。
    while previous_label != label:  # 逐行註解：持續清理直到標籤不再改變。
        previous_label = label  # 逐行註解：記錄本輪清理前的標籤。
        for pattern in prefix_patterns:  # 逐行註解：逐一套用所有前綴清理規則。
            label = re.sub(pattern, "", label, flags=re.IGNORECASE).strip(" \t\r\n-:：,，、;；")  # 逐行註解：移除符合的前綴並重新清掉分隔符。
    label = re.sub(r"^(?:的|之)\s*", "", label).strip(" \t\r\n-:：,，、;；")  # 逐行註解：移除中文連接詞，處理「的圓餅圖」殘留情況。
    return label  # 逐行註解：回傳可用於圖表顯示的乾淨標籤。


def stable_parse_chart_data_from_user_text(user_text: str) -> tuple[list[str], list[float]]:  # 逐行註解：直接從使用者原始訊息穩定解析圖表 labels 與 values。
    labels: list[str] = []  # 逐行註解：建立解析出的標籤清單。
    values: list[float] = []  # 逐行註解：建立解析出的數值清單。
    text = str(user_text or "").strip()  # 逐行註解：把原始訊息轉成字串並清理頭尾空白。
    if not text:  # 逐行註解：空訊息沒有任何圖表資料可解析。
        return labels, values  # 逐行註解：回傳空清單，讓呼叫端改走其他流程。
    pair_pattern = re.compile(r"([^0-9+\-:：,，、;；\n]+?)\s*[:：]?\s*([-+]?\d+(?:\.\d+)?)%?")  # 逐行註解：支援「香蕉20」「香蕉 20」「香蕉：20」「香蕉:20」等格式。
    for match in pair_pattern.finditer(text):  # 逐行註解：逐一找出訊息中所有標籤與數字配對。
        label = clean_stable_chart_label(match.group(1))  # 逐行註解：清理配對中的標籤文字。
        if not label:  # 逐行註解：空標籤不能拿來畫圖。
            continue  # 逐行註解：略過無效配對，繼續看下一組。
        try:  # 逐行註解：數值轉換可能失敗，所以用 try 保護。
            value = float(match.group(2))  # 逐行註解：把抓到的數字文字轉成 float。
        except (TypeError, ValueError):  # 逐行註解：若不是有效數字，就不要讓整個 parser 崩潰。
            continue  # 逐行註解：略過這組壞資料。
        labels.append(label)  # 逐行註解：保存有效標籤。
        values.append(value)  # 逐行註解：保存有效數值。
    return labels, values  # 逐行註解：回傳所有解析出的圖表資料。


def extract_label_value_pairs_from_user_text(user_text: str) -> tuple[list[str], list[float]]:  # 逐行註解：從使用者訊息中抽取「標籤+數字」資料列。
    labels: list[str] = []  # 逐行註解：建立標籤清單。
    values: list[float] = []  # 逐行註解：建立數值清單。
    pair_pattern = re.compile(r"(?:^|[、,，;；\n])\s*([^:：,，、;；\n]+?)\s*[:：]\s*([-+]?\d+(?:\.\d+)?)%?")  # 逐行註解：支援同一行多組「label: value」資料。

    def _clean_chart_label(raw_label: str) -> str:  # 逐行註解：清理圖表資料標籤，避免把「畫一個」這類指令文字當成標籤。
        label = (raw_label or "").strip(" -:：,，、;；")
        label = re.sub(r"^(?:請你|請|麻煩你|麻煩|幫我|幫忙|幫|替我)?\s*", "", label)
        label = re.sub(r"^(?:畫出|畫一個|畫個|畫|做出|做一個|做個|做|產生|建立|生成|給我|用)\s*", "", label)
        label = re.sub(r"^(?:一個|一張|張|個)\s*", "", label)
        label = label.strip(" -:：,，、;；")
        # 英文資料常見於「畫一個apple:3」，保留最後一段英文標籤。
        english_tail = re.search(r"([A-Za-z][A-Za-z0-9 _-]*)$", label)
        if english_tail:
            label = english_tail.group(1).strip()
        return label

    for match in pair_pattern.finditer(user_text or ""):  # 逐行註解：先處理同一行用逗號、頓號分隔的多筆資料。
        label = _clean_chart_label(match.group(1))
        if not label:
            continue
        labels.append(label)
        values.append(float(match.group(2)))

    if labels:  # 逐行註解：同一行多資料已成功解析時直接回傳。
        return labels, values

    for raw_line in (user_text or "").splitlines():  # 逐行註解：逐行處理使用者輸入。
        line = raw_line.strip()  # 逐行註解：整理每一行頭尾空白。
        if not line:  # 逐行註解：空行不含資料。
            continue  # 逐行註解：跳過空行。
        match = re.match(r"^(.+?)[\s:：,，]*([-+]?\d+(?:\.\d+)?)%?\s*$", line)  # 逐行註解：支援「小明80」「小明 80」「小明：80」等格式。
        if not match:  # 逐行註解：沒有匹配到標籤與數字就不是資料列。
            continue  # 逐行註解：跳過非資料列。
        label = _clean_chart_label(match.group(1))  # 逐行註解：取出資料標籤並清掉分隔符。
        if not label:  # 逐行註解：空標籤不能畫圖。
            continue  # 逐行註解：跳過無效資料列。
        labels.append(label)  # 逐行註解：保存有效標籤。
        values.append(float(match.group(2)))  # 逐行註解：保存有效數值。
    return labels, values  # 逐行註解：回傳抽取出的標籤與數值。


def fallback_chart_title_from_user_text(user_text: str, chart_type: str) -> str:  # 逐行註解：依使用者訊息建立保底圖表標題。
    text = user_text or ""  # 逐行註解：保留原始文字供關鍵字判斷。
    if "成績" in text:  # 逐行註解：成績資料使用較貼近內容的標題。
        return "成績比較"  # 逐行註解：回傳成績圖表標題。
    return CHART_TYPE_NAMES.get(chart_type, "圖表")  # 逐行註解：其他資料用圖表類型當標題。


def build_chart_payload_from_user_text(user_text: str) -> dict | None:  # 逐行註解：模型沒有回圖表 JSON 時，從使用者訊息本身建立保底 chart payload。
    chart_type = requested_chart_type_from_text(user_text)  # 逐行註解：先確認使用者是否明確要求支援的圖表類型。
    if chart_type not in CHART_TYPE_NAMES:  # 逐行註解：沒有圖表需求就不啟動保底流程。
        return None  # 逐行註解：回傳 None 讓一般聊天維持原流程。
    labels, values = stable_parse_chart_data_from_user_text(user_text)  # 逐行註解：優先用穩定 parser 直接從使用者原文解析資料。
    if not labels or len(labels) != len(values):  # 逐行註解：穩定 parser 沒抓到完整資料時才改用既有 parser。
        labels, values = parse_chart_text(user_text)  # 逐行註解：使用原本獨立 parser 作為第二層備援。
    if not labels or len(labels) != len(values):  # 逐行註解：第二層 parser 仍失敗時改用舊的逐行 parser。
        labels, values = extract_label_value_pairs_from_user_text(user_text)  # 逐行註解：保留舊流程相容既有輸入格式。
    # 逐行註解：資料不足時不能畫圖。
    if not labels or len(labels) != len(values):  # 逐行註解：資料不足時不能畫圖。
        return None  # 逐行註解：回傳 None 讓一般回覆維持原流程。
    chart_data = {  # 逐行註解：建立與 AI JSON 相同格式的圖表資料。
        "type": "chart",  # 逐行註解：標記這是一筆圖表資料。
        "chart_type": chart_type,  # 逐行註解：保存標準化圖表類型。
        "title": fallback_chart_title_from_user_text(user_text, chart_type),  # 逐行註解：保存保底圖表標題。
        "labels": labels,  # 逐行註解：保存資料標籤。
        "values": values,  # 逐行註解：保存資料數值。
    }  # 逐行註解：結束 chart payload。
    print("偵測到使用者圖表資料，改用程式保底產生圖表")  # 逐行註解：後台標記這次不是模型 JSON，而是程式保底。
    debug_chart_type(chart_type)  # 逐行註解：依需求印出 chart_type。
    debug_json_parsed(chart_data)  # 逐行註解：依需求印出組出的 chart_data。
    return chart_data  # 逐行註解：回傳可直接送進 chart_utils 的圖表資料。


def strip_markdown_json_code_block(raw_text: str) -> str:  # 逐行註解：清掉模型可能包住 JSON 的 markdown code block。
    cleaned = ANSI_ESCAPE_RE.sub("", str(raw_text or "").strip())  # 逐行註解：先移除 ANSI 控制碼並整理頭尾空白。
    fence_match = re.fullmatch(r"(?is)```(?:json)?\s*(.*?)\s*```", cleaned)  # 逐行註解：偵測整段內容是否被 ```json 或 ``` 包住。
    if fence_match:  # 逐行註解：如果整段文字是 markdown code block。
        return fence_match.group(1).strip()  # 逐行註解：只回傳 code block 裡面的 JSON 內容。
    return cleaned  # 逐行註解：沒有 code block 時回傳清理後原文。


def extract_first_json_object_text(raw_text: str) -> str:  # 逐行註解：從模型回覆中抓出第一個 JSON 物件文字。
    cleaned = strip_markdown_json_code_block(raw_text)  # 逐行註解：先清掉 markdown JSON code block，再進行 JSON 掃描。
    decoder = json.JSONDecoder()  # 逐行註解：建立 JSON decoder，用 raw_decode 從任意位置解析。
    for index, char in enumerate(cleaned):  # 逐行註解：逐字尋找可能的 JSON 物件起點。
        if char != "{":  # 逐行註解：只有左大括號才可能是 JSON 物件開頭。
            continue  # 逐行註解：不是大括號就繼續找下一個字元。
        try:  # 逐行註解：嘗試從目前位置解析 JSON。
            data, end_index = decoder.raw_decode(cleaned[index:])  # 逐行註解：解析目前位置開始的第一個 JSON 值。
        except json.JSONDecodeError:  # 逐行註解：目前位置不是有效 JSON 時換下一個大括號。
            continue  # 逐行註解：繼續尋找下一個可能位置。
        if isinstance(data, dict):  # 逐行註解：圖表格式必須是 JSON object，也就是 Python dict。
            return cleaned[index:index + end_index]  # 逐行註解：回傳剛剛成功解析的 JSON 物件文字。
    return ""  # 逐行註解：找不到 JSON 物件時回傳空字串。


def fallback_chart_payload_from_raw_user_text(fallback_user_text: str) -> dict | None:  # 逐行註解：在模型 JSON 解析失敗時，用使用者原始訊息建立圖表資料。
    if not str(fallback_user_text or "").strip():  # 逐行註解：沒有原始使用者訊息時不能 fallback。
        return None  # 逐行註解：回傳 None 讓呼叫端維持原本失敗處理。
    return build_chart_payload_from_user_text(fallback_user_text)  # 逐行註解：呼叫穩定原文 parser 建立 chart payload。


def parse_chart_reply(raw_text: str, fallback_user_text: str = "") -> dict | None:  # 逐行註解：判斷模型回覆是否為圖表 JSON，失敗時可用使用者原文 fallback。
    response = str(raw_text or "")  # 逐行註解：保留 AI 回覆原文，除錯與解析都用同一份內容。
    should_debug_response = looks_like_chart_json_response(response)  # 逐行註解：只有看起來像圖表 JSON 時才印完整原文，避免一般聊天洗版。
    if should_debug_response:  # 逐行註解：如果像圖表 JSON，就依需求印出 AI 原始回覆。
        debug_ai_response(response)  # 逐行註解：印出 AI RESPONSE 區塊。
    try:  # 逐行註解：JSON 解析可能失敗，所以用 try 保護。
        json_text = extract_first_json_object_text(response)  # 逐行註解：先從模型回覆抽出 JSON 物件。
        if not json_text:  # 逐行註解：沒有 JSON 就代表是一般文字回答或模型格式錯誤。
            if should_debug_response:  # 逐行註解：看起來像圖表 JSON 卻抓不到物件時要印 traceback。
                print_chart_traceback("找不到可解析的 JSON object")  # 逐行註解：完整記錄解析失敗原因。
            fallback_payload = fallback_chart_payload_from_raw_user_text(fallback_user_text)  # 逐行註解：嘗試從使用者原始訊息補出圖表資料。
            if fallback_payload:  # 逐行註解：如果原始訊息能解析成功。
                return fallback_payload  # 逐行註解：直接回傳 fallback 圖表資料。
            return None  # 逐行註解：回傳 None，讓呼叫端決定是否攔截原文。
        data = json.loads(json_text)  # 逐行註解：把 JSON 文字轉成 Python dict。
    except Exception as e:  # 逐行註解：任何解析例外都完整印出 traceback，不只 JSONDecodeError。
        print(f"圖表 JSON 解析失敗：{type(e).__name__}: {e}")  # 逐行註解：先印出錯誤類型與摘要。
        traceback.print_exc()  # 逐行註解：依需求完整印出 traceback。
        fallback_payload = fallback_chart_payload_from_raw_user_text(fallback_user_text)  # 逐行註解：json.loads 失敗時改用正則解析使用者原始訊息。
        if fallback_payload:  # 逐行註解：如果 fallback 成功建立圖表資料。
            return fallback_payload  # 逐行註解：回傳 fallback 圖表資料，不讓壞 JSON 影響使用者。
        return None  # 逐行註解：解析失敗時改走一般文字流程。
    if not isinstance(data, dict):  # 逐行註解：圖表資料必須是 JSON object。
        return None  # 逐行註解：格式不符時改走一般文字流程。
    if str(data.get("type") or "").strip().lower() != "chart":  # 逐行註解：只有 type=chart 才啟動圖表輸出。
        return None  # 逐行註解：不是圖表 JSON 時改走一般文字流程。
    chart_type = normalize_chart_type_name(data.get("chart_type"))  # 逐行註解：讀取並整理圖表類型。
    if chart_type not in CHART_TYPE_NAMES:  # 逐行註解：圖表類型只允許 bar、line、pie。
        print_chart_traceback(f"不支援的 chart_type：{chart_type}")  # 逐行註解：支援外的類型要完整印出 traceback。
        return None  # 逐行註解：不支援的圖表類型改走一般文字流程。
    labels = data.get("labels")  # 逐行註解：讀取圖表標籤清單。
    values = data.get("values")  # 逐行註解：讀取圖表數值清單。
    if not isinstance(labels, list) or not isinstance(values, list):  # 逐行註解：labels 和 values 都必須是 JSON array。
        print_chart_traceback("labels 或 values 不是 JSON array")  # 逐行註解：資料格式錯誤時完整印 traceback。
        return None  # 逐行註解：資料格式不符時改走一般文字流程。
    if not labels or len(labels) != len(values):  # 逐行註解：資料不可空，標籤與數值數量也必須相同。
        print_chart_traceback("labels 與 values 數量不一致或為空")  # 逐行註解：資料數量錯誤時完整印 traceback。
        return None  # 逐行註解：資料數量不符時改走一般文字流程。
    normalized_labels = [str(label).strip() for label in labels]  # 逐行註解：將標籤統一轉成字串。
    normalized_values: list[float] = []  # 逐行註解：建立整理後的數值清單。
    for value in values:  # 逐行註解：逐一整理每個圖表數值。
        try:  # 逐行註解：數值轉換可能失敗，所以用 try 保護。
            normalized_values.append(float(value))  # 逐行註解：允許 int、float 或數字字串轉成 float。
        except (TypeError, ValueError):  # 逐行註解：遇到無法轉成數字的值時停止圖表流程。
            print_chart_traceback(f"values 包含無法轉成數字的值：{value}")  # 逐行註解：數值錯誤時完整印 traceback。
            return None  # 逐行註解：資料不合法時改走一般文字流程。
    if any(not label for label in normalized_labels):  # 逐行註解：空標籤會讓圖表難以閱讀。
        print_chart_traceback("labels 包含空字串")  # 逐行註解：空標籤錯誤時完整印 traceback。
        return None  # 逐行註解：有空標籤時改走一般文字流程。
    chart_data = {  # 逐行註解：建立標準化後的圖表資料。
        "type": "chart",  # 逐行註解：保留圖表型別。
        "chart_type": chart_type,  # 逐行註解：保存圖表種類。
        "title": str(data.get("title") or CHART_TYPE_NAMES[chart_type]).strip(),  # 逐行註解：保存圖表標題。
        "labels": normalized_labels,  # 逐行註解：保存整理後標籤。
        "values": normalized_values,  # 逐行註解：保存整理後數值。
    }  # 逐行註解：結束標準化圖表資料。
    print("偵測到圖表 JSON")  # 逐行註解：除錯輸出，確認程式真的有攔截 chart JSON。
    print(chart_data)  # 逐行註解：除錯輸出，印出已解析的圖表資料。
    debug_json_parsed(chart_data)  # 逐行註解：依需求印出 JSON PARSED 區塊。
    return chart_data  # 逐行註解：回傳標準化後的圖表資料。


def extract_all_json_objects(raw_text: str) -> list[str]:  # 逐行註解：從模型回覆中抓出所有可能是 JSON 物件的區塊。
    cleaned = ANSI_ESCAPE_RE.sub("", (raw_text or "").strip())  # 逐行註解：先移除 ANSI 控制碼與前後空白。
    results: list[str] = []  # 逐行註解：準備存放找到的所有 JSON 物件文字。
    decoder = json.JSONDecoder()  # 逐行註解：建立 JSON decoder。
    idx = 0  # 逐行註解：從字串開頭開始掃描。
    while idx < len(cleaned):  # 逐行註解：遍歷整個字串內容。
        if cleaned[idx] == "{":  # 逐行註解：發現左大括號，可能是 JSON 物件起點。
            try:  # 嘗試從目前位置解析 JSON。
                data, end_idx = decoder.raw_decode(cleaned[idx:])  # 逐行註解：解析第一個完整的 JSON 值。
                if isinstance(data, dict):  # 逐行註解：圖表必須是字典格式。
                    results.append(cleaned[idx:idx + end_idx])  # 逐行註解：擷取該段 JSON 文字並存入結果。
                idx += end_idx  # 逐行註解：掃描位置跳到該物件結束之後。
                continue  # 逐行註解：繼續尋找下一個物件。
            except json.JSONDecodeError:  # 逐行註解：如果目前大括號不是有效 JSON 的起點。
                pass  # 逐行註解：忽略此位置，繼續往後找。
        idx += 1  # 逐行註解：掃描位置往後移一個字元。
    return results  # 逐行註解：回傳所有找到的 JSON 物件文字清單。


def parse_all_charts_reply(raw_text: str) -> list[dict]:  # 逐行註解：從 AI 回覆中解析出所有符合圖表格式的資料。
    json_texts = extract_all_json_objects(raw_text)  # 逐行註解：擷取回覆中所有 JSON 物件文字。
    payloads = []  # 逐行註解：準備存放驗證通過的圖表資料。
    for jt in json_texts:  # 逐行註解：逐一檢查每個擷取出的 JSON。
        try:  # 嘗試進行圖表格式驗證。
            data = json.loads(jt)  # 逐行註解：將文字轉為字典。
            if not isinstance(data, dict) or str(data.get("type") or "").lower() != "chart":  # 逐行註解：檢查是否標記為 chart 類型。
                continue  # 逐行註解：不是圖表就跳過。
            chart_type = normalize_chart_type_name(data.get("chart_type"))  # 逐行註解：正規化圖表類型（如 bar, line, pie）。
            if chart_type not in CHART_TYPE_NAMES:  # 逐行註解：檢查是否為支援的圖表類型。
                continue  # 逐行註解：不支援則跳過。
            labels = data.get("labels")  # 逐行註解：讀取資料標籤。
            values = data.get("values")  # 逐行註解：讀取資料數值。
            if isinstance(labels, list) and isinstance(values, list) and labels and len(labels) == len(values):  # 逐行註解：檢查標籤與數值是否匹配且非空。
                payloads.append({  # 逐行註解：加入標準化的圖表 payload。
                    "type": "chart",
                    "chart_type": chart_type,
                    "title": str(data.get("title") or CHART_TYPE_NAMES[chart_type]).strip(),
                    "labels": [str(l).strip() for l in labels],
                    "values": [float(v) for v in values]
                })
        except Exception:  # 逐行註解：忽略個別 JSON 解析失敗的錯誤。
            continue
    return payloads  # 逐行註解：回傳所有有效圖表資料清單。


async def send_multiple_charts_to_interaction(interaction: discord.Interaction, payloads: list[dict], *, status_message: discord.Message | None = None, ephemeral: bool = False) -> None:  # 逐行註解：將多張圖表一次傳送到 Discord。
    files = []  # 逐行註解：準備存放圖表圖片檔案物件。
    summaries = []  # 逐行註解：準備存放每張圖表的完成摘要。
    for i, payload in enumerate(payloads, start=1):  # 逐行註解：逐一產生每一張圖表圖片。
        try:  # 嘗試繪製圖表。
            buffer = make_chart_buffer_from_payload(payload)  # 逐行註解：呼叫 matplotlib 產生圖片緩衝區。
            files.append(discord.File(buffer, filename=f"chart_{i}.png"))  # 逐行註解：封裝成 Discord 檔案物件。
            summaries.append(chart_reply_summary(payload))  # 逐行註解：取得該圖表的文字摘要（如：已產生圓餅圖...）。
        except Exception as e:  # 捕捉繪圖過程的錯誤。
            print(f"產生第 {i} 張圖表失敗：{type(e).__name__}: {e}")  # 在後台印出錯誤訊息。

    if not files:  # 逐行註解：如果沒有任何圖表產生成功。
        if status_message:  # 逐行註解：若有進度訊息，更新為錯誤提示。
            await safe_edit_message(status_message, CHART_PARSE_FAILED_MESSAGE)
        return  # 結束傳送流程。

    full_summary = "\n".join(summaries)  # 逐行註解：將所有圖表摘要合併為一段文字。
    if status_message:  # 逐行註解：將原本的「正在等待回答」訊息更新為圖表摘要。
        await safe_edit_message(status_message, full_summary)
    
    if interaction.channel:  # 逐行註解：優先透過頻道發送檔案。
        await interaction.channel.send(files=files)  # 逐行註解：一次傳送所有產生的圖表。
    else:  # 逐行註解：若無頻道物件，則使用 followup 備援發送。
        await interaction.followup.send(files=files, ephemeral=ephemeral)


def make_chart_buffer_from_payload(chart_payload: dict) -> io.BytesIO:  # 逐行註解：依 chart_type 呼叫對應的 matplotlib 圖表函式。
    chart_type = str(chart_payload.get("chart_type") or "").strip().lower()  # 逐行註解：取得標準化圖表類型。
    debug_chart_type(chart_type)  # 逐行註解：依需求在真正進入繪圖分支前印出 chart_type。
    title = chart_payload.get("title") or CHART_TYPE_NAMES.get(chart_type, "圖表")  # 逐行註解：取得圖表標題，缺少時使用預設名稱。
    labels = chart_payload.get("labels") or []  # 逐行註解：取得圖表標籤清單。
    values = chart_payload.get("values") or []  # 逐行註解：取得圖表數值清單。
    if chart_type == "bar":  # 逐行註解：bar 類型使用長條圖工具。
        return make_bar_chart(title, labels, values)  # 逐行註解：回傳長條圖 BytesIO。
    if chart_type == "line":  # 逐行註解：line 類型使用折線圖工具。
        return make_line_chart(title, labels, values)  # 逐行註解：回傳折線圖 BytesIO。
    if chart_type == "pie":  # 逐行註解：pie 類型使用圓餅圖工具。
        return make_pie_chart(title, labels, values)  # 逐行註解：回傳圓餅圖 BytesIO。
    raise ValueError(f"不支援的圖表類型：{chart_type}")  # 逐行註解：理論上 parse 已擋掉，這裡保留保險錯誤。


def chart_reply_summary(chart_payload: dict) -> str:  # 逐行註解：建立圖表送出前後可顯示的簡短狀態文字。
    chart_type = str(chart_payload.get("chart_type") or "").strip().lower()  # 逐行註解：取得圖表類型。
    chart_name = CHART_TYPE_NAMES.get(chart_type, "圖表")  # 逐行註解：將圖表類型轉成中文顯示名稱。
    title = str(chart_payload.get("title") or chart_name).strip()  # 逐行註解：取得圖表標題。
    return f"{SUCCESS} 已產生{chart_name}：{title}"  # 逐行註解：回傳不含 JSON 的圖表完成訊息。


async def send_chart_payload_to_message_channel(channel: discord.abc.Messageable, chart_payload: dict, *, status_message: discord.Message | None = None) -> None:  # 逐行註解：將圖表 BytesIO 傳送到一般訊息所在頻道。
    try:  # 逐行註解：繪圖可能因資料或 matplotlib 失敗，所以要完整捕捉。
        buffer = make_chart_buffer_from_payload(chart_payload)  # 逐行註解：根據圖表資料在記憶體中產生 PNG。
    except Exception as e:  # 逐行註解：任何繪圖錯誤都不能讓原始 JSON 回到 Discord。
        print(f"圖表 PNG 產生失敗：{type(e).__name__}: {e}")  # 逐行註解：印出繪圖錯誤摘要。
        traceback.print_exc()  # 逐行註解：完整印出 traceback，方便追蹤 chart_type 分支或資料問題。
        if status_message is not None:  # 逐行註解：如果有 Thinking 訊息，就改成安全錯誤提示。
            await safe_edit_message(status_message, CHART_PARSE_FAILED_MESSAGE)  # 逐行註解：避免顯示原始 JSON。
        else:  # 逐行註解：沒有可 edit 的訊息時，直接送安全錯誤提示。
            await channel.send(CHART_PARSE_FAILED_MESSAGE)  # 逐行註解：送出安全錯誤提示。
        return  # 逐行註解：錯誤已處理，停止傳檔流程。
    if status_message is not None:  # 逐行註解：如果呼叫端有 Thinking 訊息，就先把它改成完成訊息。
        await safe_edit_message(status_message, chart_reply_summary(chart_payload))  # 逐行註解：避免把原始 JSON 顯示在 Discord。
    await channel.send(file=discord.File(buffer, "chart.png"))  # 逐行註解：直接把 BytesIO 包成 discord.File 傳到原頻道。


async def send_chart_payload_to_interaction_channel(interaction: discord.Interaction, chart_payload: dict, *, status_message: discord.Message | None = None, ephemeral: bool = False) -> None:  # 逐行註解：將圖表 BytesIO 傳送到 slash 指令原頻道。
    try:  # 逐行註解：繪圖可能因資料或 matplotlib 失敗，所以要完整捕捉。
        buffer = make_chart_buffer_from_payload(chart_payload)  # 逐行註解：根據圖表資料在記憶體中產生 PNG。
    except Exception as e:  # 逐行註解：任何繪圖錯誤都不能讓原始 JSON 回到 Discord。
        print(f"圖表 PNG 產生失敗：{type(e).__name__}: {e}")  # 逐行註解：印出繪圖錯誤摘要。
        traceback.print_exc()  # 逐行註解：完整印出 traceback，方便追蹤 chart_type 分支或資料問題。
        if status_message is not None:  # 逐行註解：如果有進度訊息，就改成安全錯誤提示。
            await safe_edit_message(status_message, CHART_PARSE_FAILED_MESSAGE)  # 逐行註解：避免顯示原始 JSON。
        elif interaction.channel is not None:  # 逐行註解：有原頻道時優先送到原頻道。
            await interaction.channel.send(CHART_PARSE_FAILED_MESSAGE)  # 逐行註解：送出安全錯誤提示。
        else:  # 逐行註解：沒有原頻道時使用 followup 備援。
            await interaction.followup.send(CHART_PARSE_FAILED_MESSAGE, ephemeral=ephemeral)  # 逐行註解：送出安全錯誤提示。
        return  # 逐行註解：錯誤已處理，停止傳檔流程。
    if status_message is not None:  # 逐行註解：如果 slash 指令已有進度訊息，就先改成完成訊息。
        await safe_edit_message(status_message, chart_reply_summary(chart_payload))  # 逐行註解：避免進度訊息顯示原始 JSON。
    if interaction.channel is not None:  # 逐行註解：優先傳到使用者執行指令的原頻道。
        await interaction.channel.send(file=discord.File(buffer, "chart.png"))  # 逐行註解：把 BytesIO 圖表送到原頻道。
        return  # 逐行註解：原頻道傳送成功後結束。
    await interaction.followup.send(file=discord.File(buffer, "chart.png"), ephemeral=ephemeral)  # 逐行註解：沒有原頻道時使用 followup 備援傳送。


async def send_text_to_interaction_channel(interaction: discord.Interaction, text: str, *, ephemeral: bool = False) -> None:  # 逐行註解：把補充文字送到 slash 指令原頻道或 followup。
    for chunk in split_discord_text(text):  # 逐行註解：依 Discord 文字長度限制切段送出。
        if interaction.channel is not None:  # 逐行註解：優先傳到使用者執行指令的原頻道。
            await interaction.channel.send(chunk)  # 逐行註解：在原頻道送出補充文字。
        else:  # 逐行註解：如果沒有原頻道，就用 followup 備援。
            await interaction.followup.send(chunk, ephemeral=ephemeral)  # 逐行註解：用 slash followup 傳送補充文字。


SIMPLIFIED_TO_TRADITIONAL = str.maketrans({  # 逐行註解：開始建立一個跨多行的字典或集合資料。
    "么": "麼",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "吗": "嗎",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "为": "為",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "这": "這",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "个": "個",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "后": "後",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "里": "裡",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "会": "會",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "帮": "幫",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "说": "說",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "让": "讓",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "请": "請",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "问": "問",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "题": "題",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "应": "應",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "对": "對",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "时": "時",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "间": "間",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "现": "現",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "发": "發",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "过": "過",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "还": "還",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "没": "沒",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "给": "給",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "开": "開",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "关": "關",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "实": "實",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "种": "種",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "动": "動",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "国": "國",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "语": "語",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "汉": "漢",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "体": "體",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "简": "簡",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "繁": "繁",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "软": "軟",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "频": "頻",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "讯": "訊",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "资": "資",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "与": "與",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "内": "內",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "写": "寫",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "读": "讀",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "条": "條",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "将": "將",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "来": "來",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "优": "優",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "习": "習",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "义": "義",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "云": "雲",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "尽": "盡",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "准": "準",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "确": "確",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    "为": "為",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
})  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。


def force_common_traditional_chinese(text: str) -> str:  # 逐行註解：定義函式 force_common_traditional_chinese，把一段會重複使用的流程包起來。
    """qwen 小模型偶爾會漏簡體字；這裡把常見簡體字轉回繁體。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    return (text or "").translate(SIMPLIFIED_TO_TRADITIONAL)  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def get_conversation_memory(user_id: int, model: str) -> list[dict[str, str]]:  # 逐行註解：定義函式 get_conversation_memory，把一段會重複使用的流程包起來。
    """取出某個使用者在某個模型底下的最近對話記憶。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    return conversation_memory.get((user_id, model), [])  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def memory_role_name(role: str) -> str:
    """把內部 role 名稱轉成 prompt 裡更好懂的繁中標籤。"""
    if role == "user":
        return "使用者"
    if role == "summary":
        return "Summary memory"
    return "AI"


def format_memory_history(
    history: list[dict[str, str]],
    *,
    source_label: str,
    remaining_chars: int,
) -> tuple[str, int]:
    """把某一段 memory history 轉成文字，並回傳實際使用字數。"""
    if remaining_chars <= 0:
        return "", 0
    lines: list[str] = []
    used_chars = 0
    for item in reversed(history):
        role = memory_role_name(item.get("role") or "")
        content = (item.get("content") or "").strip()
        if not content:
            continue
        line = f"[{source_label}] {role}：{content}"
        if used_chars + len(line) > remaining_chars:
            break
        lines.append(line)
        used_chars += len(line)
    lines.reverse()
    return "\n".join(lines), used_chars


def format_conversation_memory(user_id: int, model: str) -> str:  # 逐行註解：定義函式 format_conversation_memory，把一段會重複使用的流程包起來。
    """把 summary、共享記憶和目前模型記憶整理進 prompt，讓任何 AI 回覆都可被後續讀到。"""
    sections: list[str] = []
    used_chars = 0

    memory_sources = [
        ("summary memory（整理後，優先參考）", get_conversation_memory(user_id, SUMMARY_MEMORY_MODEL)),
        ("shared memory（跨模型工具結果）", get_conversation_memory(user_id, SHARED_MEMORY_MODEL)),
    ]
    if model not in {SUMMARY_MEMORY_MODEL, SHARED_MEMORY_MODEL}:
        memory_sources.append((f"{model} chat history", get_conversation_memory(user_id, model)))

    for source_label, history in memory_sources:
        remaining_chars = CONVERSATION_MEMORY_MAX_CHARS - used_chars
        section_text, section_chars = format_memory_history(
            history,
            source_label=source_label,
            remaining_chars=remaining_chars,
        )
        if section_text:
            sections.append(section_text)
            used_chars += section_chars

    return "\n".join(sections) if sections else "無"  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def format_permanent_memory_for_prompt(user_id: int) -> str:  # 逐行註解：把目前使用者自己的永久記憶整理成可放進 Ollama prompt 的文字。
    memories = load_permanent_memories(user_id)  # 逐行註解：只讀取這位 Discord 使用者自己的 JSON 永久記憶。
    if not memories:  # 逐行註解：如果沒有任何永久記憶，就回傳無，讓 prompt 保持乾淨。
        return "無"  # 逐行註解：沒有永久記憶時回傳固定文字。
    lines: list[str] = []  # 逐行註解：建立要送給 Ollama 的永久記憶文字清單。
    used_chars = 0  # 逐行註解：累計目前已放入 prompt 的字數。
    for item in sorted(memories, key=lambda row: int(row.get("id", 0))):  # 逐行註解：依照永久記憶編號排序，讓模型看到穩定順序。
        memory_id = item.get("id")  # 逐行註解：取得這筆永久記憶的編號。
        content = str(item.get("content") or "").strip()  # 逐行註解：取得這筆永久記憶的內容並去除頭尾空白。
        created_at = str(item.get("created_at") or "未知").strip()  # 逐行註解：取得這筆永久記憶的建立時間，舊資料沒有時間時用未知。
        if not content:  # 逐行註解：如果內容是空的，就不要送進模型。
            continue  # 逐行註解：跳過空內容，繼續下一筆永久記憶。
        line = f"[{memory_id}] {content}（建立時間：{created_at}）"  # 逐行註解：把編號、內容、建立時間合成一行，方便模型引用。
        used_chars += len(line)  # 逐行註解：累加這一行的字數，用來控制 prompt 長度。
        if used_chars > PERMANENT_MEMORY_MAX_CHARS:  # 逐行註解：如果超過永久記憶上限，就停止加入更多記憶。
            break  # 逐行註解：跳出迴圈，避免 prompt 過長。
        lines.append(line)  # 逐行註解：把這筆永久記憶加入 prompt 文字清單。
    return "\n".join(lines) if lines else "無"  # 逐行註解：回傳整理後永久記憶；如果沒有可用內容就回傳無。


def build_prompt_with_memory(user_id: int, model: str, user_text: str) -> str:  # 逐行註解：定義函式 build_prompt_with_memory，把一段會重複使用的流程包起來。
    """把永久記憶與 max token 預算內的對話記憶一起交給 Ollama，讓每個模型都能接續上下文。"""  # 逐行註解：說明這裡會同時讀永久記憶與短期對話記憶。
    user_text = (user_text or "").strip()  # 逐行註解：設定 user_text 這個變數，供後面的流程使用。
    permanent_memory_context = format_permanent_memory_for_prompt(user_id)  # 逐行註解：讀取目前使用者自己的 /remember 永久記憶，讓 AI 回答時知道。
    memory_context = format_conversation_memory(user_id, model)  # 逐行註解：設定 memory_context 這個變數，供後面的流程使用。
    chart_rules = chart_output_rules_prompt()  # 逐行註解：取得圖表 JSON 規則，讓聊天需要視覺化時可觸發圖表輸出。

    return f"""
【身份判斷原則】
你是 Smart_Sean AI，不是 Discord 使用者。
永久記憶和短期對話記憶都屬於目前這位 Discord 使用者，不是你的個人資料。
中文第一人稱「我、我的、我是誰、我叫什麼」指的是 Discord 使用者本人；中文第二人稱「你、你的、你是誰、你叫什麼」指的是 AI 助理。
回答任何身份、姓名、偏好、設備或個人資料問題前，先自行判斷使用者是在問「使用者本人」還是在問「AI 助理」。
如果問題是在問使用者本人，請到永久記憶和短期對話記憶裡找可用資料，再用第二人稱回答；沒有足夠記憶時，直接說目前記憶不足。
如果問題是在問 AI 助理，請根據你的 AI 身份回答，不要引用使用者的姓名、暱稱、設備或偏好當成你的資料。
沒有明確資料來源時，不要編造你的製作者、公司、模型來源或產品背景。
不要套用固定句型；每次都根據使用者的新訊息和下方記憶內容自行整理答案。

【圖表輸出規則】
{chart_rules}

【永久記憶】
{permanent_memory_context}

【短期對話記憶】
{memory_context}

【使用者現在的新訊息】
{user_text}
""".strip()


def normalize_identity_query(text: str) -> str:
    """把身份問題整理成容易比對的字串。"""
    return re.sub(r"[\s，,。.!！?？；;：:「」『』\"'`~～（）()【】\\[\\]]+", "", (text or "").strip().lower())


def identity_question_target(user_text: str) -> str:
    """判斷身份問題是在問使用者本人還是 AI 助理；不是身份問題就回空字串。"""
    text = normalize_identity_query(user_text)
    if not text:
        return ""
    user_identity_phrases = (
        "我是誰",
        "我是谁",
        "我叫什麼",
        "我叫什么",
        "我的名字是什麼",
        "我的名字是什么",
        "我的名稱是什麼",
        "我的名稱是什么",
        "你知道我是誰",
        "你記得我是誰",
        "你還記得我是誰",
        "記得我是誰",
        "還記得我是誰",
        "whoami",
        "whatismyname",
    )
    if any(phrase in text for phrase in user_identity_phrases):
        return "user"
    ai_identity_phrases = (
        "你是誰",
        "你是谁",
        "你叫什麼",
        "你叫什么",
        "你的名字是什麼",
        "你的名字是什么",
        "你的名稱是什麼",
        "你的名稱是什么",
        "whoareyou",
        "whatisyourname",
    )
    if any(phrase in text for phrase in ai_identity_phrases):
        return "ai"
    return ""


def user_memory_lookup_requested(user_text: str) -> bool:
    """判斷使用者是不是在問 bot 目前記得哪些使用者資料。"""
    text = normalize_identity_query(user_text)
    if not text:
        return False
    if identity_question_target(user_text) == "ai":
        return False
    lookup_phrases = (
        "你還記得我嗎",
        "你記得我嗎",
        "還記得我嗎",
        "記得我嗎",
        "你認識我嗎",
        "認識我嗎",
        "你知道我嗎",
        "知道我嗎",
        "你知道我的資料嗎",
        "你有我的資料嗎",
        "你有我的記憶嗎",
        "我的記憶有什麼",
        "我的記憶有哪些",
        "你記得我的什麼",
        "你記得我什麼",
        "你對我有什麼記憶",
        "你知道哪些關於我",
        "你知道關於我的什麼",
        "你目前記得什麼",
        "你記憶裡有什麼",
        "列出我的記憶",
        "顯示我的記憶",
    )
    return any(phrase in text for phrase in lookup_phrases)


def memory_content_to_second_person(content: str) -> str:
    """把 memories JSON 裡的「使用者...」改成回答使用者時自然的第二人稱。"""
    text = (content or "").strip()
    replacements = (
        (r"^使用者名稱為", "你的名稱是"),
        (r"^使用者名字為", "你的名字是"),
        (r"^使用者叫做", "你叫做"),
        (r"^使用者叫", "你叫"),
        (r"^使用者是", "你是"),
        (r"^使用者使用", "你使用"),
    )
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    if text.startswith("使用者"):
        text = "你" + text[len("使用者"):]
    return text


def collect_user_memory_answer_items(user_id: int, *, include_short_term: bool = True) -> list[str]:
    """收集可直接回答使用者的記憶內容，永久記憶優先，必要時補短期記憶。"""
    items: list[str] = []
    seen: set[str] = set()

    for item in load_permanent_memories(user_id):
        content = str(item.get("content") or "").strip()
        normalized = normalize_memory_content(content)
        if not content or not normalized or normalized in seen:
            continue
        items.append(memory_content_to_second_person(content))
        seen.add(normalized)

    if include_short_term:
        for model in (SUMMARY_MEMORY_MODEL, SHARED_MEMORY_MODEL):
            for item in get_conversation_memory(user_id, model):
                content = str(item.get("content") or "").strip()
                normalized = normalize_memory_content(content)
                if not content or not normalized or normalized in seen:
                    continue
                items.append(memory_content_to_second_person(content))
                seen.add(normalized)
                if len(items) >= 8:
                    return items

    return items[:8]


def identity_memory_contents(user_id: int) -> list[str]:
    """從永久記憶優先找出使用者身份相關內容。"""
    identity_keywords = ("名稱", "名字", "叫做", "叫", "身份", "身分", "我是", "生日", "年齡", "設備", "mac", "電腦", "discord", "帳號")
    contents: list[str] = []
    seen: set[str] = set()
    for item in load_permanent_memories(user_id):
        content = str(item.get("content") or "").strip()
        normalized = normalize_memory_content(content)
        lowered = content.lower()
        if not content or not normalized or normalized in seen:
            continue
        if any(keyword.lower() in lowered for keyword in identity_keywords):
            contents.append(memory_content_to_second_person(content))
            seen.add(normalized)
    return contents


def build_identity_answer(user_id: int, user_text: str) -> str:
    """身份問題不交給一般聊天模型猜，避免把使用者和 AI 身份混在一起。"""
    target = identity_question_target(user_text)
    if target == "ai":
        return "我是 Smart_Sean AI。"
    if target != "user":
        return ""
    contents = identity_memory_contents(user_id)
    if not contents:
        return "我目前沒有足夠的永久記憶判斷你是誰。"
    if len(contents) == 1:
        return f"根據永久記憶，{contents[0]}"
    bullet_lines = "\n".join(f"- {content}" for content in contents[:5])
    return f"根據永久記憶，我目前知道：\n{bullet_lines}"


def build_user_memory_lookup_answer(user_id: int, user_text: str) -> str:
    """記憶查詢不交給小模型猜，直接從 memories JSON 和短期記錄回答。"""
    if not user_memory_lookup_requested(user_text):
        return ""
    items = collect_user_memory_answer_items(user_id)
    if not items:
        return "我目前沒有可用的永久記憶或短期聊天記錄。"
    bullet_lines = "\n".join(f"- {item}" for item in items)
    return f"我目前記得：\n{bullet_lines}"


def remember_conversation(user_id: int, model: str, user_text: str, assistant_text: str) -> None:  # 逐行註解：定義函式 remember_conversation，把一段會重複使用的流程包起來。
    """保存使用者訊息與 AI 回覆；一般聊天按模型分開記，web_search 可存進共享記憶。"""  # 逐行註解：說明記憶可以分模型保存，也可以保存到共享記憶給所有模型使用。
    user_text = (user_text or "").strip()  # 逐行註解：設定 user_text 這個變數，供後面的流程使用。
    assistant_text = (assistant_text or "").strip()  # 逐行註解：設定 assistant_text 這個變數，供後面的流程使用。
    if not user_text and not assistant_text:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    key = (user_id, model)  # 逐行註解：設定 key 這個變數，供後面的流程使用。
    history = conversation_memory.setdefault(key, [])  # 逐行註解：設定 history 這個變數，供後面的流程使用。
    entry_max_chars = SUMMARY_MEMORY_ENTRY_MAX_CHARS if model == SUMMARY_MEMORY_MODEL else CONVERSATION_MEMORY_ENTRY_MAX_CHARS
    if user_text:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        history.append({"role": "user", "content": user_text[:entry_max_chars]})  # 逐行註解：保存使用者訊息，但最多保留設定好的單筆字數，避免記憶爆太大。
    if assistant_text:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        role = "summary" if model == SUMMARY_MEMORY_MODEL else "assistant"
        history.append({"role": role, "content": assistant_text[:entry_max_chars]})  # 逐行註解：保存 AI 回覆，web_search 長回答也能保留更多內容。


def iter_user_memory_records(user_id: int) -> list[tuple[str, str, str]]:
    """列出指定使用者目前保留的所有短期、共享、summary 和永久記憶。"""
    records: list[tuple[str, str, str]] = []
    for (stored_user_id, model), history in conversation_memory.items():
        if stored_user_id != user_id:
            continue
        for item in history:
            content = (item.get("content") or "").strip()
            if content:
                records.append((model, item.get("role") or "assistant", content))
    for item in load_permanent_memories(user_id):
        content = str(item.get("content") or "").strip()
        if content:
            records.append(("permanent memory", "summary", content))
    return records


def count_user_memory_records(user_id: int) -> int:
    """計算指定使用者有多少筆聊天記錄可整理。"""
    return len(iter_user_memory_records(user_id))


def format_user_memory_for_summary(user_id: int) -> str:
    """把全部聊天記錄整理成 gemma4_thinking 用來產生 summary memory 的輸入。"""
    records = iter_user_memory_records(user_id)
    if not records:
        return ""

    summary_records = [record for record in records if record[0] == SUMMARY_MEMORY_MODEL]
    permanent_records = [record for record in records if record[0] == "permanent memory"]
    raw_records = [record for record in records if record[0] not in {SUMMARY_MEMORY_MODEL, "permanent memory"}]
    ordered_records = summary_records + permanent_records + list(reversed(raw_records))

    lines: list[str] = []
    used_chars = 0
    for model, role, content in ordered_records:
        line = f"[{model}] {memory_role_name(role)}：{content}"
        if used_chars + len(line) > SUMMARY_MEMORY_SOURCE_MAX_CHARS:
            break
        lines.append(line)
        used_chars += len(line)
    return "\n".join(lines)


def build_summary_memory_prompt(memory_context: str) -> str:
    """建立 summary memory 專用 prompt；呼叫端固定用 gemma4_thinking。"""
    return f"""
你是 Discord bot 的 summary memory 整理器。
你必須把聊天記錄整理成可以寫回 memories/<user_id>.json 的永久記憶項目。

規則：
1. 使用繁體中文。
2. 每一筆 content 都要是完整、清楚、單句或短句的使用者記憶，讓小模型不用推理太多也能理解。
3. 重複、相似或互相包含的內容要自動合併，不要逐字堆疊。
4. 如果新內容修正舊內容，以新內容為準，直接改寫成最新版本。
5. 刪掉寒暄、無後續價值的中間過程、重複失敗訊息和不重要細節。
6. content 要使用原本 memories JSON 的記憶寫法，優先以「使用者...」開頭，不要寫成「Summary memory:」或分類標題。
7. 不要把 AI 身份、AI 規則或 Smart_Sean AI 寫成使用者資料。
8. 最多輸出 12 筆，每筆 content 盡量 120 字以內。
9. 只能輸出 JSON，不要輸出 Markdown、thinking process、整理理由、前言或結語。

輸出格式：
{{"memories":[{{"content":"使用者..."}}]}}

聊天記錄：
{memory_context}
""".strip()


def normalize_summary_memory_content(content: str) -> str:
    """把 summary model 產生的內容整理成單筆 memories JSON content。"""
    cleaned = clean_memory_request_content(content, MEMORY_SUGGESTION_MAX_CHARS)
    cleaned = re.sub(r"^(?:content|記憶|memory)\s*[:：]\s*", "", cleaned, flags=re.I).strip()
    cleaned = re.sub(r"^(?:使用者偏好|目前任務|重要上下文|工具或搜尋結果|注意事項)\s*[:：]\s*", "使用者", cleaned).strip()
    if not cleaned:
        return ""
    if cleaned.lower() in {"summary memory", "memories"}:
        return ""
    if not cleaned.startswith("使用者"):
        cleaned = f"使用者{cleaned}"
    return cleaned[:MEMORY_SUGGESTION_MAX_CHARS].rstrip()


def parse_summary_memory_items(raw_text: str) -> list[str]:
    """解析 gemma4_thinking 輸出的 summary memory，回傳可寫入 memories JSON 的 content 清單。"""
    text = (raw_text or "").strip()
    if not text:
        return []
    cleaned = re.sub(r"(?is)^```(?:json)?\s*|\s*```$", "", text).strip()
    parsed_data = None
    for candidate in (cleaned, extract_first_json_object_text(cleaned)):
        if not candidate:
            continue
        try:
            parsed_data = json.loads(candidate)
            break
        except Exception:
            continue
    if parsed_data is None:
        array_match = re.search(r"\[.*\]", cleaned, flags=re.S)
        if array_match:
            try:
                parsed_data = json.loads(array_match.group(0))
            except Exception:
                parsed_data = None

    raw_items: list[str] = []
    if isinstance(parsed_data, dict):
        memories = parsed_data.get("memories") or parsed_data.get("memory") or parsed_data.get("items") or []
        if isinstance(memories, list):
            for item in memories:
                if isinstance(item, dict):
                    raw_items.append(str(item.get("content") or "").strip())
                elif isinstance(item, str):
                    raw_items.append(item.strip())
    elif isinstance(parsed_data, list):
        for item in parsed_data:
            if isinstance(item, dict):
                raw_items.append(str(item.get("content") or "").strip())
            elif isinstance(item, str):
                raw_items.append(item.strip())

    if not raw_items:
        for line in cleaned.splitlines():
            line = line.strip()
            line = re.sub(r"^[-*•]\s*", "", line)
            line = re.sub(r"^\d+[.)、]\s*", "", line)
            if not line or line.lower().startswith(("summary memory", "```")):
                continue
            raw_items.append(line)

    contents: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        content = normalize_summary_memory_content(item)
        normalized = normalize_memory_content(content)
        if not content or not normalized or normalized in seen:
            continue
        contents.append(content)
        seen.add(normalized)
        if len(contents) >= 12:
            break
    return contents


def replace_permanent_memories_with_summary(user_id: int, contents: list[str]) -> list[dict]:
    """用 summary_memory 整理後的內容覆蓋永久記憶，格式維持 memories JSON。"""
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items = [build_memory_json_item(index + 1, content, created_at) for index, content in enumerate(contents)]
    save_permanent_memories(user_id, items)
    upsert_summary_memory(user_id, format_memory_json_items(items))
    return items


def upsert_summary_memory(user_id: int, summary_text: str) -> None:
    """只更新 summary memory，不刪 raw chat history。"""
    summary_text = (summary_text or "").strip()
    if not summary_text:
        return
    conversation_memory[(user_id, SUMMARY_MEMORY_MODEL)] = [
        {"role": "summary", "content": summary_text[:SUMMARY_MEMORY_ENTRY_MAX_CHARS]}
    ]


def clear_user_conversation_memory(user_id: int) -> int:
    """清空指定使用者的聊天記錄，回傳刪掉的記錄區數量。"""
    keys_to_delete = [key for key in conversation_memory if key[0] == user_id]
    for key in keys_to_delete:
        del conversation_memory[key]
    return len(keys_to_delete)


class DuckDuckGoResultParser(HTMLParser):  # 逐行註解：定義類別 DuckDuckGoResultParser，用來描述一種資料或 Discord UI 元件。
    """
    專門解析 DuckDuckGo HTML 搜尋結果的 parser。
    這裡不用 BeautifulSoup，是為了讓專案不需要額外安裝套件。
    """
    def __init__(self):  # 逐行註解：定義函式 __init__，把一段會重複使用的流程包起來。
        super().__init__()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        self.results: list[dict[str, str]] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        self._in_title = False  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        self._in_snippet = False  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        self._title_parts: list[str] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        self._snippet_parts: list[str] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        self._current_href = ""  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。

    def handle_starttag(self, tag, attrs):  # 逐行註解：定義函式 handle_starttag，把一段會重複使用的流程包起來。
        attr = dict(attrs)  # 逐行註解：設定 attr 這個變數，供後面的流程使用。
        classes = set((attr.get("class") or "").split())  # 逐行註解：設定 classes 這個變數，供後面的流程使用。
        # DuckDuckGo 的結果標題會放在 class="result__a" 或 "result-link" 的 <a> 裡。
        if tag == "a" and ("result__a" in classes or "result-link" in classes):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            self._in_title = True  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            self._title_parts = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            self._current_href = attr.get("href") or ""  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        # 搜尋摘要會放在 result__snippet 或 result-snippet，之後會接到最後一筆結果上。
        elif "result__snippet" in classes or "result-snippet" in classes:  # 逐行註解：前面的 if 不成立時，改檢查這個額外條件。
            self._in_snippet = True  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            self._snippet_parts = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。

    def handle_data(self, data):  # 逐行註解：定義函式 handle_data，把一段會重複使用的流程包起來。
        if self._in_title:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            self._title_parts.append(data)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        elif self._in_snippet:  # 逐行註解：前面的 if 不成立時，改檢查這個額外條件。
            self._snippet_parts.append(data)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    def handle_endtag(self, tag):  # 逐行註解：定義函式 handle_endtag，把一段會重複使用的流程包起來。
        if tag == "a" and self._in_title:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            title = " ".join("".join(self._title_parts).split())  # 逐行註解：設定 title 這個變數，供後面的流程使用。
            url = normalize_duckduckgo_url(self._current_href)  # 逐行註解：設定 url 這個變數，供後面的流程使用。
            if title and url:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                self.results.append({"title": title, "url": url, "snippet": ""})  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            self._in_title = False  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        elif self._in_snippet:  # 逐行註解：前面的 if 不成立時，改檢查這個額外條件。
            snippet = " ".join("".join(self._snippet_parts).split())  # 逐行註解：設定 snippet 這個變數，供後面的流程使用。
            if snippet and self.results:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                self.results[-1]["snippet"] = snippet  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            self._in_snippet = False  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。


class WebPageTextParser(HTMLParser):  # 逐行註解：定義類別 WebPageTextParser，用來描述一種資料或 Discord UI 元件。
    """把一般網頁 HTML 轉成純文字，給 Ollama 當成真正讀到的頁面內容。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    def __init__(self):  # 逐行註解：定義函式 __init__，把一段會重複使用的流程包起來。
        super().__init__()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        self.parts: list[str] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        self._skip_depth = 0  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。

    def handle_starttag(self, tag, attrs):  # 逐行註解：定義函式 handle_starttag，把一段會重複使用的流程包起來。
        if tag in {"script", "style", "noscript", "svg"}:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            self._skip_depth += 1  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    def handle_endtag(self, tag):  # 逐行註解：定義函式 handle_endtag，把一段會重複使用的流程包起來。
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth > 0:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            self._skip_depth -= 1  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    def handle_data(self, data):  # 逐行註解：定義函式 handle_data，把一段會重複使用的流程包起來。
        if self._skip_depth:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
        cleaned = " ".join((data or "").split())  # 逐行註解：設定 cleaned 這個變數，供後面的流程使用。
        if cleaned:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            self.parts.append(cleaned)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    def text(self, *, max_chars: int = 1800) -> str:  # 逐行註解：定義函式 text，把一段會重複使用的流程包起來。
        return " ".join(self.parts)[:max_chars].strip()  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def normalize_duckduckgo_url(raw_url: str) -> str:  # 逐行註解：定義函式 normalize_duckduckgo_url，把一段會重複使用的流程包起來。
    """
    DuckDuckGo 結果常常不是直接網址，而是 /l/?uddg=真正網址。
    這個函式把它還原成後台容易讀的原始網址。
    """
    raw_url = (raw_url or "").strip()  # 逐行註解：設定 raw_url 這個變數，供後面的流程使用。
    if raw_url.startswith("//"):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        raw_url = "https:" + raw_url  # 逐行註解：設定 raw_url 這個變數，供後面的流程使用。
    parsed = urlparse.urlparse(raw_url)  # 逐行註解：設定 parsed 這個變數，供後面的流程使用。
    qs = urlparse.parse_qs(parsed.query)  # 逐行註解：設定 qs 這個變數，供後面的流程使用。
    if "uddg" in qs and qs["uddg"]:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return qs["uddg"][0]  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    return raw_url  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def format_search_results_for_log(results: list[dict[str, str]]) -> str:  # 逐行註解：定義函式 format_search_results_for_log，把一段會重複使用的流程包起來。
    """把搜尋結果整理成後台看的格式：標題、網址、摘要。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if not results:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return "無"  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    return "\n".join(  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
        f"[{i}] 標題：{r['title']}\n網址：{r['url']}\n摘要：{r.get('snippet') or '（沒有摘要）'}"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        for i, r in enumerate(results, start=1)  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。


def format_search_urls_for_log(results: list[dict[str, str]]) -> str:  # 逐行註解：定義函式 format_search_urls_for_log，把一段會重複使用的流程包起來。
    """只列出 Ollama 參考到的網址，方便在後台快速檢查來源。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if not results:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return "無"  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    return "\n".join(f"[{i}] {r['url']}" for i, r in enumerate(results, start=1))  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def format_page_reads_for_log(pages: list[dict[str, str]]) -> str:  # 逐行註解：定義函式 format_page_reads_for_log，把一段會重複使用的流程包起來。
    if not pages:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return "無"  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    return "\n\n".join(  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
        f"[{i}] 搜尋順位：{p.get('search_index') or '？'}\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        f"標題：{p.get('title') or '（沒有標題）'}\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        f"網址：{p['url']}\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        f"挑選理由：{p.get('fetch_reason') or '依搜尋結果順序'}\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        f"狀態：{p['status']}\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        f"內容：{p.get('text') or '（沒有讀到可用文字）'}"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        for i, p in enumerate(pages, start=1)  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。


def _domain_from_url(url: str) -> str:  # 逐行註解：定義函式 _domain_from_url，把一段會重複使用的流程包起來。
    parsed = urlparse.urlparse(url or "")  # 逐行註解：設定 parsed 這個變數，供後面的流程使用。
    return (parsed.netloc or "").lower().removeprefix("www.")  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def _search_terms(text: str) -> set[str]:  # 逐行註解：定義函式 _search_terms，把一段會重複使用的流程包起來。
    text = (text or "").lower()  # 逐行註解：設定 text 這個變數，供後面的流程使用。
    terms = set(re.findall(r"[a-z0-9][a-z0-9_-]{1,}", text))  # 逐行註解：設定 terms 這個變數，供後面的流程使用。
    chinese = re.sub(r"[^\u4e00-\u9fff]+", "", text)  # 逐行註解：設定 chinese 這個變數，供後面的流程使用。
    for size in (2, 3, 4):  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        for i in range(0, max(0, len(chinese) - size + 1)):  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
            terms.add(chinese[i:i + size])  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    return {term for term in terms if term}  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

def _looks_like_weather_question(question: str) -> bool:  # 逐行註解：定義函式 _looks_like_weather_question，把一段會重複使用的流程包起來。
    q = (question or "").lower()  # 逐行註解：設定 q 這個變數，供後面的流程使用。
    return any(word in q for word in ("天氣", "氣溫", "下雨", "降雨", "weather", "forecast", "temperature"))  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def score_search_result_for_fetch(question: str, result: dict[str, str]) -> tuple[int, str]:  # 逐行註解：定義函式 score_search_result_for_fetch，把一段會重複使用的流程包起來。
    """
    先根據標題、摘要、網址判斷哪個連結最值得打開。
    分數只用來排序，真正回答仍然要看 fetch 回來的頁面內容。
    """
    title = result.get("title") or ""  # 逐行註解：設定 title 這個變數，供後面的流程使用。
    snippet = result.get("snippet") or ""  # 逐行註解：設定 snippet 這個變數，供後面的流程使用。
    url = result.get("url") or ""  # 逐行註解：設定 url 這個變數，供後面的流程使用。
    domain = _domain_from_url(url)  # 逐行註解：設定 domain 這個變數，供後面的流程使用。
    title_l = title.lower()  # 逐行註解：設定 title_l 這個變數，供後面的流程使用。
    haystack = f"{title} {snippet} {domain} {url}".lower()  # 逐行註解：設定 haystack 這個變數，供後面的流程使用。

    score = 0  # 逐行註解：設定 score 這個變數，供後面的流程使用。
    reasons: list[str] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。

    for term in _search_terms(question):  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        if term in title_l:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            score += 6  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            reasons.append(f"標題符合「{term}」")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        elif term in haystack:  # 逐行註解：前面的 if 不成立時，改檢查這個額外條件。
            score += 2  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    if _looks_like_weather_question(question):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        weather_words = ("天氣", "氣溫", "降雨", "預報", "weather", "forecast", "temperature")  # 逐行註解：設定 weather_words 這個變數，供後面的流程使用。
        if any(word in haystack for word in weather_words):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            score += 20  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            reasons.append("看起來是天氣資料頁")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        if any(domain.endswith(d) for d in ("cwa.gov.tw", "weather.com", "accuweather.com", "weather.yahoo.com", "timeanddate.com")):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            score += 18  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            reasons.append("來源像天氣網站")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    if any(bad in domain for bad in ("youtube.com", "facebook.com", "instagram.com", "x.com", "twitter.com", "tiktok.com")):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        score -= 12  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        reasons.append("社群/影音頁較不適合讀文字")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    if not reasons:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        reasons.append("依標題摘要與問題關聯度")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    return score, "、".join(reasons[:3])  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def select_results_for_fetch(question: str, results: list[dict[str, str]], *, limit: int = 5) -> list[dict[str, str]]:  # 逐行註解：定義函式 select_results_for_fetch，把一段會重複使用的流程包起來。
    ranked: list[tuple[int, int, dict[str, str]]] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    for index, result in enumerate(results, start=1):  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        score, reason = score_search_result_for_fetch(question, result)  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        ranked.append((  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
            score,  # 逐行註解：這行是跨行資料或參數的一個項目。
            index,  # 逐行註解：這行是跨行資料或參數的一個項目。
            {  # 逐行註解：開始建立一個跨多行的字典或集合資料。
                **result,  # 逐行註解：這行是跨行資料或參數的一個項目。
                "search_index": str(index),  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                "fetch_score": str(score),  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                "fetch_reason": reason,  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            },  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        ))  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    ranked.sort(key=lambda item: (-item[0], item[1]))  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    return [item for _, _, item in ranked[:limit]]  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def format_fetch_plan_for_log(results: list[dict[str, str]]) -> str:  # 逐行註解：定義函式 format_fetch_plan_for_log，把一段會重複使用的流程包起來。
    if not results:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return "無"  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    return "\n".join(  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
        f"[{i}] 原搜尋順位：{r.get('search_index') or '？'}｜分數：{r.get('fetch_score') or '0'}\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        f"標題：{r.get('title') or '（沒有標題）'}\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        f"網址：{r.get('url') or '（沒有網址）'}\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        f"挑選理由：{r.get('fetch_reason') or '依搜尋結果順序'}"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        for i, r in enumerate(results, start=1)  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。


async def search_web_results(question: str, *, limit: int = 5) -> list[dict[str, str]]:  # 逐行註解：定義非同步函式 search_web_results，可以搭配 await 處理 Discord 或網路等待。
    """
    /web_search 會呼叫這裡：
    1. 把使用者問題送到 DuckDuckGo HTML 搜尋。
    2. 解析出前幾筆搜尋結果。
    3. 回傳給 Ollama 當作回答依據。
    """
    question = (question or "").strip()  # 逐行註解：設定 question 這個變數，供後面的流程使用。
    if not question:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return []  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    def _search() -> list[dict[str, str]]:  # 逐行註解：定義函式 _search，把一段會重複使用的流程包起來。
        url = "https://html.duckduckgo.com/html/?q=" + urlparse.quote(question)  # 逐行註解：設定 url 這個變數，供後面的流程使用。
        req = urlrequest.Request(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
            url,  # 逐行註解：這行是跨行資料或參數的一個項目。
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},  # 逐行註解：使用更現代的 User-Agent 避免被擋。
            method="GET",  # 逐行註解：設定 method 這個變數，供後面的流程使用。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        with urlrequest.urlopen(req, timeout=15) as resp:  # 逐行註解：開啟需要自動收尾的資源，例如網路回應或檔案。
            html = resp.read().decode("utf-8", errors="replace")  # 逐行註解：讀取 HTML 內容。
            if "result__a" not in html and "result-link" not in html:  # 逐行註解：如果找不到任何搜尋結果的關鍵 class。
                print(f"DEBUG: DuckDuckGo HTML 內容可能已變更或被擋。HTML 長度：{len(html)}")  # 逐行註解：印出除錯資訊。
        parser = DuckDuckGoResultParser()  # 逐行註解：設定 parser 這個變數，供後面的流程使用。
        parser.feed(html)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        return parser.results[:limit]  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    # urllib 是同步阻塞工具，放到 thread 裡跑，才不會卡住 Discord bot。
    return await asyncio.to_thread(_search)  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


async def fetch_web_pages(  # 逐行註解：定義非同步函式 fetch_web_pages，可以搭配 await 處理 Discord 或網路等待。
    results: list[dict[str, str]],  # 逐行註解：這行是跨行資料或參數的一個項目。
    *,  # 逐行註解：這行是跨行資料或參數的一個項目。
    question: str = "",  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    limit: int = 5,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    min_attempts: int = 3,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    min_successful: int = 1,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
) -> list[dict[str, str]]:  # 逐行註解：這行開啟一個程式區塊，下面縮排內容會一起執行。
    """實際打開挑過的搜尋結果網址；如果前幾個讀不到，繼續試到至少一個成功。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    selected = results[:limit]  # 逐行註解：設定 selected 這個變數，供後面的流程使用。

    def _fetch_one(item: dict[str, str]) -> dict[str, str]:  # 逐行註解：定義函式 _fetch_one，把一段會重複使用的流程包起來。
        url = item["url"]  # 逐行註解：設定 url 這個變數，供後面的流程使用。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            # 先取得網頁 HTML 內容，尋找資料下載連結。
            html = dataset_utils.fetch_html(url)  # 逐行註解：取得該網址的 HTML 內容。
            data_links = dataset_utils.extract_data_links(html, url) if html else []  # 逐行註解：從 HTML 中找出可能的資料檔下載連結。
            
            if data_links:  # 逐行註解：如果網頁中包含資料檔連結。
                print(f"DEBUG: 找到 {len(data_links)} 個資料連結於 {url}")  # 逐行註解：後台輸出日誌。
                # 嘗試前 5 個連結。
                for i, link_info in enumerate(data_links[:dataset_utils.MAX_DATA_LINKS_TO_TRY]):  # 逐行註解：限制嘗試次數。
                    d_url = link_info["url"]  # 逐行註解：取得下載網址。
                    f_type = link_info["type"]  # 逐行註解：取得檔案類型（csv, json, xlsx 等）。
                    print(f"DEBUG: 嘗試下載第 {i+1} 個資料檔：{d_url} (類型: {f_type})")  # 逐行註解：輸出日誌。
                    
                    data_bytes, status = dataset_utils.download_data_safely(d_url)  # 逐行註解：安全下載檔案位元組。
                    if not data_bytes:  # 逐行註解：如果下載失敗。
                        print(f"DEBUG: 下載失敗：{status}")  # 逐行註解：輸出日誌。
                        # 將失敗資訊帶回，讓 AI 能告知使用者。
                        return {**item, "status": f"下載資料檔失敗 ({f_type.upper()})", "text": f"找到資料檔連結但下載失敗。\n網址：{d_url}\n原因：{status}", "auto_charts": []}
                    
                    df = dataset_utils.read_table_safely(data_bytes, f_type)  # 逐行註解：從記憶體讀取表格。
                    if df is not None and not df.empty:  # 逐行註解：如果成功讀取且有資料。
                        print(f"DEBUG: 成功讀取表格，形狀：{df.shape}，欄位：{df.columns.tolist()}")  # 逐行註解：輸出日誌。
                        info = dataset_utils.infer_columns(df, question)  # 逐行註解：動態推論欄位意義。
                        
                        # 核心邏輯：自動偵測是否可產生特定圖表。
                        auto_payloads = []  # 逐行註解：準備存放自動產生的圖表。
                        if any(info.get(k) for k in ["young", "total"]):  # 逐行註解：如果像是人口相關資料。
                            auto_payloads = dataset_utils.process_population_charts(df, info)  # 逐行註解：處理人口圓餅圖與折線圖。
                        
                        summary = dataset_utils.summarize_generic_data(df, info)  # 逐行註解：產生資料摘要供 AI 文字說明。
                        
                        # 清理大型物件參考。
                        del df  # 逐行註解：釋放 DataFrame 記憶體。
                        
                        return {  # 逐行註解：回傳包含資料摘要與自動圖表的結果。
                            **item, 
                            "status": f"已成功解析 {f_type.upper()} ({d_url})", 
                            "text": summary,
                            "auto_charts": auto_payloads  # 逐行註解：將產生的圖表 payload 帶回。
                        }
                    # 釋放位元組緩衝區。
                    del data_bytes  # 逐行註解：釋放下載資料。

            # 若非資料集頁面，則走一般網頁文字讀取流程。
            req = urlrequest.Request(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
                url,  # 逐行註解：這行是跨行資料或參數的一個項目。
                headers={"User-Agent": "Mozilla/5.0"},  # 逐行註解：設定 headers 這個變數，供後面的流程使用。
                method="GET",  # 逐行註解：設定 method 這個變數，供後面的流程使用。
            )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            with urlrequest.urlopen(req, timeout=12) as resp:  # 逐行註解：開啟需要自動收尾的資源，例如網路回應或檔案。
                content_type = resp.headers.get("Content-Type", "")  # 逐行註解：設定 content_type 這個變數，供後面的流程使用。
                raw = resp.read(350_000)  # 逐行註解：設定 raw 這個變數，供後面的流程使用。
            if "html" not in content_type.lower() and "text" not in content_type.lower():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                return {**item, "status": f"略過：不是文字網頁 ({content_type})", "text": ""}  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
            parser = WebPageTextParser()  # 逐行註解：設定 parser 這個變數，供後面的流程使用。
            parser.feed(raw.decode("utf-8", errors="replace"))  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            text = parser.text()  # 逐行註解：設定 text 這個變數，供後面的流程使用。
            if not text:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                return {**item, "status": "已打開，但沒有讀到可用文字", "text": ""}  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
            return {**item, "status": "已讀取", "text": text}  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
        except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
            return {**item, "status": f"讀取失敗：{type(e).__name__}: {str(e)[:160]}", "text": ""}  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    first_batch_count = min(len(selected), max(1, min_attempts))  # 逐行註解：設定 first_batch_count 這個變數，供後面的流程使用。
    pages = await asyncio.gather(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
        *(asyncio.to_thread(_fetch_one, item) for item in selected[:first_batch_count])  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。

    successful = sum(1 for page in pages if (page.get("text") or "").strip())  # 逐行註解：設定 successful 這個變數，供後面的流程使用。
    for item in selected[first_batch_count:]:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        if successful >= min_successful:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            break  # 逐行註解：提前跳出目前這個迴圈。
        page = await asyncio.to_thread(_fetch_one, item)  # 逐行註解：設定 page 這個變數，供後面的流程使用。
        pages.append(page)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        if (page.get("text") or "").strip():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            successful += 1  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    return pages  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def has_successful_page_read(pages: list[dict[str, str]]) -> bool:  # 逐行註解：定義函式 has_successful_page_read，把一段會重複使用的流程包起來。
    return any((page.get("text") or "").strip() for page in pages)  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def format_web_search_source_links(  # 逐行註解：定義函式 format_web_search_source_links，把一段會重複使用的流程包起來。
    page_reads: list[dict[str, str]],  # 逐行註解：這行是跨行資料或參數的一個項目。
    fallback_results: list[dict[str, str]],  # 逐行註解：這行是跨行資料或參數的一個項目。
    *,  # 逐行註解：這行是跨行資料或參數的一個項目。
    limit: int = 5,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
) -> str:  # 逐行註解：這行開啟一個程式區塊，下面縮排內容會一起執行。
    """固定產生 Discord 最後要顯示的來源連結，不只靠模型自己列來源。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    sources: list[dict[str, str]] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    seen_urls: set[str] = set()  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。

    def add_source(item: dict[str, str]) -> None:  # 逐行註解：定義函式 add_source，把一段會重複使用的流程包起來。
        # 用 seen_urls 去重，避免同一個網址同時出現在「已讀取頁面」和「搜尋結果」。
        url = (item.get("url") or "").strip()  # 逐行註解：設定 url 這個變數，供後面的流程使用。
        if not url or url in seen_urls or len(sources) >= limit:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
        seen_urls.add(url)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        sources.append(item)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    # 優先列出真的讀到文字的頁面；如果都讀不到，也要列出嘗試過的連結。
    for page in page_reads:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        if (page.get("text") or "").strip():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            add_source(page)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    for page in page_reads:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        add_source(page)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    for result in fallback_results:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        add_source(result)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    if not sources:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return ""  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    # 這一段是使用者最後一定會看到的來源區塊，避免模型忘記附連結。
    lines = ["來源連結："]  # 逐行註解：設定 lines 這個變數，供後面的流程使用。
    for index, source in enumerate(sources, start=1):  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        title = " ".join((source.get("title") or "未命名來源").split())[:120]  # 逐行註解：設定 title 這個變數，供後面的流程使用。
        status = source.get("status") or ("已讀取" if source.get("text") else "搜尋結果")  # 逐行註解：設定 status 這個變數，供後面的流程使用。
        lines.append(f"[{index}] {title}（{status}）\n{source['url']}")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    return "\n".join(lines)  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def append_source_links_to_reply(reply: str, source_links: str) -> str:  # 逐行註解：定義函式 append_source_links_to_reply，把一段會重複使用的流程包起來。
    reply = (reply or "").strip()  # 逐行註解：設定 reply 這個變數，供後面的流程使用。
    source_links = (source_links or "").strip()  # 逐行註解：設定 source_links 這個變數，供後面的流程使用。
    if not source_links:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return reply  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    if not reply:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return source_links  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    # 把程式保證產生的來源連結接到模型回答後面。
    return f"{reply}\n\n{source_links}"  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


async def ask_ollama_text(  # 逐行註解：定義非同步函式 ask_ollama_text，可以搭配 await 處理 Discord 或網路等待。
    model: str,  # 逐行註解：這行是跨行資料或參數的一個項目。
    prompt: str,  # 逐行註解：這行是跨行資料或參數的一個項目。
    *,  # 逐行註解：這行是跨行資料或參數的一個項目。
    timeout_s: int | None = None,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    include_thinking: bool = False,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
) -> str | tuple[str, str]:  # 逐行註解：這行開啟一個程式區塊，下面縮排內容會一起執行。
    """
    用本機 Ollama 文字模型回覆（CLI: `ollama run <model> ...`）。
    會自動移除 thinking process。
    """
    prompt = (prompt or "").strip()  # 逐行註解：設定 prompt 這個變數，供後面的流程使用。
    if not prompt:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return ("", "") if include_thinking else ""  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    # 用 subprocess 跑 `ollama run`，不用另外安裝 Ollama Python 套件。
    proc = await asyncio.create_subprocess_exec(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
        "ollama",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        "run",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        *ollama_cli_thinking_flags(model),  # 逐行註解：這行是跨行資料或參數的一個項目。
        model,  # 逐行註解：這行是跨行資料或參數的一個項目。
        prompt,  # 逐行註解：這行是跨行資料或參數的一個項目。
        stdout=asyncio.subprocess.PIPE,  # 逐行註解：設定 stdout 這個變數，供後面的流程使用。
        stderr=asyncio.subprocess.PIPE,  # 逐行註解：設定 stderr 這個變數，供後面的流程使用。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。

    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
        if timeout_s is None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            stdout, stderr = await proc.communicate()  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    except TimeoutError:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
        proc.kill()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        reply = "（Ollama 回覆逾時，稍後再試）"  # 逐行註解：設定 reply 這個變數，供後面的流程使用。
        return (reply, "") if include_thinking else reply  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    except asyncio.CancelledError:  # 逐行註解：/stop 取消等待時會走到這裡，必須同步停止 Ollama subprocess。
        if proc.returncode is None:  # 逐行註解：只有 subprocess 還活著時才需要 kill。
            proc.kill()  # 逐行註解：終止正在執行的 ollama run，避免背景繼續占用模型。
            try:  # 逐行註解：等待 subprocess 真正收掉，避免留下殭屍程序。
                await asyncio.wait_for(proc.wait(), timeout=3)  # 逐行註解：最多等 3 秒讓作業系統回收程序。
            except Exception as stop_error:  # 逐行註解：如果等待程序結束失敗，要印出原因但仍維持取消流程。
                print(f"Ollama subprocess 停止失敗：{type(stop_error).__name__}: {stop_error}")  # 逐行註解：後台記錄 stop 失敗原因。
        raise  # 逐行註解：把取消訊號往外傳，讓呼叫端停止 Thinking 動畫並結束回覆流程。

    if proc.returncode != 0:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        err = (stderr or b"").decode("utf-8", errors="replace").strip()  # 逐行註解：設定 err 這個變數，供後面的流程使用。
        reply = f"（Ollama 執行失敗：{err[:400]}）"  # 逐行註解：設定 reply 這個變數，供後面的流程使用。
        return (reply, "") if include_thinking else reply  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    reply = (stdout or b"").decode("utf-8", errors="replace").strip()  # 逐行註解：設定 reply 這個變數，供後面的流程使用。
    thinking_process, reply = split_thinking_process(reply)  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    if model == DEFAULT_CHAT_MODEL:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        reply = force_common_traditional_chinese(reply)  # 逐行註解：設定 reply 這個變數，供後面的流程使用。
    if include_thinking:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return reply, thinking_process  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    return reply  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


async def ask_ollama_vision(  # 逐行註解：定義非同步函式 ask_ollama_vision，可以搭配 await 處理 Discord 或網路等待。
    model: str,  # 逐行註解：這行是跨行資料或參數的一個項目。
    prompt: str,  # 逐行註解：這行是跨行資料或參數的一個項目。
    image_bytes: bytes,  # 逐行註解：這行是跨行資料或參數的一個項目。
    *,  # 逐行註解：這行是跨行資料或參數的一個項目。
    timeout_s: int | None = None,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    include_thinking: bool = False,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
) -> str | tuple[str, str]:  # 逐行註解：這行開啟一個程式區塊，下面縮排內容會一起執行。
    """
    用 Ollama HTTP API 走 vision（文字 + 圖片）推論。
    會自動移除 thinking process。
    """
    prompt = (prompt or "").strip() or "請分析這張圖片。"  # 逐行註解：設定 prompt 這個變數，供後面的流程使用。
    if not image_bytes:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        raise ValueError("empty image bytes")  # 逐行註解：主動丟出錯誤，提醒設定或流程有問題。

    # Ollama vision API 要把圖片轉成 base64 字串後放進 images。
    payload = {  # 逐行註解：開始建立一個跨多行的字典或集合資料。
        "model": model,  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        "prompt": prompt,  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        "stream": False,  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        "images": [base64.b64encode(image_bytes).decode("utf-8")],  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    }  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
    think_value = ollama_api_think_value(model)  # 逐行註解：設定 think_value 這個變數，供後面的流程使用。
    if think_value is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        payload["think"] = think_value  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    req = urlrequest.Request(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
        "http://127.0.0.1:11434/api/generate",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        data=json.dumps(payload).encode("utf-8"),  # 逐行註解：設定 data 這個變數，供後面的流程使用。
        headers={"Content-Type": "application/json"},  # 逐行註解：設定 headers 這個變數，供後面的流程使用。
        method="POST",  # 逐行註解：設定 method 這個變數，供後面的流程使用。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。

    def _do_request() -> dict:  # 逐行註解：定義函式 _do_request，把一段會重複使用的流程包起來。
        with urlrequest.urlopen(req, timeout=(timeout_s or 0) or None) as resp:  # 逐行註解：開啟需要自動收尾的資源，例如網路回應或檔案。
            raw = resp.read()  # 逐行註解：設定 raw 這個變數，供後面的流程使用。
        return json.loads(raw.decode("utf-8", errors="replace"))  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
        data = await asyncio.to_thread(_do_request)  # 逐行註解：設定 data 這個變數，供後面的流程使用。
    except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
        raise RuntimeError(f"ollama vision error: {type(e).__name__}: {e}") from e  # 逐行註解：主動丟出錯誤，提醒設定或流程有問題。

    if not isinstance(data, dict):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        raise RuntimeError("invalid response from ollama")  # 逐行註解：主動丟出錯誤，提醒設定或流程有問題。
    reply = (data.get("response") or "").strip()  # 逐行註解：設定 reply 這個變數，供後面的流程使用。
    thinking_process, reply = split_thinking_process(reply)  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    if include_thinking:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return reply, thinking_process  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    return reply  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


async def ask_ollama_image(prompt: str, progress_cb=None) -> Path:  # 逐行註解：定義非同步函式 ask_ollama_image，可以搭配 await 處理 Discord 或網路等待。
    """
    用 Ollama 的 HTTP API 呼叫影像模型，回傳一張圖片路徑。
    圖片只會寫在 IMAGE_DIR，送出後會刪掉，避免堆在電腦上。
    """
    prompt = (prompt or "").strip()  # 逐行註解：設定 prompt 這個變數，供後面的流程使用。
    if not prompt:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        raise ValueError("empty prompt")  # 逐行註解：主動丟出錯誤，提醒設定或流程有問題。

    # 圖片模型用 stream=True，才能一邊生成一邊更新 Discord 進度。
    payload = {  # 逐行註解：開始建立一個跨多行的字典或集合資料。
        "model": "x/flux2-klein:latest",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        "prompt": prompt,  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        "stream": True,  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    }  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
    req = urlrequest.Request(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
        "http://127.0.0.1:11434/api/generate",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        data=json.dumps(payload).encode("utf-8"),  # 逐行註解：設定 data 這個變數，供後面的流程使用。
        headers={"Content-Type": "application/json"},  # 逐行註解：設定 headers 這個變數，供後面的流程使用。
        method="POST",  # 逐行註解：設定 method 這個變數，供後面的流程使用。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。

    def _do_stream_request() -> dict:  # 逐行註解：定義函式 _do_stream_request，把一段會重複使用的流程包起來。
        last: dict | None = None  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        collected_images: list[str] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            with urlrequest.urlopen(req, timeout=300) as resp:  # 逐行註解：開啟需要自動收尾的資源，例如網路回應或檔案。
                for raw_line in resp:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
                    if not raw_line:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                        continue  # 逐行註解：跳過本輪迴圈剩下的內容，直接進入下一輪。
                    line = raw_line.decode("utf-8", errors="replace").strip()  # 逐行註解：設定 line 這個變數，供後面的流程使用。
                    if not line:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                        continue  # 逐行註解：跳過本輪迴圈剩下的內容，直接進入下一輪。
                    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                        obj = json.loads(line)  # 逐行註解：設定 obj 這個變數，供後面的流程使用。
                    except json.JSONDecodeError:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                        continue  # 逐行註解：跳過本輪迴圈剩下的內容，直接進入下一輪。
                    # Ollama 串流每一行都是一個 JSON 片段；最後會包含圖片資料。
                    if isinstance(obj, dict):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                        last = obj  # 逐行註解：設定 last 這個變數，供後面的流程使用。
                        img_one = obj.get("image")  # 逐行註解：設定 img_one 這個變數，供後面的流程使用。
                        if isinstance(img_one, str) and img_one:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                            collected_images.append(img_one)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                        imgs = obj.get("images") or []  # 逐行註解：設定 imgs 這個變數，供後面的流程使用。
                        if isinstance(imgs, list):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                            for it in imgs:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
                                if isinstance(it, str) and it:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                                    collected_images.append(it)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                    if progress_cb is not None and isinstance(obj, dict):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                        status = (obj.get("response") or "").strip()  # 逐行註解：設定 status 這個變數，供後面的流程使用。
                        status = strip_thinking_process(status)  # 逐行註解：設定 status 這個變數，供後面的流程使用。
                        if not status and obj.get("done") is True:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                            status = "done"  # 逐行註解：設定 status 這個變數，供後面的流程使用。
                        if status:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                            progress_cb(status)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                    if isinstance(obj, dict) and obj.get("done") is True:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                        break  # 逐行註解：提前跳出目前這個迴圈。
        except (URLError, HTTPError) as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
            raise RuntimeError(f"ollama http error: {e}") from e  # 逐行註解：主動丟出錯誤，提醒設定或流程有問題。
        if not isinstance(last, dict):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            raise RuntimeError("no response from ollama")  # 逐行註解：主動丟出錯誤，提醒設定或流程有問題。
        if collected_images:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            last = dict(last)  # 逐行註解：設定 last 這個變數，供後面的流程使用。
            last["images"] = collected_images  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        return last  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    data = await asyncio.to_thread(_do_stream_request)  # 逐行註解：設定 data 這個變數，供後面的流程使用。
    images: list[str] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    img_one = data.get("image")  # 逐行註解：設定 img_one 這個變數，供後面的流程使用。
    if isinstance(img_one, str) and img_one:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        images.append(img_one)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    imgs = data.get("images") or []  # 逐行註解：設定 imgs 這個變數，供後面的流程使用。
    if isinstance(imgs, list):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        images.extend([x for x in imgs if isinstance(x, str) and x])  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    if not images:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        raise RuntimeError("no images returned from ollama")  # 逐行註解：主動丟出錯誤，提醒設定或流程有問題。

    img_b64 = images[0]  # 逐行註解：設定 img_b64 這個變數，供後面的流程使用。
    img_bytes = base64.b64decode(img_b64)  # 逐行註解：設定 img_bytes 這個變數，供後面的流程使用。

    out_path = (IMAGE_DIR / f"{uuid.uuid4().hex}.png").resolve()  # 逐行註解：設定 out_path 這個變數，供後面的流程使用。
    if IMAGE_DIR not in out_path.parents:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        raise RuntimeError("unsafe image path")  # 逐行註解：主動丟出錯誤，提醒設定或流程有問題。
    out_path.write_bytes(img_bytes)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    return out_path  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


#######################永久記憶 / PDF / YouTube / 語音 AI#######################
def split_discord_text(text: str, limit: int = DISCORD_TEXT_LIMIT) -> list[str]:  # 逐行註解：把任意長文字切成多則 Discord 訊息可送出的長度。
    text = (text or "").strip() or "（沒有內容）"  # 逐行註解：先整理空白，避免後面送出空訊息造成 Discord 錯誤。
    chunks: list[str] = []  # 逐行註解：建立最後要回傳的分段清單。
    current = ""  # 逐行註解：保存目前正在累積的訊息段落。
    for line in text.splitlines(keepends=True):  # 逐行註解：逐行處理並保留換行，讓輸出格式不要被壓扁。
        pieces = [line[i:i + limit] for i in range(0, len(line), limit)] or [""]  # 逐行註解：如果單行超長，就硬切成 Discord 可送出的片段。
        for piece in pieces:  # 逐行註解：逐一把安全長度的片段累積到目前訊息。
            if len(current) + len(piece) > limit and current:  # 逐行註解：如果加上這段會超過上限，就先收掉目前訊息。
                chunks.append(current.rstrip())  # 逐行註解：保存目前訊息，去掉尾端多餘空白。
                current = ""  # 逐行註解：重新開始累積下一則訊息。
            current += piece  # 逐行註解：把目前片段接進正在累積的訊息。
    if current.strip():  # 逐行註解：迴圈結束後，如果還有內容就加入結果。
        chunks.append(current.rstrip())  # 逐行註解：保存最後一則訊息。
    return chunks or ["（沒有內容）"]  # 逐行註解：保證至少回傳一段文字，避免呼叫端沒有東西可送。


async def send_interaction_text_chunks(interaction: discord.Interaction, text: str, *, ephemeral: bool = True):  # 逐行註解：把長文字用 interaction response/followup 自動分段送出。
    chart_payload = parse_chart_reply(text)  # 逐行註解：slash 文字送出前先檢查是否為圖表 JSON，避免 JSON 直接顯示。
    if chart_payload:  # 逐行註解：如果是圖表 JSON，就改送 PNG 圖表。
        await send_chart_payload_to_interaction_channel(interaction, chart_payload, ephemeral=ephemeral)  # 逐行註解：用 BytesIO 和 discord.File 把圖表送到原頻道。
        return  # 逐行註解：圖表已送出，不再送文字。
    if looks_like_chart_json_response(text):  # 逐行註解：解析失敗但看起來是圖表 JSON 時，禁止把 JSON 當文字送出。
        if not interaction.response.is_done():  # 逐行註解：如果 slash command 還沒回覆，就用第一則 response 傳安全提示。
            await interaction.response.send_message(CHART_PARSE_FAILED_MESSAGE, ephemeral=ephemeral)  # 逐行註解：送出安全錯誤提示，不洩漏 JSON。
        else:  # 逐行註解：如果已經 defer 或已回覆，就用 followup 傳安全提示。
            await interaction.followup.send(CHART_PARSE_FAILED_MESSAGE, ephemeral=ephemeral)  # 逐行註解：送出安全錯誤提示，不洩漏 JSON。
        return  # 逐行註解：已攔截疑似圖表 JSON，停止文字流程。
    chunks = split_discord_text(text)  # 逐行註解：先依 Discord 單則長度限制分段。
    first = True  # 逐行註解：記錄目前是不是第一則，第一則可能要用 interaction.response。
    for chunk in chunks:  # 逐行註解：逐段送出文字。
        if first and not interaction.response.is_done():  # 逐行註解：如果 slash command 還沒回覆過，第一則必須用 response。
            await interaction.response.send_message(chunk, ephemeral=ephemeral)  # 逐行註解：送出第一則 slash response。
        else:  # 逐行註解：如果已經 defer 或已回覆，後續都用 followup。
            await interaction.followup.send(chunk, ephemeral=ephemeral)  # 逐行註解：送出後續分段訊息。
        first = False  # 逐行註解：第一則送完後，後面固定走 followup。


async def send_interaction_embed_pages(interaction: discord.Interaction, embeds: list[discord.Embed], *, ephemeral: bool = True):  # 逐行註解：把多頁 Embed 用 slash response/followup 送出。
    if not embeds:  # 逐行註解：如果呼叫端沒有建立 Embed，就不要送出空內容。
        await send_interaction_text_chunks(interaction, "（沒有內容）", ephemeral=ephemeral)  # 逐行註解：用文字備援提醒使用者沒有內容。
        return  # 逐行註解：送完備援訊息後結束。
    first = True  # 逐行註解：記錄目前是不是第一頁。
    for embed in embeds:  # 逐行註解：逐頁送出 Embed。
        if first and not interaction.response.is_done():  # 逐行註解：如果還沒回覆 slash command，第一頁用 response。
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)  # 逐行註解：送出第一頁 Embed。
        else:  # 逐行註解：如果已經 defer 或已回覆，後續頁用 followup。
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)  # 逐行註解：送出後續 Embed。
        first = False  # 逐行註解：第一頁送完後，後面固定用 followup。


def clean_memory_request_content(content: str, max_chars: int = MEMORY_SUGGESTION_MAX_CHARS) -> str:
    """整理使用者要求記憶的原始內容，但不改成 AI 自己的身份。"""
    cleaned = (content or "").strip()
    cleaned = re.sub(r"^[：:，,。.!！\s]+", "", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip()
    return cleaned


def extract_temporary_memory_candidate(user_text: str) -> str:
    """抓出「暫時記得」這類只要放進短期聊天記錄的內容。"""
    text = (user_text or "").strip()
    if not text:
        return ""
    patterns = (
        r"^(?:請你|請|麻煩你|麻煩|幫我|幫忙|替我)?\s*(?:先|暫時|短期)\s*(?:記住|記得|記憶|記錄|記下)\s*[:：]?\s*(.+)$",
        r"^(?:請你|請|麻煩你|麻煩|幫我|幫忙|替我)?\s*(?:記住|記得|記憶|記錄|記下).{0,8}(?:暫時|短期|這段聊天|這次聊天)\s*[:：]?\s*(.+)$",
        r"^(?:temporarily remember|remember temporarily|keep this temporarily|temporary memory)\s*[:：]?\s*(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        content = clean_memory_request_content(match.group(1), CONVERSATION_MEMORY_ENTRY_MAX_CHARS)
        if content:
            return content
    return ""


def user_text_has_memory_request(user_text: str) -> bool:  # 逐行註解：判斷使用者是否明確要求 AI 記住內容，避免每次聊天都跳記憶選單。
    text = (user_text or "").strip().lower()  # 逐行註解：整理使用者訊息並轉成小寫，方便比對中英文記憶關鍵字。
    if not text:  # 逐行註解：空訊息不可能是記憶要求。
        return False  # 逐行註解：回傳 False，表示不要觸發記憶判斷。
    if extract_temporary_memory_candidate(user_text):  # 逐行註解：暫時記憶只寫短期聊天記錄，不跳永久記憶確認。
        return False  # 逐行註解：避免「暫時記得」又被問要不要寫永久記憶。
    memory_question_patterns = (  # 逐行註解：列出含有記憶字眼但其實是在問問題的常見說法。
        r"(記憶|記得).*(嗎|嘛|什麼|甚麼|哪些|哪個|誰|有沒有|是否|能不能|會不會)",  # 逐行註解：支援「你有記憶嗎」「記憶裡有什麼」這類問題。
        r"(列出|顯示|查看|查詢|查|讀取|回想|recall|list|show).*(記憶|memory)",  # 逐行註解：支援要求查看記憶，不代表要新增記憶。
        r"(memory|remember).*(what|do you|can you|did you|have|list|recall|show)",  # 逐行註解：支援英文記憶問題，不觸發保存確認。
    )  # 逐行註解：結束記憶問題規則清單。
    if any(re.search(pattern, text) for pattern in memory_question_patterns):  # 逐行註解：如果只是記憶相關問題，就不要跳記憶確認。
        return False  # 逐行註解：回傳 False，表示不觸發記憶確認。
    explicit_memory_patterns = (  # 逐行註解：只列出明確命令 AI 記住內容的常見說法，不把一般記憶問題算進來。
        r"^(請你|請|麻煩你|麻煩|你要|要)\s*(記住|記得|記憶|記錄|記下)",  # 逐行註解：支援「請記住」「你要記得」這類命令句。
        r"(記住|記得|記憶|記錄|記下)\s*[:：]",  # 逐行註解：支援「記憶：內容」「記住：內容」這類冒號句型。
        r"(永遠|永久)\s*(記住|記得|記憶|記錄|記下)",  # 逐行註解：支援「永遠記憶」「永久記住」這類長期記憶句型。
        r"(記住|記得|記憶|記錄|記下).{0,8}(我會|我喜歡|我使用|我叫|我是|我的)",  # 逐行註解：支援「記憶我會寫」「記住我喜歡」這種沒有請字的句型。
        r"^(記住|記下|記錄)\s*(一下|這個|這件事|我的|我叫|我喜歡|我最|我使用|我有|我會)",  # 逐行註解：支援使用者直接用「記住我...」開頭。
        r"(幫我|替我|幫忙).{0,12}(記一下|記住|記得|記憶|記錄|記下|存)",  # 逐行註解：支援「幫我記一下」「替我記」這類明確請求。
        r"(存到|加入|加到|放進).{0,8}記憶",  # 逐行註解：支援「存到記憶」「加入記憶」。
        r"以後.{0,8}(要知道|要記得)",  # 逐行註解：支援「你以後要知道...」或「以後要記得...」。
        r"(please remember|remember that|remember this|save this|save to memory|keep this in mind)",  # 逐行註解：支援明確英文記憶請求。
    )  # 逐行註解：結束記憶觸發規則清單。
    if any(re.search(pattern, text) for pattern in explicit_memory_patterns):  # 逐行註解：只有符合明確命令式記憶語句，才允許後續 AI 判斷器處理。
        return True  # 逐行註解：回傳 True，代表這句話有明確要求記憶。
    return False  # 逐行註解：沒有明確要求記憶時，一律不跳要不要記憶。


def normalize_memory_content(content: str) -> str:  # 逐行註解：把記憶內容標準化，供重複記憶比對使用。
    normalized = re.sub(r"\s+", "", content or "")  # 逐行註解：移除所有空白，避免同一句只差空格就被當成不同記憶。
    normalized = re.sub(r"[，,。.!！?？；;：:、「」『』\"'`~～（）()【】\\[\\]]+", "", normalized)  # 逐行註解：移除常見標點，降低重複記憶誤判機率。
    return normalized.lower()  # 逐行註解：回傳小寫標準化文字，英文大小寫不同也視為同一記憶。


def permanent_memory_exists(user_id: int, content: str) -> bool:  # 逐行註解：檢查使用者永久記憶中是否已經有相同或近似內容。
    normalized_content = normalize_memory_content(content)  # 逐行註解：先標準化候選記憶內容。
    if not normalized_content:  # 逐行註解：空內容不需要比對。
        return False  # 逐行註解：空候選內容視為不存在。
    for item in load_permanent_memories(user_id):  # 逐行註解：逐筆讀取目前使用者自己的永久記憶。
        existing_content = normalize_memory_content(str(item.get("content") or ""))  # 逐行註解：標準化既有記憶內容。
        if existing_content == normalized_content:  # 逐行註解：完全相同時視為已存在。
            return True  # 逐行註解：回傳 True，後續仍會跳確認選單，但會提示建議不要重複保存。
        if existing_content and (existing_content in normalized_content or normalized_content in existing_content):  # 逐行註解：一方包含另一方時也視為近似重複。
            return True  # 逐行註解：回傳 True，後續仍會詢問使用者，只是會標示已經有此記憶。
    return False  # 逐行註解：沒有找到相同或近似記憶。


def memory_candidate_has_sensitive_content(content: str) -> bool:  # 逐行註解：判斷候選永久記憶是否含有不該保存的敏感資料。
    text = (content or "").strip().lower()  # 逐行註解：整理候選記憶文字，方便同時檢查中英文敏感字。
    sensitive_patterns = (  # 逐行註解：列出不應該自動提示保存的敏感資訊種類。
        r"密碼",  # 逐行註解：避免保存使用者密碼。
        r"password",  # 逐行註解：避免保存英文密碼內容。
        r"api[_\-\s]*key",  # 逐行註解：避免保存 API key。
        r"token",  # 逐行註解：避免保存 token。
        r"信用卡",  # 逐行註解：避免保存信用卡資訊。
        r"身分證",  # 逐行註解：避免保存身分證字號。
        r"身份證",  # 逐行註解：避免保存另一種身分證寫法。
        r"地址",  # 逐行註解：避免保存住址或地址資訊。
    )  # 逐行註解：結束敏感規則清單。
    return any(re.search(pattern, text) for pattern in sensitive_patterns)  # 逐行註解：只要符合任一敏感規則，就回傳 True。


def cleanup_explicit_memory_candidate(candidate: str) -> str:  # 逐行註解：把使用者明確要求記憶的內容整理成永久記憶候選文字。
    content = (candidate or "").strip()  # 逐行註解：先移除候選內容頭尾空白。
    content = re.sub(r"^[：:，,。.!！\s]+", "", content).strip()  # 逐行註解：移除開頭冒號、逗號和空白。
    content = re.sub(r"^(我|我的)\s*", "使用者", content)  # 逐行註解：把第一人稱改成使用者資料，避免變成 AI 自己的身份。
    content = re.sub(r"^(你|你的)\s*", "使用者", content)  # 逐行註解：使用者口語寫成「你」時，也改成使用者資料，避免身份混淆。
    if content and not content.startswith("使用者"):  # 逐行註解：如果整理後沒有主詞，就補上使用者主詞。
        content = f"使用者{content}"  # 逐行註解：補成清楚的使用者永久記憶。
    content = re.sub(r"\s+", " ", content).strip()  # 逐行註解：合併多餘空白，讓確認選單更乾淨。
    if len(content) > MEMORY_SUGGESTION_MAX_CHARS:  # 逐行註解：如果內容太長，就截到永久記憶建議上限。
        content = content[:MEMORY_SUGGESTION_MAX_CHARS].rstrip()  # 逐行註解：保留前段並移除尾端空白。
    if memory_candidate_has_sensitive_content(content):  # 逐行註解：如果整理後含敏感資料，就不要提供記憶按鈕。
        return ""  # 逐行註解：回傳空字串，避免要求使用者保存敏感資料。
    return content  # 逐行註解：回傳整理好的候選永久記憶。


def extract_explicit_memory_candidate(user_text: str) -> str:  # 逐行註解：當模型判斷器失敗時，從明確記憶命令中抓出候選記憶。
    text = (user_text or "").strip()  # 逐行註解：取得使用者原始文字並移除頭尾空白。
    patterns = (  # 逐行註解：列出只處理明確記憶命令的擷取規則。
        r"^(?:你好[，,！!\s]*)?(?:請你|請|麻煩你|麻煩|你要|要|永遠|永久)?\s*(?:記住|記得|記憶|記錄|記下)\s*[:：]?\s*(.+)$",  # 逐行註解：支援「你好，記憶我會寫」「永遠記憶：內容」。
        r"^(?:幫我|替我|幫忙).{0,12}(?:記一下|記住|記得|記憶|記錄|記下|存)\s*[:：]?\s*(.+)$",  # 逐行註解：支援「幫我記一下，內容」。
        r"^(?:存到|加入|加到|放進).{0,8}記憶\s*[:：]?\s*(.+)$",  # 逐行註解：支援「存到記憶：內容」。
    )  # 逐行註解：結束擷取規則清單。
    for pattern in patterns:  # 逐行註解：逐一嘗試每種明確記憶句型。
        match = re.search(pattern, text, flags=re.I)  # 逐行註解：用正則比對目前句型。
        if not match:  # 逐行註解：如果這個句型不符合，就換下一個。
            continue  # 逐行註解：繼續嘗試下一個擷取規則。
        candidate = cleanup_explicit_memory_candidate(match.group(1))  # 逐行註解：整理抓到的候選記憶內容。
        if candidate:  # 逐行註解：如果整理後還有可保存內容，就回傳。
            return candidate  # 逐行註解：回傳候選永久記憶。
    return ""  # 逐行註解：沒有抓到安全候選內容時回傳空字串。


def parse_memory_judgement(raw_text: str) -> dict:  # 逐行註解：解析 AI 記憶判斷器回傳的 JSON，避免模型多包 code block 時壞掉。
    cleaned = (raw_text or "").strip()  # 逐行註解：先清理模型輸出頭尾空白。
    cleaned = re.sub(r"(?is)^```(?:json)?\s*|\s*```$", "", cleaned).strip()  # 逐行註解：移除模型可能包上的 markdown JSON code block。
    match = re.search(r"\{.*\}", cleaned, flags=re.S)  # 逐行註解：從輸出中抓第一段 JSON 物件，避免前後有解釋文字。
    if match:  # 逐行註解：如果有抓到 JSON 物件，就只解析該段。
        cleaned = match.group(0)  # 逐行註解：把待解析文字換成 JSON 物件本身。
    try:  # 逐行註解：解析模型回傳 JSON 可能失敗，所以用 try 保護。
        data = json.loads(cleaned)  # 逐行註解：把 JSON 字串轉成 Python dict。
    except Exception as e:  # 逐行註解：解析失敗時回傳否，避免誤存記憶。
        print(f"記憶判斷 JSON 解析失敗：{type(e).__name__}: {e}；原文：{raw_text[:300]}")  # 逐行註解：把解析問題印到後台方便調整 prompt。
        return {"should_remember": False, "content": ""}  # 逐行註解：解析失敗時不要跳記憶確認。
    if not isinstance(data, dict):  # 逐行註解：如果模型不是回傳 JSON 物件，就當作不要記憶。
        return {"should_remember": False, "content": ""}  # 逐行註解：格式不符時不要跳記憶確認。
    should_remember = bool(data.get("should_remember"))  # 逐行註解：讀取 AI 判斷是否應該記憶。
    content = str(data.get("content") or "").strip()  # 逐行註解：讀取 AI 整理後要保存的記憶內容。
    if len(content) > MEMORY_SUGGESTION_MAX_CHARS:  # 逐行註解：如果建議記憶太長，就截斷到安全長度。
        content = content[:MEMORY_SUGGESTION_MAX_CHARS].rstrip()  # 逐行註解：保留前段記憶內容並移除尾端空白。
    return {"should_remember": should_remember and bool(content), "content": content}  # 逐行註解：只有 AI 判斷要記且內容非空時才回傳 True。


def build_memory_json_item(memory_id: int, content: str, created_at: str | None = None) -> dict:
    """建立和 memories/<user_id>.json 相同欄位的記憶項目。"""
    return {
        "id": int(memory_id),
        "content": str(content or "").strip(),
        "created_at": created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def format_memory_json_items(items: list[dict]) -> str:
    """用固定 JSON 格式顯示記憶預覽，讓顯示和寫入格式一致。"""
    return json.dumps(items, ensure_ascii=False, indent=2)


def format_memory_json_code_block(items: list[dict]) -> str:
    """把記憶 JSON 包成 Discord code block。"""
    return f"```json\n{format_memory_json_items(items)}\n```"


def build_memory_judgement_prompt(user_text: str, assistant_text: str) -> str:  # 逐行註解：建立讓 AI 自己判斷是否需要跳出記憶確認的 prompt。
    clipped_user_text = (user_text or "").strip()[:2000]  # 逐行註解：限制使用者訊息長度，避免判斷 prompt 過長。
    clipped_assistant_text = (assistant_text or "").strip()[:1200]  # 逐行註解：保留 AI 回答摘要給判斷器參考，但不讓它太長。
    return f"""  # 逐行註解：回傳多行 prompt，要求模型輸出嚴格 JSON。
你是 Smart_Sean 的永久記憶判斷器。
你的工作不是回答使用者，而是判斷使用者是否想讓 AI 記住一件長期資料。

判斷標準：
1. 只有使用者明確說「記住」「幫我記」「你要記得」「remember」「save this」「以後要知道」等意思，才可以 should_remember=true。
2. 如果使用者只是一般提問、聊天、請求摘要、請求翻譯、請求搜尋、請求分析，should_remember=false。
3. 記憶內容必須是使用者資料、偏好、身份、習慣、設備、長期需求，不能保存 AI 自己的身份。
4. 不要保存密碼、API key、token、信用卡、身分證、地址等敏感資料。
5. content 要改寫成清楚的使用者資料，例如「使用者喜歡 Gemma4」。

只能輸出 JSON，不要輸出解釋文字：
{{"should_remember": true, "content": "使用者喜歡 Gemma4"}}
或
{{"should_remember": false, "content": ""}}

使用者訊息：
{clipped_user_text}

AI 回答：
{clipped_assistant_text}
""".strip()  # 逐行註解：整理 prompt 頭尾空白後回傳。


async def judge_memory_suggestion(model: str, user_text: str, assistant_text: str) -> str:  # 逐行註解：用目前 Ollama 文字模型判斷是否要詢問使用者保存永久記憶。
    judge_model = selected_text_model_for_user(0) if model == "x/flux2-klein:latest" else model  # 逐行註解：如果目前是圖片模型，就改用可用文字模型做記憶判斷。
    prompt = build_memory_judgement_prompt(user_text, assistant_text)  # 逐行註解：建立記憶判斷 prompt。
    raw_reply = await ask_ollama_text(judge_model, prompt, timeout_s=None)  # 逐行註解：請 AI 判斷這次對話是否需要跳出記憶確認。
    judgement = parse_memory_judgement(str(raw_reply))  # 逐行註解：解析 AI 回傳的 JSON 判斷結果。
    print(f"記憶判斷：model={judge_model} result={judgement}")  # 逐行註解：把記憶判斷結果印到後台，方便觀察是否太敏感或太保守。
    return str(judgement.get("content") or "").strip() if judgement.get("should_remember") else ""  # 逐行註解：只有 AI 判斷要記憶時才回傳內容。


class MemorySuggestionView(discord.ui.View):  # 逐行註解：建立記憶確認按鈕，讓使用者決定是否真的寫入永久記憶。
    def __init__(self, user_id: int, content: str, preview_item: dict | None = None):  # 逐行註解：初始化記憶確認 View，記住使用者 ID 和候選記憶內容。
        super().__init__(timeout=180)  # 逐行註解：按鈕 180 秒後自動失效。
        self.user_id = user_id  # 逐行註解：保存可操作這組按鈕的 Discord 使用者 ID。
        self.content = (content or "").strip()[:MEMORY_SUGGESTION_MAX_CHARS]  # 逐行註解：保存候選永久記憶內容並限制長度。
        self.preview_item = preview_item or build_memory_json_item(0, self.content)  # 逐行註解：保存按鈕訊息顯示用的 memories JSON 格式。

    async def interaction_check(self, interaction: discord.Interaction) -> bool:  # 逐行註解：限制只有原本使用者能按記憶確認按鈕。
        if interaction.user.id != self.user_id:  # 逐行註解：如果不是原本使用者，就拒絕操作。
            await interaction.response.send_message("這不是你的記憶確認選單。", ephemeral=True)  # 逐行註解：提醒其他使用者不能代按。
            return False  # 逐行註解：拒絕這次互動。
        return True  # 逐行註解：原本使用者可以操作。

    @discord.ui.button(label="要，幫我記憶", style=discord.ButtonStyle.primary)  # 逐行註解：建立確認保存記憶的按鈕。
    async def remember_button(self, interaction: discord.Interaction, button: discord.ui.Button):  # 逐行註解：處理使用者按下「要」。
        memories = load_permanent_memories(self.user_id)  # 逐行註解：讀取目前使用者自己的永久記憶清單。
        memory_id = next_permanent_memory_id(memories)  # 逐行註解：計算下一個永久記憶編號。
        item = build_memory_json_item(memory_id, self.content)  # 逐行註解：建立符合 memories JSON 格式的新記憶。
        memories.append(item)  # 逐行註解：把新記憶加入清單。
        save_permanent_memories(self.user_id, memories)  # 逐行註解：寫回使用者專屬 JSON 檔。
        for child in self.children:  # 逐行註解：保存後停用所有按鈕，避免重複寫入。
            child.disabled = True  # 逐行註解：停用這個按鈕。
        await interaction.response.edit_message(content=f"✅ 已寫入 memories JSON：\n{format_memory_json_code_block([item])}", view=self)  # 逐行註解：把原本確認訊息改成保存成功。
        self.stop()  # 逐行註解：停止 View 等待。

    @discord.ui.button(label="不要", style=discord.ButtonStyle.secondary)  # 逐行註解：建立取消保存記憶的按鈕。
    async def forget_button(self, interaction: discord.Interaction, button: discord.ui.Button):  # 逐行註解：處理使用者按下「不要」。
        for child in self.children:  # 逐行註解：取消後停用所有按鈕。
            child.disabled = True  # 逐行註解：停用這個按鈕。
        await interaction.response.edit_message(content=f"已取消寫入 memories JSON：\n{format_memory_json_code_block([self.preview_item])}", view=self)  # 逐行註解：把原本確認訊息改成取消狀態。
        self.stop()  # 逐行註解：停止 View 等待。


async def send_memory_confirmation_offer(user_id: int, content: str, send_offer) -> None:
    """用固定 memories JSON 格式顯示永久記憶確認選單。"""
    content = (content or "").strip()
    if not content:
        return
    memories = load_permanent_memories(user_id)
    preview_item = build_memory_json_item(next_permanent_memory_id(memories), content)
    duplicate_hint = "\n（建議不要，因為已經有此記憶）" if permanent_memory_exists(user_id, content) else ""
    view = MemorySuggestionView(user_id, content, preview_item=preview_item)
    await send_offer(f"要不要寫入 memories JSON：\n{format_memory_json_code_block([preview_item])}{duplicate_hint}", view)


async def maybe_offer_memory_suggestion(user_id: int, model: str, user_text: str, assistant_text: str, send_offer):  # 逐行註解：AI 回答後判斷是否要跳出永久記憶確認選單。
    if not user_text_has_memory_request(user_text):  # 逐行註解：只有使用者明確要求記憶時才進入 AI 記憶判斷器。
        return  # 逐行註解：沒有明確記憶要求時不呼叫模型、不跳選單。
    content = await judge_memory_suggestion(model, user_text, assistant_text)  # 逐行註解：請 AI 判斷這次對話是否像使用者要求記憶。
    if not content:  # 逐行註解：如果模型判斷器沒有產生候選內容，就使用明確命令的安全備援擷取。
        content = extract_explicit_memory_candidate(user_text)  # 逐行註解：從「記憶我會寫」這類句子抓出候選記憶，避免按鈕消失。
    if not content:  # 逐行註解：如果 AI 判斷不需要記憶，就不打擾使用者。
        return  # 逐行註解：結束記憶確認流程。
    await send_memory_confirmation_offer(user_id, content, send_offer)  # 逐行註解：用 memories JSON 格式顯示確認選單，使用者按要才真的寫入 JSON。


async def offer_memory_suggestion_after_answer(user_id: int, model: str, user_text: str, assistant_text: str, send_offer):  # 逐行註解：確保 AI 正式回答送完後，才開始處理記憶確認。
    await asyncio.sleep(0.8)  # 逐行註解：給 Discord 一點時間完成最後一次訊息 edit，避免確認選單看起來插在回答前面。
    await maybe_offer_memory_suggestion(user_id, model, user_text, assistant_text, send_offer)  # 逐行註解：回答完成後才執行記憶判斷與確認選單。


def permanent_memory_file_for_user(user_id: int) -> Path:  # 逐行註解：取得指定 Discord 使用者自己的永久記憶 JSON 路徑。
    safe_user_id = re.sub(r"[^0-9]", "", str(user_id)) or "unknown"  # 逐行註解：只保留數字 ID，避免任何奇怪字元被拿來組路徑。
    return (MEMORIES_DIR / f"{safe_user_id}.json").resolve()  # 逐行註解：回傳 memories/<user_id>.json 的完整路徑。


def load_permanent_memories(user_id: int) -> list[dict]:  # 逐行註解：讀取指定使用者的永久記憶清單，不會讀到其他使用者檔案。
    path = permanent_memory_file_for_user(user_id)  # 逐行註解：先取得這位使用者自己的 JSON 檔路徑。
    if not path.exists():  # 逐行註解：如果檔案不存在，代表這位使用者第一次使用永久記憶。
        save_permanent_memories(user_id, [])  # 逐行註解：自動建立空 JSON 檔，滿足重啟後可持續使用的格式。
        return []  # 逐行註解：第一次使用時回傳空清單。
    try:  # 逐行註解：讀 JSON 可能遇到檔案損壞，所以用 try 保護。
        data = json.loads(path.read_text(encoding="utf-8"))  # 逐行註解：用 UTF-8 讀取，確保繁體中文不亂碼。
    except Exception as e:  # 逐行註解：捕捉 JSON 格式錯誤或讀檔錯誤。
        print(f"讀取永久記憶失敗（{path.name}）：{type(e).__name__}: {e}")  # 逐行註解：把問題印到後台，不在使用者端洩漏路徑細節。
        return []  # 逐行註解：讀取失敗時回傳空清單，避免 bot 崩潰。
    if not isinstance(data, list):  # 逐行註解：永久記憶檔必須是最外層 list。
        return []  # 逐行註解：格式不正確時回傳空清單。
    memories: list[dict] = []  # 逐行註解：建立清理後的記憶清單。
    for item in data:  # 逐行註解：逐筆檢查 JSON 裡的記憶項目。
        if isinstance(item, dict) and "id" in item and "content" in item:  # 逐行註解：只保留有 id 和 content 的有效項目。
            memories.append(item)  # 逐行註解：加入有效記憶項目。
    return sorted(memories, key=lambda item: int(item.get("id", 0)))  # 逐行註解：依照編號排序後回傳。


def save_permanent_memories(user_id: int, memories: list[dict]) -> None:  # 逐行註解：把指定使用者的永久記憶寫回自己的 JSON 檔。
    path = permanent_memory_file_for_user(user_id)  # 逐行註解：取得這位使用者自己的永久記憶檔路徑。
    if MEMORIES_DIR not in path.parents:  # 逐行註解：安全檢查，避免任何意外路徑寫出 memories 資料夾外。
        raise RuntimeError("unsafe memories path")  # 逐行註解：路徑異常時直接中止，避免寫錯檔案。
    path.write_text(json.dumps(memories, ensure_ascii=False, indent=4), encoding="utf-8")  # 逐行註解：用 UTF-8 與 ensure_ascii=False 保存繁體中文。


def next_permanent_memory_id(memories: list[dict]) -> int:  # 逐行註解：計算下一筆永久記憶的編號。
    ids = [int(item.get("id", 0)) for item in memories if str(item.get("id", "")).isdigit()]  # 逐行註解：從現有記憶抽出有效數字 ID。
    return (max(ids) + 1) if ids else 1  # 逐行註解：如果已有記憶就接續最大編號，否則從 1 開始。


def format_permanent_memory_blocks(memories: list[dict]) -> list[str]:  # 逐行註解：把永久記憶轉成 /list 和 /recall 都能重用的文字區塊。
    blocks: list[str] = []  # 逐行註解：建立每筆記憶的顯示區塊清單。
    for item in sorted(memories, key=lambda row: int(row.get("id", 0))):  # 逐行註解：依照記憶編號排序後逐筆格式化。
        memory_id = item.get("id")  # 逐行註解：取得記憶編號。
        content = str(item.get("content") or "").strip()  # 逐行註解：取得記憶內容並清掉頭尾空白。
        created_at = str(item.get("created_at") or "未知").strip()  # 逐行註解：取得建立時間，舊資料缺欄位時顯示未知。
        blocks.append(f"[{memory_id}]\n{content}\n\n建立時間：\n{created_at}")  # 逐行註解：組成使用者要求的編號、內容與建立時間格式。
    return blocks  # 逐行註解：回傳所有記憶區塊。


def build_memory_list_embeds(memories: list[dict], *, title: str = "📚 我的永久記憶") -> list[discord.Embed]:  # 逐行註解：把永久記憶清單做成可自動分頁的 Discord Embed。
    if not memories:  # 逐行註解：如果這位使用者沒有永久記憶，就建立空狀態 Embed。
        return [discord.Embed(title=title, description="目前沒有永久記憶。", color=0x2F81F7)]  # 逐行註解：回傳單頁空狀態 Embed。
    pages: list[str] = []  # 逐行註解：建立每頁 description 文字清單。
    current = ""  # 逐行註解：保存目前正在累積的 Embed description。
    for block in format_permanent_memory_blocks(memories):  # 逐行註解：逐筆把記憶區塊放入頁面。
        candidate = f"{current}\n\n{block}".strip()  # 逐行註解：嘗試把目前記憶接到目前頁面後面。
        if len(candidate) > DISCORD_EMBED_DESCRIPTION_LIMIT and current:  # 逐行註解：如果超過 Embed 上限，就先收掉目前頁。
            pages.append(current)  # 逐行註解：保存目前頁面。
            current = block  # 逐行註解：用目前記憶開新頁。
        else:  # 逐行註解：如果還沒超過上限，就繼續累積。
            current = candidate  # 逐行註解：更新目前頁面內容。
    if current:  # 逐行註解：如果最後還有頁面內容，就加入頁面清單。
        pages.append(current)  # 逐行註解：保存最後一頁。
    embeds: list[discord.Embed] = []  # 逐行註解：建立 Embed 物件清單。
    for index, page in enumerate(pages, start=1):  # 逐行註解：逐頁建立 Embed。
        page_title = title if len(pages) == 1 else f"{title}（{index}/{len(pages)}）"  # 逐行註解：多頁時在標題標出目前頁數。
        embeds.append(discord.Embed(title=page_title, description=page, color=0x2F81F7))  # 逐行註解：建立這一頁 Embed 並加入清單。
    return embeds  # 逐行註解：回傳所有 Embed 頁面。


def selected_text_model_for_user(user_id: int) -> str:  # 逐行註解：取得使用者目前可用的文字模型，避免把圖片模型拿去做摘要。
    selected_model = dm_user_model.get(user_id, DEFAULT_CHAT_MODEL)  # 逐行註解：優先使用 DM 裡選過的模型，沒有就用預設文字模型。
    if selected_model == "x/flux2-klein:latest":  # 逐行註解：如果使用者目前選的是圖片生成模型，就不能拿來做文字摘要。
        return DEFAULT_CHAT_MODEL  # 逐行註解：圖片模型時退回預設文字聊天模型。
    return selected_model  # 逐行註解：回傳可用的文字模型。


def is_gemma4_model(model: str) -> bool:  # 逐行註解：判斷目前模型是不是 gemma4 系列，PDF 圖片分析會用到。
    return (model or "").strip().lower().startswith("gemma4")  # 逐行註解：gemma4_thinking、gemma4_Instant 等都算 Gemma4 系列。


def extract_pdf_text_with_pymupdf(pdf_bytes: bytes) -> str:  # 逐行註解：優先用 PyMuPDF 從 PDF bytes 抽取文字。
    import fitz  # 逐行註解：延遲匯入 PyMuPDF，避免 bot 啟動時因單一套件問題整個失敗。
    text_parts: list[str] = []  # 逐行註解：建立每頁文字清單。
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:  # 逐行註解：直接從下載到的 PDF bytes 開啟文件。
        for page_index, page in enumerate(doc, start=1):  # 逐行註解：逐頁讀取 PDF 文字。
            page_text = (page.get_text("text") or "").strip()  # 逐行註解：取得目前頁面的純文字內容。
            if page_text:  # 逐行註解：如果這頁有文字，就加入結果。
                text_parts.append(f"第 {page_index} 頁：\n{page_text}")  # 逐行註解：保留頁碼，讓考試重點可以引用頁面脈絡。
    return "\n\n".join(text_parts).strip()  # 逐行註解：把所有頁面文字接成一份文字。


def extract_pdf_text_with_pdfplumber(pdf_bytes: bytes) -> str:  # 逐行註解：PyMuPDF 讀不到時，用 pdfplumber 做第二層抽取。
    import pdfplumber  # 逐行註解：延遲匯入 pdfplumber，讓缺套件問題只影響 PDF 功能。
    text_parts: list[str] = []  # 逐行註解：建立每頁文字清單。
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:  # 逐行註解：把 PDF bytes 包成檔案物件交給 pdfplumber。
        for page_index, page in enumerate(pdf.pages, start=1):  # 逐行註解：逐頁讀取 PDF 文字。
            page_text = (page.extract_text() or "").strip()  # 逐行註解：取得目前頁面文字。
            if page_text:  # 逐行註解：如果這頁有文字，就加入結果。
                text_parts.append(f"第 {page_index} 頁：\n{page_text}")  # 逐行註解：保留頁碼，方便後續摘要。
    return "\n\n".join(text_parts).strip()  # 逐行註解：回傳整份 PDF 文字。


async def extract_pdf_text(pdf_bytes: bytes) -> str:  # 逐行註解：非同步包裝 PDF 文字抽取，避免阻塞 Discord event loop。
    def _extract() -> str:  # 逐行註解：同步 PDF 套件放在 thread 裡執行。
        text = ""  # 逐行註解：建立抽取結果變數。
        try:  # 逐行註解：先嘗試 PyMuPDF。
            text = extract_pdf_text_with_pymupdf(pdf_bytes)  # 逐行註解：用 PyMuPDF 抽文字。
        except Exception as e:  # 逐行註解：PyMuPDF 失敗時不要中斷，改用 pdfplumber。
            print(f"PyMuPDF 讀取 PDF 失敗：{type(e).__name__}: {e}")  # 逐行註解：把 PyMuPDF 問題記錄到後台。
        if text.strip():  # 逐行註解：如果 PyMuPDF 已經讀到文字，就直接回傳。
            return text.strip()  # 逐行註解：回傳 PyMuPDF 結果。
        try:  # 逐行註解：第二層改用 pdfplumber。
            return extract_pdf_text_with_pdfplumber(pdf_bytes)  # 逐行註解：用 pdfplumber 抽文字。
        except Exception as e:  # 逐行註解：pdfplumber 也失敗時回傳空字串。
            print(f"pdfplumber 讀取 PDF 失敗：{type(e).__name__}: {e}")  # 逐行註解：把 pdfplumber 問題記錄到後台。
            return ""  # 逐行註解：兩個 PDF 套件都讀不到時回空字串。
    return await asyncio.to_thread(_extract)  # 逐行註解：把同步 PDF 解析放到 thread 裡跑。


def inspect_pdf_images_with_pymupdf(pdf_bytes: bytes) -> dict:  # 逐行註解：使用 PyMuPDF 檢查 PDF 是否包含圖片頁或掃描頁。
    import fitz  # 逐行註解：延遲匯入 PyMuPDF，讓 PDF 功能需要時才載入套件。
    page_infos: list[dict] = []  # 逐行註解：建立每頁偵測結果清單。
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:  # 逐行註解：直接從 PDF bytes 開啟文件，不另外落地存檔。
        for page_index, page in enumerate(doc, start=1):  # 逐行註解：逐頁檢查 PDF 內容。
            page_area = max(float(page.rect.width * page.rect.height), 1.0)  # 逐行註解：計算頁面面積，至少為 1 避免除以零。
            page_text = (page.get_text("text") or "").strip()  # 逐行註解：取得本頁可抽取文字，用來判斷是否可能是掃描頁。
            image_blocks = [block for block in page.get_text("dict").get("blocks", []) if block.get("type") == 1]  # 逐行註解：從 PyMuPDF block 裡找圖片 block。
            image_area = 0.0  # 逐行註解：累計本頁所有圖片 block 的面積。
            for block in image_blocks:  # 逐行註解：逐一計算每個圖片 block 的矩形面積。
                x0, y0, x1, y1 = block.get("bbox", (0, 0, 0, 0))  # 逐行註解：取得圖片 block 的位置座標。
                image_area += max(float(x1) - float(x0), 0.0) * max(float(y1) - float(y0), 0.0)  # 逐行註解：把圖片面積累加到本頁圖片總面積。
            image_ratio = image_area / page_area  # 逐行註解：計算圖片面積占整頁比例。
            page_has_images = bool(image_blocks) or bool(page.get_images(full=True))  # 逐行註解：只要 block 或 PDF 資源內有圖片，就標記本頁含圖片。
            page_is_scan = page_has_images and len(page_text) < 30  # 逐行註解：有圖片但文字很少時，判斷為掃描頁或整頁圖片。
            page_is_image_heavy = image_ratio >= PDF_IMAGE_AREA_THRESHOLD  # 逐行註解：圖片面積達門檻時，判斷為需要視覺分析。
            page_infos.append({  # 逐行註解：保存這一頁的偵測資訊。
                "page": page_index,  # 逐行註解：保存頁碼。
                "text_chars": len(page_text),  # 逐行註解：保存可抽文字字數。
                "image_count": len(image_blocks),  # 逐行註解：保存圖片 block 數量。
                "image_ratio": image_ratio,  # 逐行註解：保存圖片面積比例。
                "has_images": page_has_images,  # 逐行註解：保存是否含圖片。
                "is_scan": page_is_scan,  # 逐行註解：保存是否像掃描頁。
                "needs_vision": page_is_scan or page_is_image_heavy,  # 逐行註解：保存本頁是否建議用 Gemma4 視覺分析。
            })  # 逐行註解：結束這一頁偵測資訊。
    needs_vision_pages = [info["page"] for info in page_infos if info.get("needs_vision")]  # 逐行註解：整理需要視覺分析的頁碼。
    image_pages = [info["page"] for info in page_infos if info.get("has_images")]  # 逐行註解：整理所有含圖片的頁碼。
    return {"page_count": len(page_infos), "pages": page_infos, "needs_vision_pages": needs_vision_pages, "image_pages": image_pages}  # 逐行註解：回傳整份 PDF 的圖片偵測摘要。


async def inspect_pdf_images(pdf_bytes: bytes) -> dict:  # 逐行註解：非同步包裝 PDF 圖片偵測，避免阻塞 Discord event loop。
    def _inspect() -> dict:  # 逐行註解：同步 PyMuPDF 檢查流程放到 thread 裡執行。
        try:  # 逐行註解：圖片偵測可能遇到損壞 PDF，所以用 try 保護。
            return inspect_pdf_images_with_pymupdf(pdf_bytes)  # 逐行註解：執行 PyMuPDF 圖片偵測。
        except Exception as e:  # 逐行註解：偵測失敗時不要讓 /pdf 整個崩潰。
            print(f"PDF 圖片偵測失敗：{type(e).__name__}: {e}")  # 逐行註解：把偵測錯誤印到後台。
            return {"page_count": 0, "pages": [], "needs_vision_pages": [], "image_pages": []}  # 逐行註解：回傳空偵測結果作為備援。
    return await asyncio.to_thread(_inspect)  # 逐行註解：把同步偵測丟到 thread 裡執行。


def render_pdf_pages_to_images_with_pymupdf(pdf_bytes: bytes, page_numbers: list[int]) -> list[dict]:  # 逐行註解：把指定 PDF 頁面渲染成 PNG bytes，供 Gemma4 vision 分析。
    import fitz  # 逐行註解：延遲匯入 PyMuPDF，讓需要渲染圖片時才載入。
    rendered_pages: list[dict] = []  # 逐行註解：建立渲染結果清單。
    zoom = PDF_VISION_RENDER_DPI / 72.0  # 逐行註解：把 DPI 換算成 PyMuPDF matrix 縮放比例。
    matrix = fitz.Matrix(zoom, zoom)  # 逐行註解：建立頁面渲染用的縮放矩陣。
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:  # 逐行註解：從 PDF bytes 開啟文件。
        for page_number in page_numbers[:PDF_VISION_MAX_PAGES]:  # 逐行註解：只渲染限制內的頁數，避免一次處理太多圖片。
            if page_number < 1 or page_number > len(doc):  # 逐行註解：跳過不合法頁碼，避免索引錯誤。
                continue  # 逐行註解：繼續下一個頁碼。
            page = doc[page_number - 1]  # 逐行註解：PyMuPDF 使用 0-based index，所以頁碼要減一。
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)  # 逐行註解：把 PDF 頁面渲染成不透明 PNG 像素圖。
            rendered_pages.append({"page": page_number, "image_bytes": pixmap.tobytes("png")})  # 逐行註解：保存頁碼和 PNG bytes。
    return rendered_pages  # 逐行註解：回傳所有渲染後頁面圖片。


async def render_pdf_pages_to_images(pdf_bytes: bytes, page_numbers: list[int]) -> list[dict]:  # 逐行註解：非同步包裝 PDF 頁面渲染流程。
    return await asyncio.to_thread(render_pdf_pages_to_images_with_pymupdf, pdf_bytes, page_numbers)  # 逐行註解：把同步渲染放到 thread，避免卡住 Discord bot。


def build_pdf_analysis_prompt(filename: str, pdf_text: str) -> str:  # 逐行註解：建立 PDF 分析要送給 Ollama 的 prompt。
    clipped_text = (pdf_text or "").strip()[:PDF_TEXT_MAX_CHARS]  # 逐行註解：限制 PDF 文字長度，避免超過模型可處理範圍。
    lines = [  # 逐行註解：用清單組 prompt，讓每一行新增程式碼都保留註解。
        "你正在分析一份 PDF。",  # 逐行註解：說明任務類型。
        f"檔名：{filename}",  # 逐行註解：提供原始檔名。
        "請一定使用繁體中文回答。",  # 逐行註解：指定輸出語言。
        "請依照以下格式輸出：",  # 逐行註解：要求固定格式。
        "1. 100字摘要",  # 逐行註解：要求短摘要。
        "2. 500字摘要",  # 逐行註解：要求長摘要。
        "3. 重點整理",  # 逐行註解：要求條列重點。
        "4. 考試重點",  # 逐行註解：要求考試導向整理。
        "",  # 逐行註解：加入空行分隔一般摘要格式與圖表規則。
        "圖表輸出規則：",  # 逐行註解：提醒模型 PDF 內容需要視覺化時可改輸出圖表 JSON。
        chart_output_rules_prompt(),  # 逐行註解：加入可被程式端解析的圖表 JSON 規則。
        "",  # 逐行註解：加入空行讓 prompt 易讀。
        "PDF 文字內容如下：",  # 逐行註解：標示後面是文件內容。
        clipped_text,  # 逐行註解：放入抽取到的 PDF 文字。
    ]  # 逐行註解：結束 prompt 清單。
    return "\n".join(lines).strip()  # 逐行註解：把 prompt 清單接成單一字串。


def build_pdf_page_vision_prompt(filename: str, page_number: int) -> str:  # 逐行註解：建立單頁 PDF 圖片要送給 Gemma4 vision 的 prompt。
    lines = [  # 逐行註解：用清單組 prompt，方便每一行都加繁體中文註解。
        "你正在分析 PDF 的頁面圖片。",  # 逐行註解：告訴模型這張圖來自 PDF 頁面。
        f"檔名：{filename}",  # 逐行註解：提供 PDF 檔名作為上下文。
        f"頁碼：第 {page_number} 頁",  # 逐行註解：提供目前圖片頁碼。
        "請使用繁體中文回答。",  # 逐行註解：指定輸出語言。
        "請完整讀取頁面中的文字、表格、圖片、圖表與版面。",  # 逐行註解：要求模型同時看文字與視覺內容。
        "請輸出這一頁的重點、可見文字、圖表含義、考試可能會考的內容。",  # 逐行註解：要求單頁分析重點。
    ]  # 逐行註解：結束 prompt 清單。
    return "\n".join(lines).strip()  # 逐行註解：回傳單頁視覺分析 prompt。


def build_pdf_vision_summary_prompt(filename: str, page_analyses: list[str], pdf_text: str = "") -> str:  # 逐行註解：把多頁 Gemma4 視覺分析結果整理成最終 PDF 摘要 prompt。
    clipped_text = (pdf_text or "").strip()[:PDF_TEXT_MAX_CHARS]  # 逐行註解：保留可抽文字作為輔助資料，但仍限制長度。
    joined_analyses = "\n\n".join(page_analyses).strip()  # 逐行註解：把每頁圖片分析結果合併成一份資料。
    lines = [  # 逐行註解：用清單組最終摘要 prompt。
        "你正在整合一份 PDF 的文字抽取結果與頁面圖片分析結果。",  # 逐行註解：說明這次是整份 PDF 綜合分析。
        f"檔名：{filename}",  # 逐行註解：提供檔名。
        "請一定使用繁體中文回答。",  # 逐行註解：指定輸出語言。
        "請依照以下格式輸出：",  # 逐行註解：要求固定輸出格式。
        "1. 100字摘要",  # 逐行註解：要求短摘要。
        "2. 500字摘要",  # 逐行註解：要求長摘要。
        "3. 重點整理",  # 逐行註解：要求重點整理。
        "4. 考試重點",  # 逐行註解：要求考試重點。
        "",  # 逐行註解：加入空行分隔一般摘要格式與圖表規則。
        "圖表輸出規則：",  # 逐行註解：提醒模型 PDF 視覺分析需要圖表時可改輸出圖表 JSON。
        chart_output_rules_prompt(),  # 逐行註解：加入可被程式端解析的圖表 JSON 規則。
        "",  # 逐行註解：加入空行讓 prompt 易讀。
        "頁面圖片分析結果：",  # 逐行註解：標示後面是 Gemma4 看圖後的結果。
        joined_analyses or "無",  # 逐行註解：放入每頁圖片分析，沒有時填無。
        "",  # 逐行註解：加入空行。
        "PDF 可抽取文字輔助資料：",  # 逐行註解：標示後面是 PDF 文字抽取輔助資料。
        clipped_text or "無",  # 逐行註解：放入文字抽取結果，沒有時填無。
    ]  # 逐行註解：結束 prompt 清單。
    return "\n".join(lines).strip()  # 逐行註解：回傳最終 PDF 視覺摘要 prompt。


async def maybe_report_progress(progress_cb, text: str):  # 逐行註解：如果呼叫端提供進度 callback，就更新目前附件分析進度。
    if progress_cb is not None:  # 逐行註解：只有有傳入 callback 時才需要更新進度。
        await progress_cb(text)  # 逐行註解：把最新進度交給呼叫端顯示在 Thinking 訊息上。


async def analyze_pdf_pages_with_gemma4(model: str, filename: str, pdf_bytes: bytes, page_numbers: list[int], pdf_text: str, progress_cb=None) -> str:  # 逐行註解：用 Gemma4 vision 分析 PDF 圖片頁並整理成最終摘要。
    await maybe_report_progress(progress_cb, f"正在渲染 PDF 頁面：{filename}")  # 逐行註解：告訴使用者 PDF 正在轉成圖片頁。
    rendered_pages = await render_pdf_pages_to_images(pdf_bytes, page_numbers)  # 逐行註解：先把需要分析的 PDF 頁面渲染成圖片。
    if not rendered_pages:  # 逐行註解：如果沒有成功渲染任何頁面，就回傳提示。
        return "無法把 PDF 頁面轉成圖片，因此無法使用 Gemma4 視覺分析。"  # 逐行註解：告訴使用者渲染失敗。
    page_analyses: list[str] = []  # 逐行註解：建立每頁 Gemma4 視覺分析結果清單。
    for rendered in rendered_pages:  # 逐行註解：逐頁送給 Gemma4 vision 分析。
        page_number = int(rendered.get("page") or 0)  # 逐行註解：取得目前渲染圖片的頁碼。
        image_bytes = rendered.get("image_bytes") or b""  # 逐行註解：取得目前頁面的 PNG bytes。
        prompt = build_pdf_page_vision_prompt(filename, page_number)  # 逐行註解：建立單頁圖片分析 prompt。
        await maybe_report_progress(progress_cb, f"正在分析 PDF 第 {page_number} 頁：{filename}")  # 逐行註解：顯示目前正在分析的 PDF 頁碼。
        page_reply = await ask_ollama_vision(model, prompt, image_bytes, timeout_s=None)  # 逐行註解：呼叫 Gemma4 vision 分析這一頁。
        page_analyses.append(f"第 {page_number} 頁：\n{str(page_reply).strip()}")  # 逐行註解：把頁碼和分析結果放進清單。
    await maybe_report_progress(progress_cb, f"正在整理 PDF 分析結果：{filename}")  # 逐行註解：告訴使用者頁面分析完成，正在彙整摘要。
    summary_prompt = build_pdf_vision_summary_prompt(filename, page_analyses, pdf_text)  # 逐行註解：建立整份 PDF 的最終摘要 prompt。
    return str(await ask_ollama_text(model, summary_prompt, timeout_s=None)).strip()  # 逐行註解：用同一個 Gemma4 模型整理最終摘要。


def format_pdf_image_detection_message(inspect_result: dict, model: str) -> str:  # 逐行註解：建立 PDF 偵測到圖片頁時要顯示給使用者的提示文字。
    pages = inspect_result.get("needs_vision_pages") or inspect_result.get("image_pages") or []  # 逐行註解：優先顯示需要視覺分析的頁碼，沒有就顯示含圖片頁。
    page_text = ", ".join(str(page) for page in pages[:20]) or "未知"  # 逐行註解：把頁碼整理成一行文字，最多顯示前 20 頁。
    extra = "，還有更多頁" if len(pages) > 20 else ""  # 逐行註解：如果頁數太多，就提醒還有更多頁沒有列出。
    lines = [  # 逐行註解：用清單組成 Discord 提示文字。
        "偵測到這份 PDF 含有圖片頁或掃描頁。",  # 逐行註解：說明為什麼暫停文字摘要流程。
        f"需要視覺分析的頁面：{page_text}{extra}",  # 逐行註解：列出需要 Gemma4 看圖的頁碼。
        f"目前文字摘要模型：{model}",  # 逐行註解：顯示目前使用者選的文字模型。
        f"是否要改用 {PDF_GEMMA4_VISION_MODEL} 分析 PDF 圖片頁？",  # 逐行註解：詢問使用者是否切到 Gemma4 視覺分析。
    ]  # 逐行註解：結束提示文字清單。
    return "\n".join(lines)  # 逐行註解：回傳完整提示文字。


class PdfVisionConfirmView(discord.ui.View):  # 逐行註解：建立 PDF 圖片頁確認用的 Discord 按鈕 View。
    def __init__(self, user_id: int):  # 逐行註解：初始化 View，記住允許按按鈕的使用者 ID。
        super().__init__(timeout=120)  # 逐行註解：設定按鈕 120 秒後自動失效。
        self.user_id = user_id  # 逐行註解：保存 slash command 發起人的 Discord user id。
        self.confirmed: bool | None = None  # 逐行註解：保存使用者是否同意改用 Gemma4 vision。

    async def interaction_check(self, interaction: discord.Interaction) -> bool:  # 逐行註解：限制只有原本使用者可以按這組按鈕。
        if interaction.user.id != self.user_id:  # 逐行註解：如果按鈕使用者不是原本執行 /pdf 的人，就拒絕。
            await interaction.response.send_message("這不是你的 PDF 分析確認按鈕。", ephemeral=True)  # 逐行註解：提示其他使用者不能操作。
            return False  # 逐行註解：拒絕這次按鈕互動。
        return True  # 逐行註解：允許原本使用者操作按鈕。

    @discord.ui.button(label="改用 Gemma4 分析圖片", style=discord.ButtonStyle.primary)  # 逐行註解：建立同意切換 Gemma4 vision 的按鈕。
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):  # 逐行註解：處理使用者按下同意按鈕。
        self.confirmed = True  # 逐行註解：記錄使用者同意改用 Gemma4 vision。
        for child in self.children:  # 逐行註解：按下後停用所有按鈕，避免重複點擊。
            child.disabled = True  # 逐行註解：停用這個按鈕元件。
        await interaction.response.edit_message(content="已切換為 Gemma4 圖片分析，正在處理 PDF。", view=self)  # 逐行註解：更新原本確認訊息。
        self.stop()  # 逐行註解：結束 View 等待，讓 /pdf 流程繼續。

    @discord.ui.button(label="取消", style=discord.ButtonStyle.secondary)  # 逐行註解：建立取消按鈕。
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):  # 逐行註解：處理使用者按下取消按鈕。
        self.confirmed = False  # 逐行註解：記錄使用者取消 Gemma4 vision。
        for child in self.children:  # 逐行註解：按下後停用所有按鈕。
            child.disabled = True  # 逐行註解：停用這個按鈕元件。
        await interaction.response.edit_message(content="已取消 PDF 圖片分析。", view=self)  # 逐行註解：更新原本確認訊息。
        self.stop()  # 逐行註解：結束 View 等待，讓 /pdf 流程停止。


def attachment_extension(filename: str) -> str:  # 逐行註解：取得附件副檔名，讓檔案類型判斷集中管理。
    return Path(filename or "").suffix.lower()  # 逐行註解：用 Path 取得小寫副檔名，沒有副檔名時回空字串。


def is_image_attachment_meta(filename: str, content_type: str) -> bool:  # 逐行註解：判斷附件是否為圖片，圖片需要 Gemma4 vision。
    ext = attachment_extension(filename)  # 逐行註解：取得附件副檔名。
    return (content_type or "").lower().startswith("image/") or ext in IMAGE_ATTACHMENT_EXTENSIONS  # 逐行註解：Content-Type 或副檔名任一符合圖片就算圖片。


def is_pdf_attachment_meta(filename: str, content_type: str) -> bool:  # 逐行註解：判斷附件是否為 PDF，PDF 會自動抽文字或渲染圖片頁。
    ext = attachment_extension(filename)  # 逐行註解：取得附件副檔名。
    return ext == ".pdf" or "pdf" in (content_type or "").lower()  # 逐行註解：副檔名或 Content-Type 顯示 PDF 就算 PDF。


def is_video_attachment_meta(filename: str, content_type: str) -> bool:  # 逐行註解：判斷附件是否為影片，影片目前不直接下載分析。
    ext = attachment_extension(filename)  # 逐行註解：取得附件副檔名。
    return (content_type or "").lower().startswith("video/") or ext in VIDEO_ATTACHMENT_EXTENSIONS  # 逐行註解：Content-Type 或副檔名任一符合影片就算影片。


def is_office_attachment_meta(filename: str) -> bool:  # 逐行註解：判斷附件是否為常見 Office 檔，可用 zip+xml 讀文字。
    ext = attachment_extension(filename)  # 逐行註解：取得附件副檔名。
    return ext in OFFICE_ATTACHMENT_EXTENSIONS  # 逐行註解：支援新版與舊版 Word、PowerPoint、Excel，以及 RTF/ODT。


def decode_plain_text_bytes(file_bytes: bytes) -> str:  # 逐行註解：把一般文字附件 bytes 解碼成字串。
    sample = (file_bytes or b"")[:4096]  # 逐行註解：先取前段樣本判斷是否像二進位檔。
    if b"\x00" in sample:  # 逐行註解：含有大量 NUL 的檔案通常不是純文字。
        return ""  # 逐行註解：回空字串，交給呼叫端回覆無法直接讀取。
    for encoding in ("utf-8-sig", "utf-8", "cp950", "big5"):  # 逐行註解：依序嘗試常見繁中與 UTF-8 編碼。
        try:  # 逐行註解：單一編碼可能解碼失敗，所以用 try 保護。
            return (file_bytes or b"").decode(encoding).strip()  # 逐行註解：成功解碼就回傳文字。
        except UnicodeDecodeError:  # 逐行註解：這個編碼不適合時換下一個。
            continue  # 逐行註解：繼續嘗試下一種編碼。
    return ""  # 逐行註解：全部解碼失敗時回空字串。


def collect_xml_text(xml_bytes: bytes) -> str:  # 逐行註解：從 Office XML bytes 收集所有可見文字節點。
    try:  # 逐行註解：XML 可能損壞，所以用 try 保護解析。
        root = ET.fromstring(xml_bytes)  # 逐行註解：把 XML bytes 解析成 ElementTree。
    except Exception:  # 逐行註解：解析失敗時回空字串。
        return ""  # 逐行註解：讓呼叫端改用其他資料或提示無法讀取。
    texts: list[str] = []  # 逐行註解：建立文字節點清單。
    for element in root.iter():  # 逐行註解：走訪 XML 裡每一個節點。
        value = (element.text or "").strip()  # 逐行註解：取得節點文字並去除空白。
        if value:  # 逐行註解：只保留非空文字。
            texts.append(value)  # 逐行註解：把文字加入清單。
    return "\n".join(texts).strip()  # 逐行註解：用換行合併文字，保留大致閱讀順序。


def extract_docx_text(file_bytes: bytes) -> str:  # 逐行註解：從 docx 檔案抽取可見文字。
    texts: list[str] = []  # 逐行註解：建立 Word 文件文字清單。
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:  # 逐行註解：docx 本質是 zip，直接在記憶體打開。
        names = [name for name in archive.namelist() if name.startswith("word/") and name.endswith(".xml")]  # 逐行註解：讀取 Word 主要文件、表格、頁首頁尾 XML。
        for name in names:  # 逐行註解：逐一解析每個 Word XML。
            text = collect_xml_text(archive.read(name))  # 逐行註解：收集這個 XML 裡的文字。
            if text:  # 逐行註解：有文字才加入結果。
                texts.append(text)  # 逐行註解：把這段文字加入 Word 結果。
    return "\n\n".join(texts).strip()[:OFFICE_XML_TEXT_MAX_CHARS]  # 逐行註解：合併並限制文字量。


def extract_pptx_text(file_bytes: bytes) -> str:  # 逐行註解：從 pptx 簡報抽取投影片文字。
    slides: list[str] = []  # 逐行註解：建立投影片文字清單。
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:  # 逐行註解：pptx 本質是 zip，直接在記憶體打開。
        names = sorted(name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml"))  # 逐行註解：依檔名順序讀取每張投影片 XML。
        for index, name in enumerate(names, start=1):  # 逐行註解：逐張投影片抽文字並標上頁碼。
            text = collect_xml_text(archive.read(name))  # 逐行註解：收集這張投影片的文字。
            if text:  # 逐行註解：有文字才加入結果。
                slides.append(f"投影片 {index}：\n{text}")  # 逐行註解：保留投影片序號方便 AI 整理。
    return "\n\n".join(slides).strip()[:OFFICE_XML_TEXT_MAX_CHARS]  # 逐行註解：合併並限制文字量。


def extract_xlsx_text(file_bytes: bytes) -> str:  # 逐行註解：從 xlsx 試算表抽取儲存格文字與數值。
    rows: list[str] = []  # 逐行註解：建立試算表文字清單。
    shared_strings: list[str] = []  # 逐行註解：建立 Excel shared strings 清單。
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:  # 逐行註解：xlsx 本質是 zip，直接在記憶體打開。
        if "xl/sharedStrings.xml" in archive.namelist():  # 逐行註解：如果有 shared strings，就先解析文字表。
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))  # 逐行註解：解析 sharedStrings XML。
            for item in shared_root.iter():  # 逐行註解：走訪 shared strings 的所有節點。
                if item.tag.endswith("}t") or item.tag == "t":  # 逐行註解：只取文字節點 t。
                    shared_strings.append((item.text or "").strip())  # 逐行註解：加入 shared string 文字。
        sheet_names = sorted(name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))  # 逐行註解：依序讀取每張工作表。
        for sheet_index, sheet_name in enumerate(sheet_names, start=1):  # 逐行註解：逐張工作表抽取儲存格。
            sheet_root = ET.fromstring(archive.read(sheet_name))  # 逐行註解：解析工作表 XML。
            cell_values: list[str] = []  # 逐行註解：建立目前工作表的儲存格值清單。
            for cell in sheet_root.iter():  # 逐行註解：走訪所有 XML 節點。
                if not cell.tag.endswith("}c") and cell.tag != "c":  # 逐行註解：只處理儲存格 c 節點。
                    continue  # 逐行註解：不是儲存格就跳過。
                cell_type = cell.attrib.get("t", "")  # 逐行註解：取得儲存格型別。
                raw_value = ""  # 逐行註解：建立儲存格原始值。
                for child in cell:  # 逐行註解：讀取儲存格子節點。
                    if child.tag.endswith("}v") or child.tag == "v":  # 逐行註解：v 節點是一般值或 shared string index。
                        raw_value = (child.text or "").strip()  # 逐行註解：保存 v 節點文字。
                    if child.tag.endswith("}is") or child.tag == "is":  # 逐行註解：is 節點代表 inline string。
                        raw_value = collect_xml_text(ET.tostring(child, encoding="utf-8"))  # 逐行註解：收集 inline string 文字。
                if cell_type == "s" and raw_value.isdigit() and int(raw_value) < len(shared_strings):  # 逐行註解：shared string index 轉成真正文字。
                    raw_value = shared_strings[int(raw_value)]  # 逐行註解：用 shared string 文字替換 index。
                if raw_value:  # 逐行註解：只保留非空儲存格。
                    cell_values.append(raw_value)  # 逐行註解：加入目前工作表的值清單。
            if cell_values:  # 逐行註解：工作表有內容才加入結果。
                rows.append(f"工作表 {sheet_index}：\n" + "\n".join(cell_values[:500]))  # 逐行註解：每張表最多保留前 500 格，避免超長。
    return "\n\n".join(rows).strip()[:OFFICE_XML_TEXT_MAX_CHARS]  # 逐行註解：合併並限制文字量。


def extract_text_with_textutil(filename: str, file_bytes: bytes) -> str:  # 逐行註解：使用 macOS textutil 嘗試把舊 Office、RTF、ODT 轉成文字。
    textutil_path = shutil.which("textutil")  # 逐行註解：尋找 macOS textutil 指令位置。
    if not textutil_path:  # 逐行註解：如果系統沒有 textutil，就不能使用這個轉換方式。
        return ""  # 逐行註解：回傳空字串，交給下一層備援。
    ext = attachment_extension(filename) or ".bin"  # 逐行註解：取得副檔名，沒有副檔名時使用 .bin。
    temp_path = Path(tempfile.gettempdir()) / f"discord_upload_{uuid.uuid4().hex}{ext}"  # 逐行註解：建立安全的暫存檔路徑，避免檔名衝突。
    try:  # 逐行註解：暫存檔與外部指令都可能失敗，所以用 try 保護。
        temp_path.write_bytes(file_bytes or b"")  # 逐行註解：把 Discord 附件 bytes 寫入暫存檔供 textutil 讀取。
        result = subprocess.run(  # 逐行註解：執行 textutil 轉文字。
            [textutil_path, "-convert", "txt", "-stdout", str(temp_path)],  # 逐行註解：要求 textutil 把檔案轉成純文字並輸出到 stdout。
            capture_output=True,  # 逐行註解：捕捉 stdout 與 stderr，避免輸出直接跑到終端機。
            timeout=20,  # 逐行註解：限制轉換最多 20 秒，避免卡住 bot。
        )  # 逐行註解：結束 subprocess.run 呼叫。
        if result.returncode != 0:  # 逐行註解：textutil 轉換失敗時不要使用結果。
            return ""  # 逐行註解：回空字串，交給二進位文字備援。
        return (result.stdout or b"").decode("utf-8", errors="replace").strip()[:OFFICE_XML_TEXT_MAX_CHARS]  # 逐行註解：把 stdout 解碼成文字並限制長度。
    except Exception as e:  # 逐行註解：捕捉 textutil 或暫存檔錯誤。
        print(f"textutil 讀取檔案失敗：{filename} {type(e).__name__}: {e}")  # 逐行註解：把失敗原因印到後台方便排查。
        return ""  # 逐行註解：回空字串，交給下一層備援。
    finally:  # 逐行註解：不管成功失敗都清理暫存檔。
        try:  # 逐行註解：刪除暫存檔也可能遇到權限或不存在。
            temp_path.unlink(missing_ok=True)  # 逐行註解：刪除暫存檔，避免累積使用者附件。
        except Exception as e:  # 逐行註解：捕捉清理失敗。
            print(f"暫存附件刪除失敗：{temp_path} {type(e).__name__}: {e}")  # 逐行註解：把清理失敗原因印到後台。


def extract_binary_strings_text(file_bytes: bytes) -> str:  # 逐行註解：從未知或舊版二進位檔抽出可讀文字片段作為最後備援。
    if not file_bytes:  # 逐行註解：空檔案沒有可抽文字。
        return ""  # 逐行註解：回傳空字串。
    decoded_sources = [  # 逐行註解：準備不同解碼角度，增加抓到舊檔文字的機率。
        file_bytes.decode("utf-8", errors="ignore"),  # 逐行註解：用 UTF-8 忽略錯誤解碼。
        file_bytes.decode("utf-16le", errors="ignore"),  # 逐行註解：用 UTF-16LE 抓舊 Office 常見寬字元文字。
        file_bytes.decode("latin-1", errors="ignore"),  # 逐行註解：用 latin-1 作為最後保底，保留單位元組可見字元。
    ]  # 逐行註解：結束解碼來源清單。
    lines: list[str] = []  # 逐行註解：建立可讀文字片段清單。
    seen: set[str] = set()  # 逐行註解：建立去重集合，避免同一段文字重複很多次。
    for decoded in decoded_sources:  # 逐行註解：逐一處理每種解碼結果。
        candidates = re.findall(r"[^\x00-\x08\x0b\x0c\x0e-\x1f\x7f]{4,}", decoded)  # 逐行註解：找出長度至少 4 的可見字元片段。
        for candidate in candidates:  # 逐行註解：逐一整理可見字元片段。
            cleaned = " ".join(candidate.split()).strip()  # 逐行註解：壓掉多餘空白與換行。
            if len(cleaned) < 4:  # 逐行註解：太短的片段通常沒有分析價值。
                continue  # 逐行註解：跳過短片段。
            if not re.search(r"[A-Za-z0-9\u4e00-\u9fff]", cleaned):  # 逐行註解：沒有英數或中文的片段多半是二進位雜訊。
                continue  # 逐行註解：跳過雜訊片段。
            if cleaned in seen:  # 逐行註解：同一段文字已經加入過就不要重複。
                continue  # 逐行註解：跳過重複片段。
            seen.add(cleaned)  # 逐行註解：記錄這段文字已加入。
            lines.append(cleaned)  # 逐行註解：加入可讀文字清單。
            if sum(len(line) for line in lines) >= OFFICE_XML_TEXT_MAX_CHARS:  # 逐行註解：累積文字達上限就停止。
                return "\n".join(lines).strip()[:OFFICE_XML_TEXT_MAX_CHARS]  # 逐行註解：回傳限制後文字。
    return "\n".join(lines).strip()[:OFFICE_XML_TEXT_MAX_CHARS]  # 逐行註解：回傳所有抽到的文字片段。


def extract_office_text(filename: str, file_bytes: bytes) -> str:  # 逐行註解：依 Office 副檔名選擇對應文字抽取器。
    ext = attachment_extension(filename)  # 逐行註解：取得附件副檔名。
    try:  # 逐行註解：Office 檔可能損壞，所以用 try 保護。
        if ext == ".docx":  # 逐行註解：Word 文件走 docx 抽取。
            return extract_docx_text(file_bytes)  # 逐行註解：回傳 Word 文字。
        if ext == ".pptx":  # 逐行註解：PowerPoint 簡報走 pptx 抽取。
            return extract_pptx_text(file_bytes)  # 逐行註解：回傳簡報文字。
        if ext == ".xlsx":  # 逐行註解：Excel 試算表走 xlsx 抽取。
            return extract_xlsx_text(file_bytes)  # 逐行註解：回傳試算表文字。
    except Exception as e:  # 逐行註解：抽取失敗時印到後台，不讓整個 bot 崩潰。
        print(f"Office 檔案讀取失敗：{filename} {type(e).__name__}: {e}")  # 逐行註解：記錄失敗檔名與錯誤。
    textutil_text = extract_text_with_textutil(filename, file_bytes)  # 逐行註解：新版抽取失敗或舊版 Office 時，嘗試用 macOS textutil。
    if textutil_text:  # 逐行註解：如果 textutil 有讀到文字，就直接使用。
        return textutil_text  # 逐行註解：回傳 textutil 轉出的文字。
    return extract_binary_strings_text(file_bytes)  # 逐行註解：最後用二進位可讀字串備援，支援舊 .doc/.ppt/.xls 的部分文字。


def extract_readable_attachment_text(filename: str, content_type: str, file_bytes: bytes) -> str:  # 逐行註解：從非 PDF、非圖片附件抽取可送給 AI 的文字。
    ext = attachment_extension(filename)  # 逐行註解：取得附件副檔名。
    if is_office_attachment_meta(filename):  # 逐行註解：Office 檔案使用 zip+xml 抽文字。
        return extract_office_text(filename, file_bytes)  # 逐行註解：回傳 Office 抽取結果。
    if ext in READABLE_TEXT_EXTENSIONS or (content_type or "").lower().startswith("text/"):  # 逐行註解：文字、程式碼或 text/* Content-Type 直接解碼。
        return decode_plain_text_bytes(file_bytes)[:UPLOADED_FILE_TEXT_MAX_CHARS]  # 逐行註解：解碼並限制文字量。
    decoded = decode_plain_text_bytes(file_bytes)  # 逐行註解：未知副檔名也嘗試當文字讀取。
    if decoded:  # 逐行註解：如果未知檔案可以直接解碼成文字，就使用它。
        return decoded[:UPLOADED_FILE_TEXT_MAX_CHARS]  # 逐行註解：回傳限制長度後的文字。
    return extract_binary_strings_text(file_bytes)[:UPLOADED_FILE_TEXT_MAX_CHARS]  # 逐行註解：最後用二進位可讀字串備援，讓更多未知檔案也能被分析。


def build_uploaded_text_file_prompt(filename: str, extracted_text: str, user_text: str) -> str:  # 逐行註解：建立一般文字附件分析 prompt。
    clipped_text = (extracted_text or "").strip()[:UPLOADED_FILE_TEXT_MAX_CHARS]  # 逐行註解：限制附件文字長度。
    user_note = (user_text or "").strip() or "請分析這個檔案。"  # 逐行註解：保留使用者附加訊息，沒有就用預設分析需求。
    lines = [  # 逐行註解：用清單組 prompt，方便維持每行註解。
        "使用者上傳了一個檔案，請直接閱讀並分析。",  # 逐行註解：說明任務類型。
        f"檔名：{filename}",  # 逐行註解：提供原始檔名。
        f"使用者附加訊息：{user_note}",  # 逐行註解：提供使用者對附件的要求。
        "請一定使用繁體中文回答。",  # 逐行註解：指定輸出繁體中文。
        "請整理檔案內容、重點、可能問題，以及使用者可能需要知道的資訊。",  # 逐行註解：指定分析方向。
        "如果檔案內容適合做比較、趨勢、比例或統計視覺化，請改用下方圖表 JSON 規則輸出。",  # 逐行註解：讓一般附件分析也能觸發即時圖表。
        chart_output_rules_prompt(),  # 逐行註解：加入可被程式端解析的圖表 JSON 規則。
        "",  # 逐行註解：加入空行讓 prompt 易讀。
        "檔案文字內容如下：",  # 逐行註解：標示後面是附件內容。
        clipped_text or "（沒有讀到文字）",  # 逐行註解：放入抽取文字，沒有時明確標記。
    ]  # 逐行註解：結束 prompt 清單。
    return "\n".join(lines).strip()  # 逐行註解：回傳完整 prompt。


def build_uploaded_image_prompt(filename: str, user_text: str) -> str:  # 逐行註解：建立圖片附件分析 prompt。
    user_note = (user_text or "").strip() or "請分析這張圖片。"  # 逐行註解：保留使用者附加訊息，沒有就用預設看圖需求。
    lines = [  # 逐行註解：用清單組 vision prompt。
        "使用者上傳了一張圖片，請直接看圖分析。",  # 逐行註解：說明任務類型。
        f"檔名：{filename}",  # 逐行註解：提供圖片檔名。
        f"使用者附加訊息：{user_note}",  # 逐行註解：提供使用者對圖片的要求。
        "請一定使用繁體中文回答。",  # 逐行註解：指定輸出繁體中文。
        "請描述圖片內容、讀取可見文字、整理重點，並回答使用者附加訊息。",  # 逐行註解：指定看圖分析方向。
        "如果圖片中有可量化資料並適合重新畫成圖表，請改用下方圖表 JSON 規則輸出。",  # 逐行註解：讓圖片分析遇到表格或數值時也能觸發程式繪圖。
        chart_output_rules_prompt(),  # 逐行註解：加入可被程式端解析的圖表 JSON 規則。
    ]  # 逐行註解：結束 prompt 清單。
    return "\n".join(lines).strip()  # 逐行註解：回傳完整 vision prompt。


async def prepare_uploaded_attachments(attachments: list[discord.Attachment], progress_cb=None) -> list[dict]:  # 逐行註解：下載並初步分析 Discord 附件，後面可直接交給 AI。
    prepared: list[dict] = []  # 逐行註解：建立已準備附件清單。
    total = len(attachments or [])  # 逐行註解：計算附件總數，讓進度可以顯示第幾個檔案。
    for index, attachment in enumerate(attachments, start=1):  # 逐行註解：逐一處理使用者上傳的附件。
        filename = (attachment.filename or "未命名檔案").strip()  # 逐行註解：取得附件檔名。
        content_type = (attachment.content_type or "").lower()  # 逐行註解：取得附件 Content-Type。
        await maybe_report_progress(progress_cb, f"正在檢查檔案 {index}/{total}：{filename}")  # 逐行註解：顯示目前正在檢查的附件。
        if is_video_attachment_meta(filename, content_type):  # 逐行註解：影片檔目前不能直接分析，也不要下載整個影片。
            prepared.append({"filename": filename, "content_type": content_type, "bytes": b"", "kind": "video"})  # 逐行註解：只保存影片檔名與類型，後續回覆限制提示。
            continue  # 逐行註解：跳過下載影片附件。
        await maybe_report_progress(progress_cb, f"正在下載檔案 {index}/{total}：{filename}")  # 逐行註解：顯示正在從 Discord 下載附件。
        file_bytes = await attachment.read()  # 逐行註解：從 Discord 下載附件 bytes 到記憶體。
        item = {"filename": filename, "content_type": content_type, "bytes": file_bytes, "kind": "unknown"}  # 逐行註解：建立附件描述資料。
        if is_image_attachment_meta(filename, content_type):  # 逐行註解：圖片需要 Gemma4 vision。
            item["kind"] = "image"  # 逐行註解：標記為圖片附件。
        elif is_pdf_attachment_meta(filename, content_type):  # 逐行註解：PDF 先抽文字並檢查圖片頁。
            item["kind"] = "pdf"  # 逐行註解：標記為 PDF 附件。
            await maybe_report_progress(progress_cb, f"正在讀取 PDF 文字：{filename}")  # 逐行註解：顯示正在抽取 PDF 文字。
            item["pdf_text"] = await extract_pdf_text(file_bytes)  # 逐行註解：抽取 PDF 文字。
            await maybe_report_progress(progress_cb, f"正在檢查 PDF 圖片頁：{filename}")  # 逐行註解：顯示正在偵測 PDF 是否有圖片或掃描頁。
            item["pdf_inspect"] = await inspect_pdf_images(file_bytes)  # 逐行註解：檢查 PDF 是否含圖片頁或掃描頁。
        else:  # 逐行註解：其他檔案嘗試抽取文字或 Office 內容。
            item["kind"] = "text"  # 逐行註解：先標記為文字型附件。
            await maybe_report_progress(progress_cb, f"正在讀取檔案文字：{filename}")  # 逐行註解：顯示正在抽取一般檔案文字。
            item["text"] = extract_readable_attachment_text(filename, content_type, file_bytes)  # 逐行註解：嘗試取得附件文字內容。
        prepared.append(item)  # 逐行註解：把準備好的附件加入清單。
    return prepared  # 逐行註解：回傳所有已準備附件。


def attachment_item_needs_gemma4(item: dict) -> bool:  # 逐行註解：判斷單一附件是否需要 Gemma4 vision。
    if item.get("kind") == "image":  # 逐行註解：圖片檔一定需要視覺模型。
        return True  # 逐行註解：回傳需要 Gemma4。
    if item.get("kind") == "pdf":  # 逐行註解：PDF 要看是否含圖片頁或掃描頁。
        inspect_result = item.get("pdf_inspect") or {}  # 逐行註解：取得 PDF 圖片偵測結果。
        return bool(inspect_result.get("image_pages") or inspect_result.get("needs_vision_pages"))  # 逐行註解：有圖片頁或需要視覺分析頁就回 True。
    return False  # 逐行註解：其他檔案不需要 Gemma4 vision。


def format_attachment_gemma_switch_message(items: list[dict], model: str) -> str:  # 逐行註解：建立附件需要切換 Gemma4 的確認訊息。
    filenames = [str(item.get("filename") or "未命名檔案") for item in items if attachment_item_needs_gemma4(item)]  # 逐行註解：整理需要 Gemma4 的附件檔名。
    shown = "\n".join(f"- {name}" for name in filenames[:10]) or "- 未知附件"  # 逐行註解：最多列出前 10 個附件名稱。
    extra = "\n- 還有更多附件..." if len(filenames) > 10 else ""  # 逐行註解：附件太多時補上省略提示。
    lines = [  # 逐行註解：用清單組 Discord 按鈕前提示。
        "偵測到你上傳的檔案需要圖片理解能力。",  # 逐行註解：說明為什麼詢問切換模型。
        f"目前模型：{model}",  # 逐行註解：顯示目前模型。
        f"是否要切換成 {PDF_GEMMA4_VISION_MODEL} 來分析以下檔案？",  # 逐行註解：詢問使用者是否切換 Gemma4。
        shown + extra,  # 逐行註解：列出需要 Gemma4 的附件。
    ]  # 逐行註解：結束提示清單。
    return "\n".join(lines)  # 逐行註解：回傳完整提示。


class AttachmentGemmaSwitchView(discord.ui.View):  # 逐行註解：建立附件分析切換 Gemma4 的確認按鈕。
    def __init__(self, user_id: int):  # 逐行註解：初始化 View，記住原本上傳附件的使用者。
        super().__init__(timeout=120)  # 逐行註解：按鈕等待 120 秒後逾時。
        self.user_id = user_id  # 逐行註解：保存可操作按鈕的 Discord user id。
        self.confirmed: bool | None = None  # 逐行註解：保存使用者是否同意切換 Gemma4。

    async def interaction_check(self, interaction: discord.Interaction) -> bool:  # 逐行註解：限制只有原本使用者能按這組按鈕。
        if interaction.user.id != self.user_id:  # 逐行註解：如果按鈕使用者不是原本附件上傳者，就拒絕。
            await interaction.response.send_message("這不是你的檔案分析確認按鈕。", ephemeral=True)  # 逐行註解：提醒其他使用者不能代按。
            return False  # 逐行註解：拒絕互動。
        return True  # 逐行註解：原本使用者可以操作。

    @discord.ui.button(label="是，切換 gemma4_thinking", style=discord.ButtonStyle.primary)  # 逐行註解：建立同意切換 Gemma4 的按鈕。
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):  # 逐行註解：處理使用者按下同意。
        self.confirmed = True  # 逐行註解：記錄使用者同意切換。
        dm_user_model[self.user_id] = PDF_GEMMA4_VISION_MODEL  # 逐行註解：按下是就把 DM 模型切成 gemma4_thinking。
        for child in self.children:  # 逐行註解：按下後停用所有按鈕。
            child.disabled = True  # 逐行註解：停用目前按鈕元件。
        await interaction.response.edit_message(content=f"已切換為 {PDF_GEMMA4_VISION_MODEL}，正在分析附件。", view=self)  # 逐行註解：更新確認訊息。
        self.stop()  # 逐行註解：結束 View 等待。

    @discord.ui.button(label="不要", style=discord.ButtonStyle.secondary)  # 逐行註解：建立不同意切換的按鈕。
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):  # 逐行註解：處理使用者按下不要。
        self.confirmed = False  # 逐行註解：記錄使用者不同意切換。
        for child in self.children:  # 逐行註解：按下後停用所有按鈕。
            child.disabled = True  # 逐行註解：停用目前按鈕元件。
        await interaction.response.edit_message(content="已取消 Gemma4 圖片分析，會略過需要看圖的檔案。", view=self)  # 逐行註解：更新確認訊息。
        self.stop()  # 逐行註解：結束 View 等待。


async def maybe_switch_to_gemma4_for_attachments(message: discord.Message, selected_model: str, items: list[dict], progress_cb=None) -> tuple[str, bool]:  # 逐行註解：附件需要視覺能力時詢問是否切換 Gemma4。
    if is_gemma4_model(selected_model):  # 逐行註解：目前已經是 Gemma4 系列就不用詢問。
        return selected_model, True  # 逐行註解：回傳原模型並允許視覺分析。
    if not any(attachment_item_needs_gemma4(item) for item in items):  # 逐行註解：沒有圖片或圖片 PDF 時不需要切換。
        return selected_model, False  # 逐行註解：回傳原模型且不需要視覺分析。
    view = AttachmentGemmaSwitchView(message.author.id)  # 逐行註解：建立只有上傳者能按的確認按鈕。
    await maybe_report_progress(progress_cb, f"等待是否切換成 {PDF_GEMMA4_VISION_MODEL}")  # 逐行註解：顯示目前正在等使用者決定是否切換模型。
    await message.channel.send(format_attachment_gemma_switch_message(items, selected_model), view=view)  # 逐行註解：送出是否切換 Gemma4 的確認訊息。
    await view.wait()  # 逐行註解：等待使用者按下是、不要，或逾時。
    if view.confirmed is True:  # 逐行註解：使用者同意切換時。
        await maybe_report_progress(progress_cb, f"已切換為 {PDF_GEMMA4_VISION_MODEL}")  # 逐行註解：顯示模型已切換成功。
        return PDF_GEMMA4_VISION_MODEL, True  # 逐行註解：回傳 gemma4_thinking 並允許視覺分析。
    await maybe_report_progress(progress_cb, "未切換 Gemma4，將略過需要圖片理解的檔案")  # 逐行註解：顯示使用者沒有切換模型的後續行為。
    return selected_model, False  # 逐行註解：不同意或逾時時不做視覺分析。


async def analyze_prepared_attachment(item: dict, model: str, user_text: str, allow_vision: bool, timeout_s: int | None, progress_cb=None) -> tuple[str, str]:  # 逐行註解：分析單一已準備附件並回傳回答與 thinking。
    filename = str(item.get("filename") or "未命名檔案")  # 逐行註解：取得附件檔名。
    kind = str(item.get("kind") or "unknown")  # 逐行註解：取得附件種類。
    file_bytes = item.get("bytes") or b""  # 逐行註解：取得附件 bytes。
    if kind == "video":  # 逐行註解：影片檔目前無法直接讀取內容。
        await maybe_report_progress(progress_cb, f"略過影片檔：{filename}")  # 逐行註解：顯示影片檔會被略過。
        return "影片檔目前無法直接讀取或摘要；請提供字幕、逐字稿、截圖，或使用 /youtube 處理 YouTube 影片。", ""  # 逐行註解：回覆影片限制。
    if kind == "image":  # 逐行註解：圖片附件走 Gemma4 vision。
        if not allow_vision or not is_gemma4_model(model):  # 逐行註解：沒有切換 Gemma4 時略過圖片。
            await maybe_report_progress(progress_cb, f"略過圖片檔：{filename}")  # 逐行註解：顯示圖片因未切換 Gemma4 而略過。
            return "這是圖片檔，需要切換 gemma4_thinking 才能分析。", ""  # 逐行註解：提醒需要視覺模型。
        prompt = build_uploaded_image_prompt(filename, user_text)  # 逐行註解：建立圖片分析 prompt。
        await maybe_report_progress(progress_cb, f"正在分析圖片：{filename}")  # 逐行註解：顯示正在分析圖片附件。
        reply, thinking_process = await ask_ollama_vision(model, prompt, file_bytes, timeout_s=timeout_s, include_thinking=True)  # 逐行註解：用 Gemma4 vision 分析圖片。
        return str(reply).strip(), str(thinking_process).strip()  # 逐行註解：回傳圖片分析結果。
    if kind == "pdf":  # 逐行註解：PDF 附件走文字抽取或 Gemma4 頁面圖片分析。
        pdf_text = str(item.get("pdf_text") or "")  # 逐行註解：取得 PDF 抽取文字。
        inspect_result = item.get("pdf_inspect") or {}  # 逐行註解：取得 PDF 圖片偵測結果。
        image_pages = inspect_result.get("image_pages") or []  # 逐行註解：取得所有含圖片頁。
        needs_vision_pages = inspect_result.get("needs_vision_pages") or []  # 逐行註解：取得需要視覺分析頁。
        if image_pages or needs_vision_pages:  # 逐行註解：PDF 含圖片或掃描頁時優先使用 Gemma4。
            if allow_vision and is_gemma4_model(model):  # 逐行註解：使用者同意切換或本來就是 Gemma4 時直接分析圖片頁。
                pages_to_analyze = needs_vision_pages or image_pages  # 逐行註解：優先分析需要視覺頁，否則分析所有含圖片頁。
                reply = await analyze_pdf_pages_with_gemma4(model, filename, file_bytes, pages_to_analyze, pdf_text, progress_cb=progress_cb)  # 逐行註解：把 PDF 頁面渲染成圖後交給 Gemma4，並顯示逐頁進度。
                return str(reply).strip(), ""  # 逐行註解：回傳 PDF 視覺分析結果。
            if len(pdf_text.strip()) < 30:  # 逐行註解：沒有切換 Gemma4 且文字很少時無法可靠分析。
                await maybe_report_progress(progress_cb, f"略過圖片 PDF：{filename}")  # 逐行註解：顯示 PDF 因未切換 Gemma4 而略過。
                return "此 PDF 可能是掃描檔或圖片頁；未切換 gemma4_thinking，所以目前無法直接讀取內容。", ""  # 逐行註解：回覆限制原因。
        if len(pdf_text.strip()) < 30:  # 逐行註解：文字太少且沒有可用視覺頁時視為讀不到。
            await maybe_report_progress(progress_cb, f"PDF 文字不足：{filename}")  # 逐行註解：顯示 PDF 沒有足夠可抽取文字。
            return "此 PDF 可能為掃描檔，或內容無法直接抽取文字。", ""  # 逐行註解：回覆 PDF 文字抽取失敗。
        prompt = build_pdf_analysis_prompt(filename, pdf_text)  # 逐行註解：建立 PDF 文字分析 prompt。
        await maybe_report_progress(progress_cb, f"正在分析 PDF 文字：{filename}")  # 逐行註解：顯示正在分析 PDF 抽取出的文字。
        reply, thinking_process = await ask_ollama_text(model, prompt, timeout_s=timeout_s, include_thinking=True)  # 逐行註解：用目前文字模型分析 PDF 文字。
        return str(reply).strip(), str(thinking_process).strip()  # 逐行註解：回傳 PDF 文字分析結果。
    extracted_text = str(item.get("text") or "")  # 逐行註解：取得一般附件抽取出的文字。
    if not extracted_text.strip():  # 逐行註解：如果沒有可讀文字，就提示目前無法直接分析。
        await maybe_report_progress(progress_cb, f"檔案沒有可讀文字：{filename}")  # 逐行註解：顯示目前附件沒有讀到文字內容。
        return "這個檔案不是可直接讀取的文字、PDF、圖片或新版 Office 檔，暫時無法分析內容。", ""  # 逐行註解：回覆不支援的檔案類型。
    prompt = build_uploaded_text_file_prompt(filename, extracted_text, user_text)  # 逐行註解：建立一般文字附件分析 prompt。
    await maybe_report_progress(progress_cb, f"正在分析檔案：{filename}")  # 逐行註解：顯示正在分析一般文字或 Office 檔。
    reply, thinking_process = await ask_ollama_text(model, prompt, timeout_s=timeout_s, include_thinking=True)  # 逐行註解：用目前文字模型分析附件文字。
    return str(reply).strip(), str(thinking_process).strip()  # 逐行註解：回傳附件分析結果。


async def analyze_message_attachments(message: discord.Message, selected_model: str, user_text: str, timeout_s: int | None, progress_cb=None, model_state: dict | None = None) -> tuple[str, str, str, str]:  # 逐行註解：分析一則 Discord 訊息裡的所有附件。
    text_model = selected_text_model_for_user(message.author.id) if selected_model == "x/flux2-klein:latest" else selected_model  # 逐行註解：如果目前選圖片生成模型，附件分析先退回可用文字模型。
    if model_state is not None:  # 逐行註解：如果呼叫端有提供可變模型狀態，就先同步成文字分析模型。
        model_state["model"] = text_model  # 逐行註解：讓 Thinking 動畫先顯示實際要用的文字模型。
    prepared_items = await prepare_uploaded_attachments(list(message.attachments or []), progress_cb=progress_cb)  # 逐行註解：下載並準備所有附件，同時更新讀檔進度。
    active_model, allow_vision = await maybe_switch_to_gemma4_for_attachments(message, text_model, prepared_items, progress_cb=progress_cb)  # 逐行註解：必要時詢問是否切換 Gemma4。
    if model_state is not None:  # 逐行註解：確認是否切換模型後，同步更新 Thinking 動畫模型狀態。
        model_state["model"] = active_model  # 逐行註解：按下是後，下一個動畫 frame 會顯示 gemma4_thinking。
    sections: list[str] = []  # 逐行註解：建立所有附件分析結果清單。
    thinking_parts: list[str] = []  # 逐行註解：建立所有附件分析 thinking 清單。
    attachment_infos: list[str] = []  # 逐行註解：建立後台 log 的附件資訊清單。
    total = len(prepared_items)  # 逐行註解：計算附件總數，方便顯示第幾個附件。
    for index, item in enumerate(prepared_items, start=1):  # 逐行註解：逐一分析每個附件。
        filename = str(item.get("filename") or "未命名檔案")  # 逐行註解：取得目前附件檔名。
        size = len(item.get("bytes") or b"")  # 逐行註解：取得目前附件大小。
        attachment_infos.append(f"{filename} ({size} bytes)")  # 逐行註解：加入後台 log 附件資訊。
        await maybe_report_progress(progress_cb, f"正在分析檔案 {index}/{total}：{filename}")  # 逐行註解：顯示目前正在分析第幾個附件。
        reply, thinking_process = await analyze_prepared_attachment(item, active_model, user_text, allow_vision, timeout_s, progress_cb=progress_cb)  # 逐行註解：分析目前附件並更新細節進度。
        sections.append(f"檔案：{filename}\n{reply or '（我沒有產生任何回覆）'}")  # 逐行註解：把檔名與分析結果合成一段。
        if thinking_process:  # 逐行註解：如果模型有回傳 thinking，就保存供暫時顯示。
            thinking_parts.append(thinking_process)  # 逐行註解：加入 thinking 清單。
    await maybe_report_progress(progress_cb, "檔案分析完成，正在準備回覆")  # 逐行註解：顯示所有附件分析結束，準備輸出最終回答。
    return "\n\n".join(sections).strip(), "\n\n".join(thinking_parts).strip(), active_model, "；".join(attachment_infos)  # 逐行註解：回傳總回答、thinking、實際模型與附件資訊。


def extract_youtube_video_id(url: str) -> str:  # 逐行註解：從一般 YouTube、Shorts、youtu.be 網址抽出 video id。
    raw_url = (url or "").strip()  # 逐行註解：整理輸入網址。
    parsed = urlparse.urlparse(raw_url)  # 逐行註解：用標準 URL parser 拆解網址。
    host = (parsed.netloc or "").lower().removeprefix("www.")  # 逐行註解：整理網域名稱，方便比對 youtube.com 與 youtu.be。
    if host == "youtu.be":  # 逐行註解：短網址格式是 youtu.be/<video_id>。
        return parsed.path.strip("/").split("/")[0]  # 逐行註解：取第一段 path 當影片 ID。
    if host.endswith("youtube.com"):  # 逐行註解：一般 YouTube 網址和 Shorts 都在 youtube.com。
        query_id = urlparse.parse_qs(parsed.query).get("v", [""])[0]  # 逐行註解：一般影片優先讀 query string 裡的 v。
        if query_id:  # 逐行註解：如果有 v 參數就直接回傳。
            return query_id  # 逐行註解：回傳一般影片 ID。
        parts = [part for part in parsed.path.split("/") if part]  # 逐行註解：把 path 切成片段，處理 Shorts 或 embed。
        if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:  # 逐行註解：支援 /shorts/<id>、/embed/<id>、/live/<id>。
            return parts[1]  # 逐行註解：回傳 path 第二段影片 ID。
    match = re.search(r"(?<![A-Za-z0-9_-])([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])", raw_url)  # 逐行註解：最後用 11 字元影片 ID regex 做備援。
    return match.group(1) if match else ""  # 逐行註解：有抓到就回傳，沒有就回空字串。


async def get_youtube_title(url: str) -> str:  # 逐行註解：用 yt-dlp 只讀影片 metadata，不下載整部影片。
    def _get_title() -> str:  # 逐行註解：yt-dlp 是同步工具，放到 thread 裡執行。
        import yt_dlp  # 逐行註解：延遲匯入 yt-dlp，避免只有 YouTube 功能需要時才載入。
        options = {"quiet": True, "skip_download": True, "noplaylist": True}  # 逐行註解：設定只讀單支影片 metadata，不下載影片。
        with yt_dlp.YoutubeDL(options) as ydl:  # 逐行註解：建立 yt-dlp 物件。
            info = ydl.extract_info(url, download=False)  # 逐行註解：只抽取影片資訊，明確不下載影片。
        return str((info or {}).get("title") or "未知標題")  # 逐行註解：回傳影片標題，沒有就用未知標題。
    return await asyncio.to_thread(_get_title)  # 逐行註解：把 yt-dlp 同步流程放進 thread。


async def get_youtube_transcript(video_id: str) -> tuple[str, str]:  # 逐行註解：取得 YouTube 字幕文字與使用的字幕語言。
    def _fetch_transcript() -> tuple[str, str]:  # 逐行註解：YouTube transcript API 是同步流程，放到 thread 裡執行。
        from youtube_transcript_api import YouTubeTranscriptApi  # 逐行註解：延遲匯入字幕 API，避免啟動時增加負擔。
        api = YouTubeTranscriptApi()  # 逐行註解：建立字幕 API 物件。
        transcript_list = api.list(video_id)  # 逐行註解：列出這支影片可用字幕。
        preferred_languages = ["zh-Hant", "zh-TW", "zh-HK", "zh", "zh-CN"]  # 逐行註解：優先繁體中文字幕，沒有才找其他中文字幕。
        transcript = None  # 逐行註解：保存最後選到的字幕物件。
        for language_code in preferred_languages:  # 逐行註解：依序嘗試偏好的中文字幕。
            try:  # 逐行註解：某些語言不存在時會丟例外，所以逐個保護。
                transcript = transcript_list.find_transcript([language_code])  # 逐行註解：尋找指定語言字幕。
                break  # 逐行註解：找到字幕就跳出迴圈。
            except Exception:  # 逐行註解：找不到這個語言就換下一個，不讓流程中斷。
                continue  # 逐行註解：繼續下一個字幕語言。
        if transcript is None:  # 逐行註解：如果沒有中文，就使用第一個可用字幕。
            for candidate in transcript_list:  # 逐行註解：逐一取出所有可用字幕。
                transcript = candidate  # 逐行註解：保存第一個可用字幕。
                break  # 逐行註解：只需要第一個可用字幕。
        if transcript is None:  # 逐行註解：如果完全沒有字幕，就主動丟錯。
            raise RuntimeError("no transcript")  # 逐行註解：讓呼叫端顯示無字幕提示。
        fetched = transcript.fetch()  # 逐行註解：真正抓取字幕內容。
        raw_items = fetched.to_raw_data()  # 逐行註解：轉成包含 text/start/duration 的原始資料。
        lines: list[str] = []  # 逐行註解：建立字幕文字清單。
        for item in raw_items:  # 逐行註解：逐段整理字幕。
            start_seconds = float(item.get("start") or 0)  # 逐行註解：取得字幕開始秒數。
            minutes = int(start_seconds // 60)  # 逐行註解：把秒數轉成分鐘。
            seconds = int(start_seconds % 60)  # 逐行註解：把秒數轉成秒。
            subtitle_text = " ".join(str(item.get("text") or "").split())  # 逐行註解：整理字幕文字，移除多餘空白。
            if subtitle_text:  # 逐行註解：如果這段字幕有文字才加入。
                lines.append(f"[{minutes:02d}:{seconds:02d}] {subtitle_text}")  # 逐行註解：保留時間軸，讓 Ollama 能整理時間軸重點。
        return "\n".join(lines), str(getattr(transcript, "language_code", "") or getattr(fetched, "language_code", "") or "未知")  # 逐行註解：回傳字幕文字和語言代碼。
    return await asyncio.to_thread(_fetch_transcript)  # 逐行註解：把同步字幕抓取流程放進 thread。


def build_youtube_summary_prompt(title: str, transcript_text: str, subtitle_language: str) -> str:  # 逐行註解：建立 YouTube 摘要要送給 Ollama 的 prompt。
    clipped_text = (transcript_text or "").strip()[:YOUTUBE_TRANSCRIPT_MAX_CHARS]  # 逐行註解：限制字幕長度，避免太長拖垮本機模型。
    _ = subtitle_language  # 逐行註解：保留字幕語言參數給後台或未來偵錯使用，但使用者輸出不顯示字幕語言。
    lines = [  # 逐行註解：用清單組 prompt，保持每行新增程式碼都有註解。
        "你正在分析 YouTube 影片內容。",  # 逐行註解：說明任務類型，但不要讓使用者端看到字幕字樣。
        f"影片標題：{title}",  # 逐行註解：提供影片標題。
        "下方逐字稿只是內部資料來源，禁止把逐字稿原文、字幕內容、字幕語言、字幕片段輸出給使用者。",  # 逐行註解：明確禁止模型顯示字幕或逐字稿。
        "請一定使用繁體中文回答。",  # 逐行註解：指定輸出語言。
        "請依照以下格式輸出：",  # 逐行註解：要求固定格式。
        "影片標題",  # 逐行註解：要求輸出標題。
        "100字摘要",  # 逐行註解：要求短摘要。
        "重點整理",  # 逐行註解：要求條列重點。
        "時間軸重點",  # 逐行註解：要求根據字幕時間整理重點。
        "",  # 逐行註解：加入空行分隔摘要格式與圖表規則。
        "如果影片資料適合用趨勢、比較、比例或統計圖呈現，請改用下方圖表 JSON 規則輸出。",  # 逐行註解：讓 YouTube 摘要也能觸發即時圖表。
        chart_output_rules_prompt(),  # 逐行註解：加入可被程式端解析的圖表 JSON 規則。
        "",  # 逐行註解：加入空行讓 prompt 易讀。
        "內部逐字稿資料如下，只能用來摘要，不可以原文顯示：",  # 逐行註解：標示後面資料只供摘要使用，不給使用者看。
        clipped_text,  # 逐行註解：放入整理後的字幕內容。
    ]  # 逐行註解：結束 prompt 清單。
    return "\n".join(lines).strip()  # 逐行註解：回傳完整 prompt。


#######################統一日誌記錄系統#######################
_hourly_forecast_error_shown = False  # 保存 hourly forecast 錯誤是否已顯示過，避免重複列印。


def sanitize_log_value(param_name: str, value: any) -> str:  # 根據參數名稱隱藏敏感值。
    sensitive_keywords = {"token", "key", "password", "secret", "api", "passwd", "pwd", "auth", "cookie", "credential", "private"}  # 定義敏感關鍵字。
    param_lower = str(param_name or "").lower()  # 轉小寫便於比對。
    for keyword in sensitive_keywords:  # 逐一檢查敏感關鍵字。
        if keyword in param_lower:  # 如果參數名包含敏感關鍵字。
            return "[已隱藏]"  # 隱藏該參數值。
    return str(value)  # 回傳原值。


def sanitize_params(params: dict) -> dict:  # 對字典中所有參數值進行隱藏敏感值。
    if not params:  # 如果參數字典為空。
        return {}  # 回傳空字典。
    return {key: sanitize_log_value(key, value) for key, value in params.items()}  # 逐一隱藏每個參數。


def format_params_for_log(params: dict) -> str:  # 把參數格式化為日誌用的項目符號清單。
    if not params:  # 如果無參數。
        return "填入資料：無"  # 回傳無參數標示。
    sanitized = sanitize_params(params)  # 先隱藏敏感值。
    lines = ["填入資料："]  # 開始組項目符號清單。
    for key, value in sanitized.items():  # 逐一組每一行。
        lines.append(f"- {key}：{value}")  # 加入項目符號。
    return "\n".join(lines)  # 回傳格式化清單。


def get_interaction_user_info(interaction: discord.Interaction) -> dict:  # 從 interaction 物件取得使用者資訊。
    return {  # 直接回傳包含使用者資訊的字典。
        "name": interaction.user.name,  # 使用者名稱。
        "global_name": interaction.user.global_name,  # 使用者全域名稱。
        "id": interaction.user.id,  # 使用者 ID。
    }


def log_tool_usage(interaction: discord.Interaction, tool_name: str, params: dict = None, model: str = None, success: bool = True, error: str = None, elapsed: float = None) -> None:  # 主日誌記錄函式。
    user_info = get_interaction_user_info(interaction)  # 取得使用者資訊。
    formatted_params = format_params_for_log(params or {})  # 格式化參數。
    model_str = model or "無"  # 若無模型就顯示無。
    status_str = "成功" if success else "失敗"  # 根據成功與否設定狀態。
    error_str = error or "無"  # 若無錯誤就顯示無。
    elapsed_str = f"{elapsed:.2f} 秒" if elapsed is not None else "未知"  # 格式化耗時。
    
    log_output = f"""＝＝＝＝＝＝＝＝＝＝＝工具使用紀錄＝＝＝＝＝＝＝＝＝＝＝
使用者名稱：{user_info['name']}
使用者帳號：{user_info['global_name']}
使用者ID：{user_info['id']}
工具：{tool_name}
{formatted_params}
模型：{model_str}
狀態：{status_str}
花費時間：{elapsed_str}
錯誤：{error_str}
＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝"""  # 組出日誌格式。
    print(log_output)  # 列印日誌。


@tree.command(name="remember", description="新增一筆永久記憶")  # 逐行註解：註冊 /remember slash command，用來寫入目前使用者自己的 JSON。
@discord.app_commands.describe(content="要儲存的永久記憶內容")  # 逐行註解：替 /remember 的 content 參數加上 Discord 顯示說明。
async def remember_command(interaction: discord.Interaction, content: str):  # 逐行註解：定義 /remember 指令，接收使用者要保存的內容。
    if not is_allowed_interaction_user(interaction):  # 逐行註解：新增永久記憶前依目前情境檢查權限，統一走 ALLOWED_USERS 與 SUPER_USERS。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限時回覆私人提醒。
        return  # 逐行註解：沒有權限就停止。
    cleaned_content = (content or "").strip()  # 逐行註解：整理使用者輸入的記憶內容。
    if not cleaned_content:  # 逐行註解：空內容不能寫進永久記憶。
        await interaction.response.send_message("請輸入要儲存的記憶內容。", ephemeral=True)  # 逐行註解：提示使用者補上內容。
        return  # 逐行註解：停止指令。
    memories = load_permanent_memories(interaction.user.id)  # 逐行註解：只讀取目前使用者自己的永久記憶檔。
    memory_id = next_permanent_memory_id(memories)  # 逐行註解：取得下一個可用編號。
    item = build_memory_json_item(memory_id, cleaned_content)  # 逐行註解：建立符合 memories JSON 格式的新記憶物件。
    memories.append(item)  # 逐行註解：把新記憶加入這位使用者自己的清單。
    save_permanent_memories(interaction.user.id, memories)  # 逐行註解：用 UTF-8 寫回這位使用者自己的 JSON 檔。
    reply = f"✅ 已寫入 memories JSON：\n{format_memory_json_code_block([item])}"  # 逐行註解：顯示和寫入格式一致。
    await send_interaction_text_chunks(interaction, reply, ephemeral=True)  # 逐行註解：送出結果，超過 Discord 長度時自動分段。


@tree.command(name="list", description="顯示我的永久記憶")  # 逐行註解：註冊 /list slash command，用 Embed 顯示目前使用者自己的記憶。
async def list_memories_command(interaction: discord.Interaction):  # 逐行註解：定義 /list 指令。
    if not is_allowed_interaction_user(interaction):  # 逐行註解：讀取永久記憶前依目前情境檢查權限，統一走 ALLOWED_USERS 與 SUPER_USERS。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限時回覆私人提醒。
        return  # 逐行註解：沒有權限就停止。
    memories = load_permanent_memories(interaction.user.id)  # 逐行註解：只讀目前使用者自己的 JSON，不讀其他人的檔案。
    embeds = build_memory_list_embeds(memories, title="📚 我的永久記憶")  # 逐行註解：建立自動分頁 Embed。
    await send_interaction_embed_pages(interaction, embeds, ephemeral=True)  # 逐行註解：送出 Embed 分頁。


def format_summary_memory_prompt_message(memory_items: list[dict], source_count: int, *, state: str = "preview") -> str:
    """把 summary memory 的 memories JSON 預覽/結果限制在 Discord 單則訊息內。"""
    json_text = format_memory_json_items(memory_items)
    if len(json_text) > 1350:
        shown_json = json_text[:1350].rstrip() + "\n  ... 預覽已截斷，更新會寫入完整 JSON"
        shown_summary = f"```json\n{shown_json}\n```"
    else:
        shown_summary = format_memory_json_code_block(memory_items)
    if state == "updated":
        header = "Summary memory 已寫入 memories JSON"
        footer = "已用這份整理後 JSON 覆蓋你的永久記憶；raw chat history 已保留。"
    elif state == "cancelled":
        header = "Summary memory 未更新"
        footer = "沒有寫入 memories JSON，目前永久記憶沒有變更。"
    else:
        header = "Summary memory 預覽（memories JSON 格式）"
        footer = "要用這份 JSON 更新永久記憶嗎？按「更新」會覆蓋目前 memories JSON，並保留 raw chat history。"

    return (
        f"{header}\n"
        f"固定模型：{SUMMARY_MEMORY_OLLAMA_MODEL}\n"
        f"來源記錄：{source_count} 筆\n\n"
        f"{shown_summary}\n\n"
        f"{footer}"
    )


class SummaryMemoryUpdateView(discord.ui.View):
    """讓使用者確認是否用 gemma4_thinking 產生的整理稿更新 summary memory。"""

    def __init__(self, target_user_id: int, memory_items: list[dict], source_count: int):
        super().__init__(timeout=300)
        self.target_user_id = target_user_id
        self.memory_items = memory_items
        self.source_count = source_count

    def disable_buttons(self) -> None:
        for child in self.children:
            child.disabled = True

    async def reject_wrong_user(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.target_user_id:
            return False
        await interaction.response.send_message("這不是你的 summary memory 更新選項。", ephemeral=True)
        return True

    @discord.ui.button(label="更新", style=discord.ButtonStyle.primary)
    async def update_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.reject_wrong_user(interaction):
            return
        save_permanent_memories(self.target_user_id, self.memory_items)
        upsert_summary_memory(self.target_user_id, format_memory_json_items(self.memory_items))
        self.disable_buttons()
        await interaction.response.edit_message(
            content=format_summary_memory_prompt_message(self.memory_items, self.source_count, state="updated"),
            view=self,
        )

    @discord.ui.button(label="不更新", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.reject_wrong_user(interaction):
            return
        self.disable_buttons()
        await interaction.response.edit_message(
            content=format_summary_memory_prompt_message(self.memory_items, self.source_count, state="cancelled"),
            view=self,
        )


@tree.command(name="clear", description="清空你的聊天記錄")
async def clear_memory(interaction: discord.Interaction):
    """輸入 /clear，清空目前使用者的全部 bot 聊天記錄。"""
    private_reply = interaction.guild is not None
    if not is_allowed_interaction_user(interaction):
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=private_reply)
        return
    deleted_keys = clear_user_conversation_memory(interaction.user.id)
    await interaction.response.send_message(
        f"已清空聊天記錄（清掉 {deleted_keys} 個記錄區）。",
        ephemeral=private_reply,
    )


@tree.command(name="summary_memory", description="用 gemma4_thinking 整理並更新 summary memory")
async def summary_memory(interaction: discord.Interaction):
    """輸入 /summary_memory，先整理聊天記錄，再詢問是否更新 summary memory。"""
    private_reply = interaction.guild is not None
    if not is_allowed_interaction_user(interaction):
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=private_reply)
        return

    memory_context = format_user_memory_for_summary(interaction.user.id)
    source_count = count_user_memory_records(interaction.user.id)
    if not memory_context:
        await interaction.response.send_message("目前沒有聊天記錄可整理。", ephemeral=private_reply)
        return

    await interaction.response.defer(ephemeral=private_reply, thinking=True)
    response_message = await interaction.followup.send(
        thinking_animation_text(SUMMARY_MEMORY_OLLAMA_MODEL, THINKING_FRAMES[0]),
        ephemeral=private_reply,
        wait=True,
    )
    thinking_stop_event = asyncio.Event()
    thinking_task = asyncio.create_task(run_thinking_animation(response_message, thinking_stop_event, SUMMARY_MEMORY_OLLAMA_MODEL))

    try:
        summary_reply = await ask_ollama_text(
            SUMMARY_MEMORY_OLLAMA_MODEL,
            build_summary_memory_prompt(memory_context),
            timeout_s=None,
            include_thinking=False,
        )
        summary_contents = parse_summary_memory_items(str(summary_reply))
        if not summary_contents:
            thinking_stop_event.set()
            try:
                await thinking_task
            except Exception as stop_error:
                print(f"/summary_memory Thinking 動畫停止失敗：{type(stop_error).__name__}: {stop_error}")
            await safe_edit_message(response_message, "summary_memory 沒有產生可寫入 memories JSON 的內容。")
            return
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_items = [build_memory_json_item(index + 1, content, created_at) for index, content in enumerate(summary_contents)]
    except Exception as e:
        thinking_stop_event.set()
        try:
            await thinking_task
        except Exception as stop_error:
            print(f"/summary_memory Thinking 動畫停止失敗：{type(stop_error).__name__}: {stop_error}")
        await safe_edit_message(response_message, f"（summary memory 整理失敗：{type(e).__name__}: {str(e)[:300]}）")
        return

    thinking_stop_event.set()
    try:
        await thinking_task
    except Exception as e:
        print(f"/summary_memory Thinking 動畫停止失敗：{type(e).__name__}: {e}")

    view = SummaryMemoryUpdateView(interaction.user.id, summary_items, source_count)
    preview_content = format_summary_memory_prompt_message(summary_items, source_count)
    try:
        await response_message.edit(content=preview_content, view=view)
    except Exception as e:
        print(f"/summary_memory 預覽按鈕建立失敗：{type(e).__name__}: {e}")
        await safe_edit_message(response_message, preview_content)


@tree.command(name="forget", description="刪除指定編號的永久記憶")  # 逐行註解：註冊 /forget slash command，用來刪除目前使用者自己的指定記憶。
@discord.app_commands.describe(memory_id="要刪除的永久記憶編號")  # 逐行註解：替 /forget 的 memory_id 參數加上 Discord 顯示說明。
async def forget_command(interaction: discord.Interaction, memory_id: int):  # 逐行註解：定義 /forget 指令。
    if not is_allowed_interaction_user(interaction):  # 逐行註解：刪除永久記憶前依目前情境檢查權限，統一走 ALLOWED_USERS 與 SUPER_USERS。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限時回覆私人提醒。
        return  # 逐行註解：沒有權限就停止。
    memories = load_permanent_memories(interaction.user.id)  # 逐行註解：只讀目前使用者自己的永久記憶。
    kept_memories = [item for item in memories if int(item.get("id", 0)) != int(memory_id)]  # 逐行註解：建立刪除指定編號後的清單，不影響其他使用者檔案。
    if len(kept_memories) == len(memories):  # 逐行註解：長度沒變代表找不到該編號。
        await interaction.response.send_message("❌ 找不到該記憶編號", ephemeral=True)  # 逐行註解：回覆使用者指定編號不存在。
        return  # 逐行註解：停止指令。
    save_permanent_memories(interaction.user.id, kept_memories)  # 逐行註解：寫回刪除後的使用者專屬 JSON。
    await interaction.response.send_message(f"✅ 已刪除記憶\n\n編號：{memory_id}", ephemeral=True)  # 逐行註解：回覆刪除成功。


@tree.command(name="youtube", description="摘要 YouTube 影片")  # 逐行註解：註冊 /youtube slash command，支援一般影片與 Shorts，但使用者端不顯示字幕原文。
@discord.app_commands.describe(url="YouTube 一般影片或 Shorts 網址")  # 逐行註解：替 /youtube 的 url 參數加上 Discord 顯示說明。
async def youtube_command(interaction: discord.Interaction, url: str):  # 逐行註解：定義 /youtube 指令。
    if not is_allowed_interaction_user(interaction):  # 逐行註解：分析 YouTube 前依目前情境檢查權限，統一走 ALLOWED_USERS 與 SUPER_USERS。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限時回覆私人提醒。
        return  # 逐行註解：沒有權限就停止。
    video_id = extract_youtube_video_id(url)  # 逐行註解：從使用者網址抽出 YouTube video id。
    if not video_id:  # 逐行註解：如果抽不到 video id，就代表網址不支援或格式錯。
        await interaction.response.send_message("請提供有效的 YouTube 影片或 Shorts 網址。", ephemeral=True)  # 逐行註解：提醒使用者修正網址。
        return  # 逐行註解：停止指令。
    await interaction.response.defer(ephemeral=True, thinking=True)  # 逐行註解：字幕抓取與 Ollama 摘要可能超過 3 秒，所以先 defer。
    try:  # 逐行註解：yt-dlp 讀 metadata 可能因影片不可用而失敗。
        title = await get_youtube_title(url)  # 逐行註解：用 yt-dlp 取得影片標題，不下載整部影片。
    except Exception as e:  # 逐行註解：標題讀取失敗時仍可嘗試字幕摘要。
        print(f"YouTube 標題讀取失敗：{type(e).__name__}: {e}")  # 逐行註解：把標題錯誤印到後台。
        title = "未知標題"  # 逐行註解：標題失敗時用備援文字。
    try:  # 逐行註解：字幕可能不存在或影片封鎖。
        transcript_text, subtitle_language = await get_youtube_transcript(video_id)  # 逐行註解：優先抓繁體中文字幕，沒有就抓其他可用字幕。
    except Exception as e:  # 逐行註解：完全沒有字幕或抓取失敗時回覆使用者。
        print(f"YouTube 字幕讀取失敗：{type(e).__name__}: {e}")  # 逐行註解：把字幕錯誤印到後台。
        await interaction.followup.send("此影片沒有可用字幕，無法產生摘要。", ephemeral=True)  # 逐行註解：依需求提示無字幕。
        return  # 逐行註解：停止指令。
    if not transcript_text.strip():  # 逐行註解：如果 API 回傳空字幕，也視為無字幕。
        await interaction.followup.send("此影片沒有可用字幕，無法產生摘要。", ephemeral=True)  # 逐行註解：依需求提示無字幕。
        return  # 逐行註解：停止指令。
    model = selected_text_model_for_user(interaction.user.id)  # 逐行註解：取得目前可用文字模型。
    prompt = build_youtube_summary_prompt(title, transcript_text, subtitle_language)  # 逐行註解：建立 YouTube 摘要 prompt。
    reply = await ask_ollama_text(model, prompt, timeout_s=None)  # 逐行註解：用目前 Ollama 模型摘要字幕。
    response = str(reply or "")  # 逐行註解：依除錯需求保留這次 AI 回覆原文變數。
    debug_ai_response(response)  # 逐行註解：印出 === AI RESPONSE === 與完整 AI 回覆。
    chart_payload = parse_chart_reply(str(reply or ""))  # 逐行註解：檢查 YouTube 摘要是否回傳圖表 JSON。
    if chart_payload:  # 逐行註解：如果模型回傳圖表 JSON，就送實際圖表圖片。
        await interaction.followup.send(chart_reply_summary(chart_payload), ephemeral=True)  # 逐行註解：先用私人訊息告知圖表已產生。
        await send_chart_payload_to_interaction_channel(interaction, chart_payload, ephemeral=True)  # 逐行註解：用 BytesIO 圖表傳到 slash 指令原頻道。
        return  # 逐行註解：圖表已送出後結束，不再把 JSON 當文字顯示。
    await send_interaction_text_chunks(interaction, str(reply or "（我沒有產生任何回覆）"), ephemeral=True)  # 逐行註解：送出摘要結果，超長自動分段。


#######################事件#######################
"""
@bot.event 這種寫法叫做裝飾器，
可以把它寫成幫下面的函式貼上一張「事件處理員」標籤。
def 是一般函式，通常會照順序一路做完。
async def 是可以搭配 await 的函式；
遇到需要等一下的工作時，
他可以先暫停，等事情完後再回來繼續做。
"""
@bot.event  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def on_ready():  # 逐行註解：定義非同步函式 on_ready，可以搭配 await 處理 Discord 或網路等待。
    print(f"{bot.user}is ready and online\n＝＝＝＝＝＝＝＝＝＝＝後台：＝＝＝＝＝＝＝＝＝＝＝")  # 逐行註解：把資訊印到終端機後台，方便觀察 bot 執行狀態。
    await send_startup_dm()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
    ensure_weather_alert_monitor_started()  # 啟動台北危險天氣背景監控，每 5 分鐘檢查一次。
    # await：等這件事完成後再繼續往下
    # return：直接結束函式
    # tree.sync()：把slash 指令送去Discord登記
    synced_commands = await tree.sync()  # 把我們在程式裡登記的指令，同步到 Discord 上，讓她知道我們有哪些指令可以用
    print(f"Slash Commands 已同步：{len(synced_commands)} 個：{', '.join(command.name for command in synced_commands)}")  # 逐行註解：把同步結果印到後台，方便確認新增 slash commands 已註冊。


@bot.event  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def on_disconnect():  # 逐行註解：定義非同步函式 on_disconnect，可以搭配 await 處理 Discord 或網路等待。
    pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。


def notification_recipient_keys() -> list[str]:  # 逐行註解：建立上線、下線與重啟通知要通知的權限 key 清單。
    return unique_env_items(SUPER_USER_LIST + ALLOWED_USER_LIST)  # 逐行註解：SUPER_USERS 與 ALLOWED_USERS 合併後去重，超級使用者即使沒寫在 ALLOWED_USERS 也會收到通知。


def format_discord_user_for_log(user) -> str:  # 逐行註解：把 Discord 使用者整理成安全 log 標籤，不包含 token 或任何金鑰。
    user_name = getattr(user, "name", "") or getattr(user, "display_name", "") or str(user)  # 逐行註解：優先使用 Discord 名稱，避免 log 空白。
    user_id = getattr(user, "id", "未知ID")  # 逐行註解：加入 Discord ID 方便排查 DM 失敗。
    return f"{user_name}({user_id})"  # 逐行註解：回傳可讀但不含敏感金鑰的收件人標籤。


def iter_cached_guild_members() -> list:  # 逐行註解：收集目前 bot 已知 guild member cache，供名稱、顯示名稱與 email alias 解析。
    members = []  # 逐行註解：建立收集到的 member 清單。
    for guild in getattr(bot, "guilds", []) or []:  # 逐行註解：逐一檢查目前 bot 已加入的所有 guild。
        members.extend(getattr(guild, "members", []) or [])  # 逐行註解：加入這個 guild 目前快取到的 member。
    return members  # 逐行註解：回傳所有可用的快取 member。


async def collect_guild_members_for_notification() -> list:  # 逐行註解：取得通知解析可用的 guild members，優先用快取，必要時嘗試 API fetch。
    members = iter_cached_guild_members()  # 逐行註解：先使用目前 gateway 已快取的 guild members。
    if members:  # 逐行註解：如果快取已有資料，就避免額外 API 呼叫。
        return members  # 逐行註解：直接回傳快取 members。
    fetched_members = []  # 逐行註解：建立 API fetch 成功取得的 member 清單。
    for guild in getattr(bot, "guilds", []) or []:  # 逐行註解：逐一嘗試目前 bot 已加入的 guild。
        try:  # 逐行註解：fetch_members 可能因 Discord 權限或 intents 設定失敗。
            async for member in guild.fetch_members(limit=None):  # 逐行註解：嘗試完整讀取目前 guild members 以解析 username 或 display name。
                fetched_members.append(member)  # 逐行註解：把 fetch 到的 member 加入解析清單。
        except Exception as e:  # 逐行註解：單一 guild 讀取失敗不能讓通知流程崩潰。
            guild_name = getattr(guild, "name", "未知guild")  # 逐行註解：取得 guild 名稱用於安全 log。
            guild_id = getattr(guild, "id", "未知ID")  # 逐行註解：取得 guild ID 方便排查。
            print(f"讀取 guild members 失敗 {guild_name}({guild_id})：{type(e).__name__}: {e}")  # 逐行註解：記錄失敗原因，不印 token 或 API key。
    return fetched_members  # 逐行註解：回傳 API fetch 得到的 members，可能是空清單。


def resolve_permission_notification_users_from_members(members) -> tuple[list, list[str], set[str]]:  # 逐行註解：從指定 member 清單解析 ALLOWED_USERS 與 SUPER_USERS 通知收件人。
    recipients_by_id = {}  # 逐行註解：用 Discord user id 去重，避免同一人因多個 key 收到多次通知。
    unresolved_keys: list[str] = []  # 逐行註解：保存目前 guild member cache 找不到的設定項目。
    matched_keys: set[str] = set()  # 逐行註解：保存已成功對應到 Discord 使用者的權限 key。
    for permission_key in notification_recipient_keys():  # 逐行註解：逐一解析 SUPER_USERS 與 ALLOWED_USERS 的每個 key。
        matched_user = None  # 逐行註解：先假設這個 key 找不到對應 Discord 使用者。
        for member in members:  # 逐行註解：逐一比對目前 guild member cache。
            if permission_key in get_discord_user_keys(member):  # 逐行註解：任一 Discord key 命中設定 key 就視為同一人。
                matched_user = member  # 逐行註解：保存找到的 Discord member。
                break  # 逐行註解：這個 key 已找到，不需要繼續掃其他 member。
        if matched_user is None:  # 逐行註解：目前快取中找不到這個設定 key。
            unresolved_keys.append(permission_key)  # 逐行註解：保存未解析 key，稍後記 log。
            continue  # 逐行註解：繼續解析下一個 key。
        user_id = str(getattr(matched_user, "id", ""))  # 逐行註解：取出 Discord ID 作為去重依據。
        if user_id:  # 逐行註解：有 ID 才能可靠去重。
            recipients_by_id[user_id] = matched_user  # 逐行註解：同一 ID 重複命中時只保留一份。
            matched_keys.add(permission_key)  # 逐行註解：標記這個 key 已成功解析。
    return list(recipients_by_id.values()), unresolved_keys, matched_keys  # 逐行註解：回傳去重收件人、未解析 key 與已解析 key。


async def resolve_permission_notification_users() -> tuple[list, list[str]]:  # 逐行註解：解析目前應收到上線、下線或重啟通知的 Discord 使用者。
    members = await collect_guild_members_for_notification()  # 逐行註解：從快取或 API 取得目前 guild members 來解析名稱、顯示名稱與 email alias。
    recipients, unresolved_keys, matched_keys = resolve_permission_notification_users_from_members(members)  # 逐行註解：用共用解析函式找出可通知對象。
    recipients_by_id = {str(getattr(user, "id", "")): user for user in recipients if getattr(user, "id", None)}  # 逐行註解：建立已找到收件人的 ID 字典，避免後續 ID fetch 重複加入。
    still_unresolved: list[str] = []  # 逐行註解：保存連 ID fetch 都無法處理的 key。
    for permission_key in unresolved_keys:  # 逐行註解：針對快取找不到的 key 做最後處理。
        if not permission_key.isdigit():  # 逐行註解：非數字 key 無法直接 fetch Discord user。
            still_unresolved.append(permission_key)  # 逐行註解：保存非數字未解析 key，稍後只記 log。
            continue  # 逐行註解：繼續處理下一個未解析 key。
        try:  # 逐行註解：數字 ID 可以嘗試從 Discord API 取得 user。
            user = bot.get_user(int(permission_key)) or await bot.fetch_user(int(permission_key))  # 逐行註解：先讀本地 cache，沒有才 fetch。
            recipients_by_id[str(user.id)] = user  # 逐行註解：用 ID 去重加入通知收件人。
            matched_keys.add(permission_key)  # 逐行註解：標記這個數字 key 已成功解析。
        except Exception as e:  # 逐行註解：fetch 可能因 ID 錯誤或網路問題失敗。
            still_unresolved.append(permission_key)  # 逐行註解：保存失敗 key，稍後只記 log。
            print(f"找不到通知收件人 {permission_key}：{type(e).__name__}: {e}")  # 逐行註解：記錄解析失敗原因，不讓 bot 崩潰。
    return list(recipients_by_id.values()), still_unresolved  # 逐行註解：回傳可傳送使用者與無法解析的 key。


async def send_permission_notification_to_users(users, content: str, log_label: str) -> tuple[int, int]:  # 逐行註解：把指定通知傳給已解析出的 Discord 使用者，並保證單人失敗不會中斷整批。
    sent_count = 0  # 逐行註解：統計成功傳送數量，方便測試與排查。
    failed_count = 0  # 逐行註解：統計失敗傳送數量，方便測試與排查。
    for user in users:  # 逐行註解：逐一傳送通知給每個去重後的使用者。
        try:  # 逐行註解：每個人的 DM 都獨立保護，避免一個人關閉 DM 讓整批失敗。
            await user.send(content)  # 逐行註解：傳送實際通知內容。
            sent_count += 1  # 逐行註解：成功時增加成功計數。
        except Exception as e:  # 逐行註解：使用者關閉 DM、封鎖 bot 或 Discord 錯誤都會到這裡。
            failed_count += 1  # 逐行註解：失敗時增加失敗計數。
            print(f"無法傳送{log_label}通知給 {format_discord_user_for_log(user)}：{type(e).__name__}: {e}")  # 逐行註解：記錄失敗原因，但不印 token 或 API key。
    return sent_count, failed_count  # 逐行註解：回傳成功與失敗數，測試可確認不能 DM 時不會 crash。


async def send_permission_notification(content: str, log_label: str) -> tuple[int, int]:  # 逐行註解：解析權限通知收件人並送出指定通知。
    users, unresolved_keys = await resolve_permission_notification_users()  # 逐行註解：把 ALLOWED_USERS 與 SUPER_USERS 解析成 Discord 使用者。
    for permission_key in unresolved_keys:  # 逐行註解：逐一記錄找不到的設定 key。
        print(f"找不到{log_label}通知收件人 {permission_key}，略過。")  # 逐行註解：找不到收件人只記 log，不讓 bot 崩潰。
    return await send_permission_notification_to_users(users, content, log_label)  # 逐行註解：傳送通知並回傳成功失敗統計。


async def send_startup_dm():  # 逐行註解：定義非同步函式 send_startup_dm，可以搭配 await 處理 Discord 或網路等待。
    global startup_dm_sent  # 逐行註解：使用防重複旗標，避免 Discord 重連時重複通知。
    if startup_dm_sent:  # 逐行註解：如果這次啟動已經送過上線通知，就不要重複送。
        return  # 逐行註解：直接結束函式。
    await send_permission_notification("我上線了，可以開始為您服務了！", "上線")  # 逐行註解：上線時通知所有 ALLOWED_USERS 與 SUPER_USERS。
    startup_dm_sent = True  # 逐行註解：整批上線通知跑完後標記已送過。


def weather_alert_key(message: str) -> str:  # 將警報訊息轉成去重 key。
    return str(message or "").split("：", 1)[0].strip() or str(message or "").strip()  # 以冒號前的警報類型做 key，例如大雨風險。


def should_send_weather_alert(message: str, now: float, cooldown_seconds: int = 3600) -> bool:  # 判斷同類警報是否可以再次傳送。
    key = weather_alert_key(message)  # 取得警報類型 key。
    if key not in weather_alert_last_sent:  # 如果這類警報從未傳過，第一次一定要主動通知。
        weather_alert_last_sent[key] = now  # 保存第一次傳送時間。
        return True  # 回傳 True 表示可以傳送。
    last_sent = weather_alert_last_sent.get(key, 0)  # 讀取這類警報上次傳送時間。
    if now - last_sent < cooldown_seconds:  # 如果一小時內已經傳過同類警報，就不要再洗訊息。
        return False  # 回傳 False 表示略過。
    weather_alert_last_sent[key] = now  # 更新這類警報最近傳送時間。
    return True  # 回傳 True 表示可以傳送。


async def send_weather_alert_dm(message: str) -> None:  # 將危險天氣警報主動私訊給設定清單。
    content = f"⚠️ 台北天氣主動警報\n{message}\n\n請以中央氣象署、地方政府災防告警和即時雷達為準；若已在戶外，優先找安全遮蔽處。"  # 建立主動警報訊息。
    if not WEATHER_ALERT_DM_USER_IDS:  # 逐行註解：沒有另外設定天氣警報 ID 時，沿用 ALLOWED_USERS 與 SUPER_USERS 通知對象。
        await send_permission_notification(content, "天氣警報")  # 逐行註解：天氣警報也用同一套安全通知發送函式，不能 DM 時不會 crash。
        return  # 逐行註解：已用權限通知對象傳送後結束。
    for user_id in WEATHER_ALERT_DM_USER_IDS:  # 逐一傳送給警報收件人。
        try:  # 私訊可能因 ID 錯誤或使用者關閉 DM 失敗。
            user = await bot.fetch_user(int(user_id))  # 用 Discord 數字 ID 取得使用者。
            await user.send(content)  # 主動傳送天氣警報私訊。
        except Exception as e:  # 某個收件人失敗不能影響其他人。
            print(f"天氣警報私訊失敗：user_id={user_id}, {type(e).__name__}: {e}")  # 後台記錄失敗原因。


async def weather_alert_monitor_loop() -> None:  # 每 5 分鐘監控台北危險天氣並主動通知。
    await bot.wait_until_ready()  # 等 Discord client 完全 ready 後再開始抓資料和傳訊息。
    while not bot.is_closed():  # bot 還在執行時持續監控。
        try:  # 天氣 API 或 Discord 私訊都可能失敗，所以要保護背景 task。
            weather_data = await load_weather_report_data(WEATHER_ALERT_CITY)  # 查詢設定城市的天氣資料，預設台北。
            alerts = get_weather_alert_messages(weather_data)  # 從預報中抽取需要主動通知的警報。
            now = time.monotonic()  # 使用 monotonic 作為去重時間基準。
            for alert in alerts:  # 逐一處理警報。
                if should_send_weather_alert(alert, now):  # 同類警報冷卻時間過後才傳送。
                    await send_weather_alert_dm(alert)  # 主動私訊警報。
        except Exception as e:  # 背景監控錯誤不能讓 bot 崩潰。
            print(f"天氣警報監控失敗：{type(e).__name__}: {e}")  # 後台印出錯誤摘要。
            traceback.print_exc()  # 完整 traceback 方便排查。
        await asyncio.sleep(WEATHER_ALERT_CHECK_SECONDS)  # 等待 5 分鐘後再檢查一次。


def ensure_weather_alert_monitor_started() -> None:  # 確保天氣警報背景監控只啟動一次。
    global weather_alert_monitor_task  # 逐行註解：需要更新全域 task 變數。
    if weather_alert_monitor_task is not None and not weather_alert_monitor_task.done():  # 如果已經有監控 task 在跑，就不要重複啟動。
        return  # 直接結束。
    weather_alert_monitor_task = asyncio.create_task(weather_alert_monitor_loop())  # 建立背景天氣警報監控 task。


async def send_shutdown_dm(message: str ="我先下線了，掰掰！", log_label: str = "下線"):  # 逐行註解：定義非同步函式 send_shutdown_dm，可以搭配 await 處理 Discord 或網路等待。
    global shutdown_dm_sent  # 逐行註解：使用防重複旗標，避免多個關閉入口重複通知。
    if shutdown_dm_sent:  # 逐行註解：如果這次關閉流程已經送過通知，就不要重複送。
        return  # 逐行註解：直接結束函式。
    await send_permission_notification(message, log_label)  # 逐行註解：下線或重啟前通知所有 ALLOWED_USERS 與 SUPER_USERS。
    shutdown_dm_sent = True  # 逐行註解：整批通知跑完後標記已送過。


def build_agent_prompt(task: str, session: dict, terminal_feedback: str = "") -> str:  # 逐行註解：組合 Agent 要送給 Ollama 的 prompt。
    """只傳任務與 terminal feedback；輸出規則放在 gemma4_agent_discord-bot.Modelfile。"""  # 逐行註解：避免把 Agent system prompt 硬寫在 AI.py 裡。
    history = "\n".join(session.get("task_history", [])[-10:]) or "（沒有歷史）"  # 逐行註解：保留最近任務歷史，避免 prompt 太長。
    commands = "\n".join(session.get("command_history", [])[-10:]) or "（沒有指令歷史）"  # 逐行註解：保留最近 command 歷史，讓模型知道做過什麼。
    return f"""
TASK:
{task}

TASK_HISTORY:
{history}

COMMAND_HISTORY:
{commands}

TERMINAL_FEEDBACK:
{terminal_feedback or "（尚未執行 command）"}

Return exactly one JSON object using the schema configured in your Modelfile.
""".strip()  # 逐行註解：回傳完整 prompt。


def extract_agent_json(text: str) -> dict | None:  # 逐行註解：從模型輸出中找第一個 JSON object。
    """優先解析專用 Agent Modelfile 要求的 JSON 格式。"""  # 逐行註解：比舊的文字區塊更穩定。
    cleaned = (text or "").strip()  # 逐行註解：清掉前後空白。
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()  # 逐行註解：如果模型偷包 code fence，先移除。
    decoder = json.JSONDecoder()  # 逐行註解：建立 JSON decoder，用來從任意位置嘗試解析 object。
    for match in re.finditer(r"\{", cleaned):  # 逐行註解：逐一嘗試每個左大括號，避免前面混入雜訊。
        try:  # 逐行註解：JSON 解析可能失敗，所以用 try 保護。
            data, _ = decoder.raw_decode(cleaned[match.start():])  # 逐行註解：從目前大括號開始解析一個 JSON 值。
            if isinstance(data, dict):  # 逐行註解：只有 dict 才是 Agent 要的 JSON object。
                return data  # 逐行註解：找到第一個可用 object 就回傳。
        except json.JSONDecodeError:  # 逐行註解：這個大括號不是有效 JSON，就換下一個。
            continue  # 逐行註解：繼續尋找下一個候選。
    return None  # 逐行註解：完全找不到 JSON object。


def parse_agent_response(text: str) -> dict[str, str]:  # 逐行註解：解析 Ollama Agent 回覆。
    """先解析 JSON；失敗時相容舊的 ===PLAN=== 或 **PLAN** 格式。"""  # 逐行註解：避免模型偶爾格式飄掉就整個 Agent 失敗。
    data = extract_agent_json(text)  # 逐行註解：先嘗試專用 Modelfile 的 JSON 格式。
    if data is not None:  # 逐行註解：如果 JSON 解析成功，就標準化欄位。
        default_done = "任務已完成並通過驗證。"  # 逐行註解：模型偶爾漏填 done 時，由程式補上穩定完成句。
        return {  # 逐行註解：回傳統一欄位名稱，讓後面流程不用管來源格式。
            "status": str(data.get("status") or "continue").strip(),  # 逐行註解：保存模型判斷狀態。
            "plan": str(data.get("plan") or "").strip(),  # 逐行註解：保存簡短計畫。
            "command": str(data.get("command") or "").strip(),  # 逐行註解：保存要執行的一行 command。
            "verify": str(data.get("verify") or "").strip(),  # 逐行註解：保存一行驗證 command。
            "done": str(data.get("done") or default_done).strip(),  # 逐行註解：保存最後要回覆使用者的短句，空值就補預設句。
        }  # 逐行註解：結束標準化 dict。
    normalized = (text or "").strip()  # 逐行註解：JSON 失敗時改用舊格式解析。
    normalized = re.sub(r"\*\*\s*(PLAN|COMMAND|VERIFY|DONE)\s*\*\*", r"===\1===", normalized, flags=re.IGNORECASE)  # 逐行註解：把 **PLAN** 這類 markdown 標題轉成舊區塊標題。
    normalized = re.sub(r"(?m)^\s*(PLAN|COMMAND|VERIFY|DONE)\s*:\s*$", r"===\1===", normalized, flags=re.IGNORECASE)  # 逐行註解：把 PLAN: 獨立標題轉成舊區塊標題。
    parsed: dict[str, str] = {"status": "continue"}  # 逐行註解：建立解析結果 dict。
    for key in ("PLAN", "COMMAND", "VERIFY", "DONE"):  # 逐行註解：逐一抽取四個必要區塊。
        pattern = rf"==={key}===\s*(.*?)(?=\n===PLAN===|\n===COMMAND===|\n===VERIFY===|\n===DONE===|\Z)"  # 逐行註解：用下一個標題或文字結尾當作區塊邊界。
        match = re.search(pattern, normalized or "", re.DOTALL | re.IGNORECASE)  # 逐行註解：跨行搜尋目前區塊。
        parsed[key.lower()] = match.group(1).strip() if match else ""  # 逐行註解：保存區塊文字，沒有就留空。
    if not parsed.get("done"):  # 逐行註解：舊格式如果漏掉 DONE 內容，也由程式補上穩定完成句。
        parsed["done"] = "任務已完成並通過驗證。"  # 逐行註解：避免只因完成句為空就讓 Agent 格式失敗。
    if is_agent_command_done(parsed.get("command", "")):  # 逐行註解：舊格式用 COMMAND DONE 判斷完成。
        parsed["status"] = "done"  # 逐行註解：補上 done 狀態。
    return parsed  # 逐行註解：回傳解析好的四個欄位。


def is_agent_response_complete(parsed: dict[str, str]) -> bool:  # 逐行註解：檢查 Agent 回覆是否包含四個必要欄位。
    return all((parsed.get(key) or "").strip() for key in ("plan", "command", "verify", "done"))  # 逐行註解：四個區塊都有內容才算完整。


def is_agent_command_done(command: str) -> bool:  # 逐行註解：判斷 Agent 是否已宣告任務完成。
    return (command or "").strip().upper() == "DONE"  # 逐行註解：COMMAND 欄位為 DONE 代表不用再執行 shell。


def safe_agent_path_from_task(raw_path: str) -> str:  # 逐行註解：把使用者提到的資料夾名稱轉成安全路徑。
    """相對路徑預設建立在使用者家目錄；空值預設 agent_test。"""  # 逐行註解：避免模型或使用者隨手輸入造成路徑不明確。
    cleaned = (raw_path or "").strip().strip("'\"`")  # 逐行註解：移除引號與多餘空白。
    cleaned = re.sub(r"^(叫做|名稱是|name is)\s*", "", cleaned, flags=re.IGNORECASE).strip()  # 逐行註解：移除中文口語前綴。
    cleaned = re.split(r"[，,。；;]", cleaned)[0].strip()  # 逐行註解：只取第一段，避免把後面句子當路徑。
    if not cleaned:  # 逐行註解：如果沒有明確資料夾名稱。
        cleaned = "agent_test"  # 逐行註解：使用安全的預設資料夾名稱。
    path = Path(cleaned).expanduser()  # 逐行註解：支援使用者輸入 ~/xxx。
    if not path.is_absolute():  # 逐行註解：相對路徑預設放在家目錄。
        path = Path.home() / path  # 逐行註解：組成完整家目錄路徑。
    return str(path)  # 逐行註解：回傳字串路徑。


def programmatic_agent_plan(task: str) -> dict[str, str] | None:  # 逐行註解：針對常見 Mac 任務直接產生可靠 command。
    """常見任務不等 Ollama 猜格式，直接由程式產生 command 和 verify command。"""  # 逐行註解：降低 gemma 格式錯誤造成任務失敗的機率。
    task_text = (task or "").strip()  # 逐行註解：整理原始任務。
    lower_task = task_text.lower()  # 逐行註解：建立小寫版本方便比對英文 App 名稱。
    wants_open = any(word in task_text for word in ("打開", "開啟", "啟動")) or any(word in lower_task for word in ("open", "launch", "start"))  # 逐行註解：判斷是不是開啟 App 類任務。
    if wants_open and "safari" in lower_task:  # 逐行註解：處理打開 Safari。
        return {"status": "continue", "plan": "使用 macOS open 指令打開 Safari，並用 process 驗證。", "command": "open -a Safari", "verify": "sleep 1; pgrep -x Safari >/dev/null", "done": "已打開 Safari。"}  # 逐行註解：回傳 Safari 指令組。
    if wants_open and "arc" in lower_task:  # 逐行註解：處理打開 Arc。
        return {"status": "continue", "plan": "使用 macOS open 指令打開 Arc，並用 process 驗證。", "command": "open -a \"Arc\"", "verify": "sleep 1; pgrep -f \"/Applications/Arc.app|Arc.app/Contents/MacOS/Arc\" >/dev/null", "done": "已打開 Arc。"}  # 逐行註解：回傳 Arc 指令組。
    if wants_open and any(name in lower_task for name in ("vscode", "vs code", "visual studio code")):  # 逐行註解：處理打開 VSCode。
        return {"status": "continue", "plan": "使用 macOS open 指令打開 Visual Studio Code，並用 process 驗證。", "command": "open -a \"Visual Studio Code\"", "verify": "sleep 1; pgrep -f \"Visual Studio Code\" >/dev/null", "done": "已打開 VSCode。"}  # 逐行註解：回傳 VSCode 指令組。
    mkdir_match = re.search(r"\bmkdir\s+(.+)$", task_text, re.IGNORECASE)  # 逐行註解：偵測英文 mkdir 任務。
    folder_match = mkdir_match or re.search(r"(?:建立|新增|創建).{0,8}資料夾\s*(.+)?$", task_text)  # 逐行註解：偵測中文建立資料夾任務。
    if folder_match:  # 逐行註解：如果任務是建立資料夾。
        folder_path = safe_agent_path_from_task(folder_match.group(1) or "agent_test")  # 逐行註解：取得安全資料夾路徑。
        quoted_path = shlex.quote(folder_path)  # 逐行註解：把路徑 quote 起來，避免空白或特殊字元破壞 shell。
        return {"status": "continue", "plan": f"建立資料夾 {folder_path}，並確認資料夾存在。", "command": f"mkdir -p {quoted_path}", "verify": f"test -d {quoted_path}", "done": f"已建立資料夾：{folder_path}"}  # 逐行註解：回傳 mkdir 指令組。
    if "python --version" in lower_task or "python version" in lower_task or "python版本" in task_text or "python 版本" in task_text:  # 逐行註解：處理查詢 Python 版本。
        return {"status": "continue", "plan": "執行 python --version 並確認 exit code 為 0。", "command": "python --version", "verify": "python --version >/dev/null", "done": "已取得 Python 版本。"}  # 逐行註解：回傳 Python 版本指令組。
    if "pygame" in lower_task and ("install" in lower_task or "pip" in lower_task or "安裝" in task_text):  # 逐行註解：處理安裝 pygame。
        return {"status": "continue", "plan": "用 pip 安裝 pygame，並用 import pygame 驗證。", "command": "python -m pip install --user pygame", "verify": "python -c \"import pygame; print(pygame.__version__)\"", "done": "pygame 已安裝並通過 import 驗證。"}  # 逐行註解：回傳 pygame 安裝指令組。
    return None  # 逐行註解：不是常見任務就交給 Ollama 專用模型規劃。


AGENT_BLOCKED_PATTERNS = [  # 逐行註解：Agent shell command 黑名單，擋掉破壞系統或惡意行為。
    r"\brm\s+-[^;\n]*r[^;\n]*f\s+/",  # 逐行註解：禁止 rm -rf / 這類刪根目錄指令。
    r"\bsudo\s+rm\b",  # 逐行註解：禁止 sudo rm。
    r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",  # 逐行註解：禁止 fork bomb。
    r"\bchmod\s+[-+0-7A-Za-z]*\s+/(System|Library|bin|sbin|usr)\b",  # 逐行註解：禁止改系統核心路徑權限。
    r"\bchown\s+[-+0-9A-Za-z:]*\s+/(System|Library|bin|sbin|usr)\b",  # 逐行註解：禁止改系統核心路徑擁有者。
    r"\bmkfs\b",  # 逐行註解：禁止格式化磁碟。
    r"\bdd\s+.*\bof=/dev/",  # 逐行註解：禁止 dd 寫入裝置。
    r"\bshutdown\b|\breboot\b|\bhalt\b",  # 逐行註解：禁止關機或重開機。
    r"\bcurl\b.*\|\s*(sh|bash|zsh)\b",  # 逐行註解：禁止下載腳本後直接 pipe shell。
    r"\bwget\b.*\|\s*(sh|bash|zsh)\b",  # 逐行註解：禁止 wget pipe shell。
    r"\bnc\s+.*\s+-e\b",  # 逐行註解：禁止 netcat 反向 shell 常見模式。
]  # 逐行註解：結束黑名單。


def validate_agent_command(command: str) -> tuple[bool, str]:  # 逐行註解：檢查 Agent command 是否安全。
    """回傳 command 是否允許執行，以及禁止原因。"""  # 逐行註解：避免模型產生危險 shell 後直接執行。
    command = (command or "").strip()  # 逐行註解：清理 command 空白。
    if not command:  # 逐行註解：空 command 不能執行。
        return False, "COMMAND 是空的"  # 逐行註解：回傳禁止原因。
    if "\n" in command or "\r" in command:  # 逐行註解：Agent command 必須是一行，避免藏多段腳本。
        return False, "COMMAND 只能是一行 shell command"  # 逐行註解：回傳禁止原因。
    if is_agent_command_done(command):  # 逐行註解：DONE 不是 shell，不需要安全檢查。
        return True, ""  # 逐行註解：允許 DONE。
    for pattern in AGENT_BLOCKED_PATTERNS:  # 逐行註解：逐一套用黑名單 regex。
        if re.search(pattern, command, re.IGNORECASE):  # 逐行註解：如果符合危險模式，就禁止。
            return False, f"指令被安全黑名單擋下：{pattern}"  # 逐行註解：回傳禁止原因。
    return True, ""  # 逐行註解：沒有命中黑名單就允許。


async def execute_agent_command(command: str) -> dict[str, str | int | bool]:  # 逐行註解：非同步執行 Agent shell command。
    """執行 shell command 並完整保留 stdout、stderr、exit code。"""  # 逐行註解：timeout 會殺掉 process，避免卡死 Discord bot。
    started = time.monotonic()  # 逐行註解：記錄開始時間。
    try:  # 逐行註解：開始建立 shell process。
        proc = await asyncio.create_subprocess_shell(  # 逐行註解：非同步執行 shell command，避免阻塞 Discord event loop。
            command,  # 逐行註解：要執行的 shell command。
            stdout=asyncio.subprocess.PIPE,  # 逐行註解：捕捉 stdout。
            stderr=asyncio.subprocess.PIPE,  # 逐行註解：捕捉 stderr。
            cwd=str(Path.home()),  # 逐行註解：預設在使用者家目錄執行，和 /run 類似。
        )  # 逐行註解：結束 process 建立。
        try:  # 逐行註解：等待 command 完成。
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=AGENT_COMMAND_TIMEOUT_SECONDS)  # 逐行註解：加 timeout，避免長時間卡住。
            timed_out = False  # 逐行註解：標記沒有 timeout。
        except TimeoutError:  # 逐行註解：處理 command 執行超時。
            proc.kill()  # 逐行註解：殺掉超時 process。
            stdout, stderr = await proc.communicate()  # 逐行註解：收尾並讀取已產生的輸出。
            timed_out = True  # 逐行註解：標記已 timeout。
        return {  # 逐行註解：回傳完整執行結果。
            "stdout": (stdout or b"").decode("utf-8", errors="replace"),  # 逐行註解：stdout 轉文字。
            "stderr": (stderr or b"").decode("utf-8", errors="replace"),  # 逐行註解：stderr 轉文字。
            "exit_code": proc.returncode if proc.returncode is not None else -1,  # 逐行註解：保存 exit code。
            "timed_out": timed_out,  # 逐行註解：保存是否 timeout。
            "seconds": round(time.monotonic() - started, 2),  # 逐行註解：保存執行耗時。
        }  # 逐行註解：結束結果 dict。
    except Exception as e:  # 逐行註解：捕捉 process 建立或執行時的例外。
        return {"stdout": "", "stderr": f"{type(e).__name__}: {e}", "exit_code": -1, "timed_out": False, "seconds": round(time.monotonic() - started, 2)}  # 逐行註解：回傳錯誤結果。


def format_agent_terminal_feedback(command: str, result: dict[str, str | int | bool], verify_command: str = "", verify_result: dict[str, str | int | bool] | None = None) -> str:  # 逐行註解：把 terminal 結果整理成可回傳給 Ollama 的文字。
    """保留 command、stdout、stderr、exit code、timeout、耗時。"""  # 逐行註解：這段也會顯示給 Discord 使用者。
    lines = [  # 逐行註解：先建立主要 command 執行結果。
        [
            f"COMMAND: {command}",  # 逐行註解：記錄執行的 command。
            f"EXIT_CODE: {result.get('exit_code')}",  # 逐行註解：記錄 exit code。
            f"TIMED_OUT: {result.get('timed_out')}",  # 逐行註解：記錄是否 timeout。
            f"SECONDS: {result.get('seconds')}",  # 逐行註解：記錄耗時。
            "STDOUT:",  # 逐行註解：stdout 標題。
            str(result.get("stdout") or ""),  # 逐行註解：完整 stdout。
            "STDERR:",  # 逐行註解：stderr 標題。
            str(result.get("stderr") or ""),  # 逐行註解：完整 stderr。
        ]
    ][0]  # 逐行註解：取出清單內容，保持後面可 append。
    if verify_command and verify_result is not None:  # 逐行註解：如果有驗證 command，也把驗證結果保留下來。
        lines.extend(  # 逐行註解：追加驗證 command 的完整結果。
            [
                "",
                f"VERIFY_COMMAND: {verify_command}",  # 逐行註解：記錄驗證 command。
                f"VERIFY_EXIT_CODE: {verify_result.get('exit_code')}",  # 逐行註解：記錄驗證 exit code。
                f"VERIFY_TIMED_OUT: {verify_result.get('timed_out')}",  # 逐行註解：記錄驗證是否 timeout。
                f"VERIFY_SECONDS: {verify_result.get('seconds')}",  # 逐行註解：記錄驗證耗時。
                "VERIFY_STDOUT:",  # 逐行註解：驗證 stdout 標題。
                str(verify_result.get("stdout") or ""),  # 逐行註解：完整驗證 stdout。
                "VERIFY_STDERR:",  # 逐行註解：驗證 stderr 標題。
                str(verify_result.get("stderr") or ""),  # 逐行註解：完整驗證 stderr。
            ]
        )  # 逐行註解：結束 extend。
    return "\n".join(lines)  # 逐行註解：回傳 feedback。


def discord_code_block(text: str, language: str = "txt", limit: int = 1700) -> str:  # 逐行註解：建立 Discord code block，避免訊息超過上限。
    cleaned = (text or "").replace("```", "'''")  # 逐行註解：避免內容破壞 code block。
    if len(cleaned) > limit:  # 逐行註解：如果太長就截斷顯示，但完整內容仍存在 agent history。
        cleaned = cleaned[:limit].rstrip() + "\n...（輸出太長，Discord 只顯示前段）"  # 逐行註解：標記已截斷。
    return f"```{language}\n{cleaned}\n```"  # 逐行註解：回傳 code block。


def format_agent_step_message(step: int, parsed: dict[str, str], terminal_feedback: str | None = None) -> str:  # 逐行註解：整理 Agent 每一輪要顯示在 Discord 的內容。
    parts = [f"Agent Step {step}", f"AI 計畫：{parsed.get('plan') or 'N/A'}", "Command：", discord_code_block(parsed.get("command") or "", "bash"), "Verify command：", discord_code_block(parsed.get("verify") or "", "bash")]  # 逐行註解：建立基本顯示內容。
    if terminal_feedback is not None:  # 逐行註解：如果這輪已執行 command，就加上 terminal output。
        parts.extend(["Terminal Output：", discord_code_block(terminal_feedback, "txt")])  # 逐行註解：terminal output 用 txt code block 顯示。
    return "\n".join(parts)[:1900]  # 逐行註解：保守限制單則訊息長度。


def agent_command_succeeded(result: dict[str, str | int | bool]) -> bool:  # 逐行註解：判斷 command 或 verify command 是否成功。
    return result.get("exit_code") == 0 and not bool(result.get("timed_out"))  # 逐行註解：exit code 為 0 且沒有 timeout 才算成功。


async def run_agent_task(message: discord.Message, task: str, session: dict):  # 逐行註解：執行完整 Agent loop。
    """AI -> command -> terminal -> feedback -> AI 的 loop，最多 5 次。"""  # 逐行註解：完成或失敗都會在 Discord 顯示總結。
    progress_message = await message.channel.send(f"Agent task started：{task}")  # 逐行註解：建立 Agent 進度訊息。
    terminal_feedback = ""  # 逐行註解：第一輪尚未有 terminal output。
    final_summary = ""  # 逐行註解：保存最後要顯示的總結。
    success = False  # 逐行註解：記錄任務是否成功。
    direct_plan = programmatic_agent_plan(task)  # 逐行註解：先看這是不是程式端已知的常見任務。
    for step in range(1, AGENT_MAX_RETRIES + 1):  # 逐行註解：最多跑 5 輪，避免 infinite loop。
        session["retry_count"] = step - 1  # 逐行註解：更新目前 retry 次數。
        if step == 1 and direct_plan is not None:  # 逐行註解：常見任務第一輪直接使用程式端計畫，不讓模型格式拖垮流程。
            parsed = direct_plan  # 逐行註解：使用可靠的 command 和 verify command。
            raw_reply = json.dumps(parsed, ensure_ascii=False)  # 逐行註解：把程式端計畫也轉成類似模型輸出，方便紀錄。
        else:  # 逐行註解：不是常見任務，或第一輪失敗後，交給 Ollama 專用模型修正。
            prompt = build_agent_prompt(task, session, terminal_feedback)  # 逐行註解：建立送給 Ollama 的 Agent prompt。
            raw_reply = await ask_ollama_text(AGENT_MODEL, prompt, timeout_s=None, include_thinking=False)  # 逐行註解：固定請 gemma4_agent_discord-bot 產生 JSON command，不讓使用者切換模型。
            parsed = parse_agent_response(str(raw_reply))  # 逐行註解：解析 JSON 或相容舊格式。
        if not is_agent_response_complete(parsed):  # 逐行註解：如果格式不完整，就把錯誤回饋給模型進下一輪。
            terminal_feedback = f"FORMAT_ERROR: 你沒有輸出完整四個區塊。原始輸出：\n{raw_reply}"  # 逐行註解：建立格式錯誤 feedback。
            await safe_edit_message(progress_message, f"Agent Step {step}\n格式錯誤，要求模型修正…\n{discord_code_block(raw_reply, 'txt')}")  # 逐行註解：顯示格式錯誤。
            continue  # 逐行註解：進入下一輪。
        command = parsed["command"].strip()  # 逐行註解：取出 command。
        if is_agent_command_done(command):  # 逐行註解：模型判定已完成。
            final_summary = parsed["done"]  # 逐行註解：保存 DONE 區塊當總結。
            success = True  # 逐行註解：標記成功。
            await safe_edit_message(progress_message, f"AI Summary：\n- 做了什麼：{parsed.get('plan')}\n- 有沒有成功：是\n- 結果：{final_summary}")  # 逐行註解：顯示最終成功總結。
            break  # 逐行註解：跳出 loop。
        allowed, reason = validate_agent_command(command)  # 逐行註解：安全檢查 command。
        if not allowed:  # 逐行註解：如果 command 被擋，就回饋給模型修正。
            terminal_feedback = f"SAFETY_BLOCKED: {reason}"  # 逐行註解：建立安全阻擋 feedback。
            await safe_edit_message(progress_message, format_agent_step_message(step, parsed, terminal_feedback))  # 逐行註解：顯示被阻擋的 command。
            continue  # 逐行註解：進入下一輪讓模型修正。
        session["command_history"].append(command)  # 逐行註解：保存執行過的 command。
        await safe_edit_message(progress_message, format_agent_step_message(step, parsed))  # 逐行註解：先顯示計畫和 command。
        result = await execute_agent_command(command)  # 逐行註解：真的執行 command。
        verify_command = (parsed.get("verify") or "").strip()  # 逐行註解：取得驗證 command。
        verify_result = None  # 逐行註解：預設沒有驗證結果。
        verify_success = agent_command_succeeded(result)  # 逐行註解：如果沒有可執行 verify，至少 command 本身要成功。
        if verify_command and not is_agent_command_done(verify_command):  # 逐行註解：有 verify command 時一定要實際執行驗證。
            verify_allowed, verify_reason = validate_agent_command(verify_command)  # 逐行註解：驗證 command 也要過安全黑名單。
            if not verify_allowed:  # 逐行註解：如果 verify command 不安全，就視為驗證失敗。
                verify_result = {"stdout": "", "stderr": f"VERIFY_BLOCKED: {verify_reason}", "exit_code": -1, "timed_out": False, "seconds": 0}  # 逐行註解：建立驗證被阻擋的結果。
                verify_success = False  # 逐行註解：驗證被阻擋不能算成功。
            else:  # 逐行註解：verify command 安全就執行。
                verify_result = await execute_agent_command(verify_command)  # 逐行註解：執行驗證 command。
                verify_success = agent_command_succeeded(verify_result)  # 逐行註解：用驗證結果決定任務是否完成。
        terminal_feedback = format_agent_terminal_feedback(command, result, verify_command, verify_result)  # 逐行註解：把 stdout/stderr/exit code/verify 整理成 feedback。
        session["task_history"].append(f"TASK: {task}\n{terminal_feedback}")  # 逐行註解：保存完整 terminal output 到 task history。
        await safe_edit_message(progress_message, format_agent_step_message(step, parsed, terminal_feedback))  # 逐行註解：把 terminal output 顯示到 Discord。
        if verify_success:  # 逐行註解：程式端驗證成功就直接結束，不再要求模型輸出 DONE。
            final_summary = parsed.get("done") or "任務已完成並通過驗證。"  # 逐行註解：使用模型或程式端提供的完成訊息。
            success = True  # 逐行註解：標記任務成功。
            await safe_edit_message(progress_message, f"AI Summary：\n- 做了什麼：{parsed.get('plan') or task}\n- 有沒有成功：是\n- 結果：{final_summary}")  # 逐行註解：把成功結果 edit 到進度訊息。
            break  # 逐行註解：驗證成功後跳出 Agent loop。
    if not success:  # 逐行註解：如果 5 輪後仍未完成，就顯示失敗。
        final_summary = "Agent task failed：超過 retry 次數或模型沒有明確判定完成。"  # 逐行註解：建立失敗總結。
        await message.channel.send(f"AI Summary：\n- 做了什麼：嘗試執行 `{task}`\n- 有沒有成功：否\n- 失敗原因：{final_summary}")  # 逐行註解：送出失敗總結。
    else:  # 逐行註解：成功時另外補一則簡短總結，避免使用者只看到最後 edit。
        await message.channel.send(f"AI Summary：\n- 做了什麼：{task}\n- 有沒有成功：是\n- 結果：{final_summary}")  # 逐行註解：送出成功總結。


@bot.event  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def on_message(message):  # 逐行註解：定義非同步函式 on_message，可以搭配 await 處理 Discord 或網路等待。
    # messafe 就是一則剛剛出現在頻道的訊息
    if message.author == bot.user: # 如果這則訊息的作者是機器人自己，就不理他（避免無限循環）
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    if not is_allowed_message_user(message):  # 逐行註解：任何一般訊息都先檢查 ALLOWED_USERS 與 SUPER_USERS。
        if should_reply_no_permission_to_message(message):  # 逐行註解：DM 一定回覆；伺服器只有提到 bot 才回覆，避免洗版。
            await message.channel.send(NO_PERMISSION_MESSAGE)  # 逐行註解：回覆需求指定的未授權文字。
        return  # 逐行註解：沒有權限不能進入 Agent、終端、聊天、附件或圖片生成流程。

    # 檢查是否在 Agent 模式；Agent 模式會把下一則訊息當成任務，不走一般聊天。
    if message.author.id in agent_sessions and not message.author.bot:  # 逐行註解：判斷使用者是否已登入 Agent 模式。
        if not require_super_user(message.author):  # 逐行註解：Agent session 屬於敏感功能，執行任務前仍再次確認 SUPER_USERS。
            await message.channel.send(SENSITIVE_PERMISSION_MESSAGE)  # 逐行註解：非超級使用者不能使用 Agent 任務流程。
            return  # 逐行註解：沒有超級權限就停止 Agent 流程。
        session = agent_sessions[message.author.id]  # 逐行註解：取得這個使用者的 Agent session。
        if message.channel != session["channel"]:  # 逐行註解：只處理進入 Agent 模式時同一個頻道的訊息。
            return  # 逐行註解：不同頻道就忽略。
        task = (message.content or "").strip()  # 逐行註解：把使用者訊息當成 Agent 任務。
        if not task:  # 逐行註解：空任務不處理。
            return  # 逐行註解：停止 Agent 流程。
        if task.startswith("/"):  # 逐行註解：slash command 留給 Discord command tree 處理，不當 Agent 任務。
            return  # 逐行註解：停止 Agent 流程。
        session["current_task"] = task  # 逐行註解：保存目前任務。
        session["retry_count"] = 0  # 逐行註解：重設 retry 次數。
        await run_agent_task(message, task, session)  # 逐行註解：執行 AI -> command -> terminal -> feedback loop。
        return  # 逐行註解：Agent 模式下處理完就不進一般聊天。

    # 檢查是否在終端模式
    if message.author.id in terminal_sessions and not message.author.bot:  # 逐行註解：判斷使用者是否在終端模式且不是機器人。
        if not require_super_user(message.author):  # 逐行註解：終端模式可以執行 shell command，必須再次確認 SUPER_USERS。
            await message.channel.send(SENSITIVE_PERMISSION_MESSAGE)  # 逐行註解：非超級使用者不能使用終端模式。
            return  # 逐行註解：沒有超級權限就停止終端流程。
        session = terminal_sessions[message.author.id]  # 逐行註解：取得使用者的終端會話。

        # 檢查是否在同一頻道
        if message.channel != session["channel"]:  # 逐行註解：判斷訊息是否來自同一頻道。
            return  # 逐行註解：如果不同頻道，忽略這條訊息。

        # 執行使用者輸入的指令
        command = (message.content or "").strip()  # 逐行註解：取得使用者輸入的指令。
        if command:  # 逐行註解：判斷指令是否非空。
            try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                result = subprocess.run(  # 逐行註解：執行 shell 指令。
                    command,  # 逐行註解：執行的指令。
                    shell=True,  # 逐行註解：使用 shell 來執行，支援管線、重定向等。
                    capture_output=True,  # 逐行註解：捕捉標準輸出和標準錯誤。
                    text=True,  # 逐行註解：以文字模式回傳結果。
                    cwd=str(Path.home())  # 逐行註解：在使用者家目錄執行。
                )  # 逐行註解：結束 subprocess.run。

                # 組合輸出
                output_line = f"$ {command}"  # 逐行註解：顯示執行的指令。
                if result.stdout:  # 逐行註解：判斷是否有標準輸出。
                    output_line += f"\n{result.stdout}"  # 逐行註解：附加標準輸出。
                if result.stderr:  # 逐行註解：判斷是否有標準錯誤。
                    output_line += f"\n{result.stderr}"  # 逐行註解：附加標準錯誤。

                session["output"].append(output_line)  # 逐行註解：將輸出行加入會話的輸出清單。

            except Exception as e:  # 逐行註解：捕捉執行錯誤。
                session["output"].append(f"$ {command}\n[錯誤] {type(e).__name__}: {str(e)[:200]}")  # 逐行註解：記錄錯誤訊息。

        # 刪除使用者的指令訊息，避免頻道留下聊天記錄
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            await message.delete()  # 逐行註解：刪除使用者發送的訊息。
        except:  # 逐行註解：捕捉刪除訊息時發生的任何錯誤。
            pass  # 逐行註解：忽略刪除失敗的錯誤。

        return  # 逐行註解：終端模式下只處理指令，不繼續其他邏輯。

    user_text = (message.content or "").strip()  # 逐行註解：設定 user_text 這個變數，供後面的流程使用。

    # 伺服器頻道：禁止「你說話就回答」；只能用 /ask 觸發
    # 私訊(DM)：保留原本體驗，直接問直接答
    if message.guild is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    if user_text.lower() in {"clear", "/clear", "清空", "清除記憶"}:
        deleted_keys = clear_user_conversation_memory(message.author.id)
        await message.channel.send(f"已清空聊天記錄（清掉 {deleted_keys} 個記錄區）。")
        return

    identity_answer = build_identity_answer(message.author.id, user_text)
    if identity_answer:
        selected_model_for_memory = dm_user_model.get(message.author.id, DEFAULT_CHAT_MODEL)
        remember_conversation(message.author.id, selected_model_for_memory, user_text, identity_answer)
        await message.channel.send(identity_answer)
        return

    temporary_memory_content = extract_temporary_memory_candidate(user_text)
    if temporary_memory_content:
        stored_content = f"使用者暫時記住：{temporary_memory_content}"
        remember_conversation(message.author.id, SHARED_MEMORY_MODEL, "短期/shared memory", stored_content)
        preview_item = build_memory_json_item(1, stored_content)
        await message.channel.send(f"已寫入短期/shared memory：\n{format_memory_json_code_block([preview_item])}")
        return

    if user_text_has_memory_request(user_text):
        permanent_memory_content = extract_explicit_memory_candidate(user_text)
        if permanent_memory_content:
            async def _send_direct_memory_offer(content: str, view: discord.ui.View):
                await message.channel.send(content, view=view)
            await send_memory_confirmation_offer(message.author.id, permanent_memory_content, _send_direct_memory_offer)
            return

    # 如果是 Discord 指令（例如 /hello），就不要當成一般聊天內容來回覆
    if user_text.startswith("/"):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    if user_text.lower() == "hello" and not (message.attachments or []): # 如果這則訊息的內容是 hello 且沒有附件，才走打招呼快捷回覆
        await message.channel.send("Hey!") # 就回 Hey!
        print("有人打招呼了！") # 在終端機印出「有人打招呼了！」，讓我們知道這件事發生了
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    def _author_label(m: discord.Message) -> str:  # 逐行註解：定義函式 _author_label，把一段會重複使用的流程包起來。
        a = m.author  # 逐行註解：設定 a 這個變數，供後面的流程使用。
        name = (getattr(a, "global_name", None) or getattr(a, "display_name", None) or a.name or "").strip()  # 逐行註解：設定 name 這個變數，供後面的流程使用。
        handle = str(a).strip()  # 逐行註解：設定 handle 這個變數，供後面的流程使用。
        return f"{name} ({handle}) id={a.id}"  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    def _is_dm(message: discord.Message) -> bool:  # 逐行註解：定義函式 _is_dm，把一段會重複使用的流程包起來。
        return message.guild is None  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    async def _start_thinking_effect(channel: discord.abc.Messageable):  # 逐行註解：定義非同步函式 _start_thinking_effect，可以搭配 await 處理 Discord 或網路等待。
        """
        文字模型等待時顯示「思考中...」動態效果。
        回覆完成後 stop() 會把這則等待訊息刪掉，避免頻道留下多餘訊息。
        """
        thinking_msg: discord.Message | None = await channel.send("思考中…")  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        stop_event = asyncio.Event()  # 逐行註解：設定 stop_event 這個變數，供後面的流程使用。

        async def _animator():  # 逐行註解：定義非同步函式 _animator，可以搭配 await 處理 Discord 或網路等待。
            frames = ("思考中", "思考中.", "思考中..", "思考中...")  # 逐行註解：設定 frames 這個變數，供後面的流程使用。
            i = 0  # 逐行註解：設定 i 這個變數，供後面的流程使用。
            while not stop_event.is_set():  # 逐行註解：只要條件還成立，就持續重複執行下面的程式。
                try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                    if thinking_msg is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                        ok = await safe_edit_message(thinking_msg, frames[i % len(frames)])  # 逐行註解：用安全 edit 更新舊版等待動畫，避免 429 時硬重試。
                        if not ok:  # 逐行註解：如果 edit 失敗，就停止這個舊版動畫。
                            stop_event.set()  # 逐行註解：通知動畫停止。
                            return  # 逐行註解：離開動畫 coroutine。
                except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                    print(f"舊版思考動畫更新失敗：{type(e).__name__}: {e}")  # 逐行註解：不要用 pass 吃掉 edit 相關錯誤。
                    stop_event.set()  # 逐行註解：發生錯誤時停止動畫。
                    return  # 逐行註解：離開動畫 coroutine。
                i += 1  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                    await asyncio.wait_for(stop_event.wait(), timeout=0.8)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                except TimeoutError:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                    continue  # 逐行註解：跳過本輪迴圈剩下的內容，直接進入下一輪。

        task = asyncio.create_task(_animator())  # 逐行註解：設定 task 這個變數，供後面的流程使用。

        async def stop():  # 逐行註解：定義非同步函式 stop，可以搭配 await 處理 Discord 或網路等待。
            stop_event.set()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                await task  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            except Exception as e:  # 逐行註解：捕捉 task 收尾錯誤，避免 bot 直接崩潰。
                print(f"舊版思考動畫 task 收尾失敗：{type(e).__name__}: {e}")  # 逐行註解：把錯誤印到後台，不用 pass 吃掉。
            if thinking_msg is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                    await thinking_msg.delete()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                except Exception as e:  # 逐行註解：捕捉刪除舊版思考訊息失敗的錯誤。
                    print(f"舊版思考訊息刪除失敗：{type(e).__name__}: {e}")  # 逐行註解：把刪除失敗原因印到後台。

        return stop  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    # 不是 hello 的話，就依照目前模型回覆（文字顯示思考中，圖片保留生成進度）
    active_ai_run = None  # 逐行註解：保存這次 DM AI 任務的 /stop 登記，結束時要清掉。
    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
        if _is_dm(message):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            selected_model = dm_user_model.get(message.author.id, DEFAULT_CHAT_MODEL)  # 逐行註解：設定 selected_model 這個變數，供後面的流程使用。
        else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
            selected_model = DEFAULT_CHAT_MODEL  # 逐行註解：設定 selected_model 這個變數，供後面的流程使用。

        if _is_dm(message) and selected_model == "x/flux2-klein:latest" and not (message.attachments or []):  # 逐行註解：只有沒有附件時才把圖片模型當成生成圖片，附件訊息要優先走檔案分析。
            img_path: Path | None = None  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            progress_msg: discord.Message | None = None  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            progress_text = ""  # 逐行註解：設定 progress_text 這個變數，供後面的流程使用。
            progress_queue: asyncio.Queue[str] | None = None  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            progress_task: asyncio.Task | None = None  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            percent_task: asyncio.Task | None = None  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                started = time.monotonic()  # 逐行註解：設定 started 這個變數，供後面的流程使用。
                # 顯示生成進度（像終端機那樣一路更新）
                progress_msg = await message.channel.send("0%\n開始生成圖片…")  # 逐行註解：設定 progress_msg 這個變數，供後面的流程使用。

                loop = asyncio.get_running_loop()  # 逐行註解：設定 loop 這個變數，供後面的流程使用。
                progress_queue = asyncio.Queue()  # 逐行註解：設定 progress_queue 這個變數，供後面的流程使用。
                start_ts = time.monotonic()  # 逐行註解：設定 start_ts 這個變數，供後面的流程使用。
                done_flag = False  # 逐行註解：設定 done_flag 這個變數，供後面的流程使用。

                def _progress_cb(s: str):  # 逐行註解：定義函式 _progress_cb，把一段會重複使用的流程包起來。
                    if not s:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
                    # 這個 callback 會在 thread 內被呼叫，用 call_soon_threadsafe 回到 event loop
                    loop.call_soon_threadsafe(progress_queue.put_nowait, s)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

                async def _progress_updater():  # 逐行註解：定義非同步函式 _progress_updater，可以搭配 await 處理 Discord 或網路等待。
                    nonlocal progress_text  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                    assert progress_queue is not None  # 逐行註解：檢查條件是否正確，不正確就讓程式報錯。
                    while True:  # 逐行註解：只要條件還成立，就持續重複執行下面的程式。
                        s = await progress_queue.get()  # 逐行註解：設定 s 這個變數，供後面的流程使用。
                        if s == "__DONE__":  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                            break  # 逐行註解：提前跳出目前這個迴圈。
                        progress_text = (progress_text + "\n" + s).strip()  # 逐行註解：設定 progress_text 這個變數，供後面的流程使用。
                        progress_text = "\n".join(progress_text.splitlines()[-15:])  # 逐行註解：設定 progress_text 這個變數，供後面的流程使用。

                async def _percent_updater():  # 逐行註解：定義非同步函式 _percent_updater，可以搭配 await 處理 Discord 或網路等待。
                    nonlocal progress_text, done_flag  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                    last_percent = -1  # 逐行註解：設定 last_percent 這個變數，供後面的流程使用。
                    while not done_flag:  # 逐行註解：只要條件還成立，就持續重複執行下面的程式。
                        elapsed = time.monotonic() - start_ts  # 逐行註解：設定 elapsed 這個變數，供後面的流程使用。
                        if elapsed < 5:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                            percent = 0  # 逐行註解：設定 percent 這個變數，供後面的流程使用。
                        elif elapsed < 15:  # 逐行註解：前面的 if 不成立時，改檢查這個額外條件。
                            percent = 25  # 逐行註解：設定 percent 這個變數，供後面的流程使用。
                        elif elapsed < 30:  # 逐行註解：前面的 if 不成立時，改檢查這個額外條件。
                            percent = 50  # 逐行註解：設定 percent 這個變數，供後面的流程使用。
                        elif elapsed < 60:  # 逐行註解：前面的 if 不成立時，改檢查這個額外條件。
                            percent = 75  # 逐行註解：設定 percent 這個變數，供後面的流程使用。
                        else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
                            percent = 75  # 逐行註解：設定 percent 這個變數，供後面的流程使用。

                        if percent != last_percent and progress_msg is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                            last_percent = percent  # 逐行註解：設定 last_percent 這個變數，供後面的流程使用。
                            shown = progress_text.strip() or "生成中…"  # 逐行註解：設定 shown 這個變數，供後面的流程使用。
                            if len(shown) > 1800:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                                shown = shown[-1800:]  # 逐行註解：設定 shown 這個變數，供後面的流程使用。
                            await safe_edit_message(progress_msg, f"{last_percent}%\n```{shown}```")  # 逐行註解：圖片生成進度保留百分比，但 edit 改用安全函式。
                        await asyncio.sleep(2)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。

                progress_task = asyncio.create_task(_progress_updater())  # 逐行註解：設定 progress_task 這個變數，供後面的流程使用。
                percent_task = asyncio.create_task(_percent_updater())  # 逐行註解：設定 percent_task 這個變數，供後面的流程使用。

                img_path = await ask_ollama_image(user_text, progress_cb=_progress_cb)  # 逐行註解：設定 img_path 這個變數，供後面的流程使用。
                if progress_queue is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    progress_queue.put_nowait("__DONE__")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                if progress_task is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    await progress_task  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                done_flag = True  # 逐行註解：設定 done_flag 這個變數，供後面的流程使用。
                if percent_task is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    await percent_task  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                if progress_msg is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    await safe_edit_message(progress_msg, "100%\n完成，正在傳送圖片…")  # 逐行註解：圖片生成完成訊息也用安全 edit。
                await message.channel.send(file=discord.File(str(img_path)))  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                remember_conversation(message.author.id, selected_model, user_text, "已生成圖片")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                author_name = (getattr(message.author, "global_name", None) or getattr(message.author, "display_name", None) or message.author.name or "").strip()  # 逐行註解：設定 author_name 這個變數，供後面的流程使用。
                author_account = str(message.author).strip()  # 逐行註解：設定 author_account 這個變數，供後面的流程使用。
                print(  # 逐行註解：把資訊印到終端機後台，方便觀察 bot 執行狀態。
                    "\n".join(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
                        [  # 逐行註解：開始建立一個跨多行的列表資料。
                            "——————————————————",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                            f"使用者名稱：{author_name}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                            f"使用者帳號：{author_account}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                            f"使用者ID：{message.author.id}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                            f"使用者詢問：{user_text}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                            "工具：無",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                            f"使用者選的模型：{selected_model}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                            "AI回覆：已生成圖片",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                            f"思考時間：{time.monotonic() - started:.2f}秒",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                            "——————————————————",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                            "",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                        ]  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
                    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
                )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            finally:  # 逐行註解：不管有沒有錯誤，最後都會執行這個區塊。
                done_flag = True  # 逐行註解：設定 done_flag 這個變數，供後面的流程使用。
                if progress_queue is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                        progress_queue.put_nowait("__DONE__")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                    except Exception as e:  # 逐行註解：捕捉通知進度 queue 失敗的錯誤。
                        print(f"圖片生成進度 queue 收尾失敗：{type(e).__name__}: {e}")  # 逐行註解：把 queue 收尾錯誤印到後台。
                if progress_task is not None and not progress_task.done():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    progress_task.cancel()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                if percent_task is not None and not percent_task.done():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    percent_task.cancel()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                if progress_msg is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                        await progress_msg.delete()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                    except Exception as e:  # 逐行註解：捕捉刪除圖片進度訊息失敗的錯誤。
                        print(f"圖片生成進度訊息刪除失敗：{type(e).__name__}: {e}")  # 逐行註解：把刪除失敗原因印到後台。
                if img_path is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                        img_path = img_path.resolve()  # 逐行註解：設定 img_path 這個變數，供後面的流程使用。
                        if IMAGE_DIR in img_path.parents and img_path.is_file():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                            img_path.unlink(missing_ok=True)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                    except Exception as e:  # 逐行註解：捕捉刪除暫存圖片檔失敗的錯誤。
                        print(f"暫存圖片刪除失敗：{type(e).__name__}: {e}")  # 逐行註解：把暫存檔刪除失敗原因印到後台。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

        message_has_attachments = bool(message.attachments or [])  # 逐行註解：記錄這則 DM 是否有附件，有附件就走自動檔案分析流程。
        thinking_model_state = {"model": selected_model}  # 逐行註解：建立可變模型狀態，讓附件切換 Gemma4 後 Thinking 動畫能即時更新。
        attachment_progress_state = {"text": ""}  # 逐行註解：建立附件分析進度狀態，讓 Thinking 動畫顯示目前正在分析哪個檔案或頁面。

        async def update_attachment_progress(progress_text: str):  # 逐行註解：定義附件分析進度更新函式。
            attachment_progress_state["text"] = (progress_text or "").strip()  # 逐行註解：把最新進度寫進共享狀態，下一個 Thinking frame 會顯示。

        response_message = await message.channel.send(thinking_animation_text(selected_model, THINKING_FRAMES[0]))  # 逐行註解：先送出同一則之後要被 edit 的 Thinking 訊息。
        thinking_stop_event = asyncio.Event()  # 逐行註解：建立停止 Thinking 動畫的事件，正式回答前會先觸發它。
        thinking_task = asyncio.create_task(run_thinking_animation(response_message, thinking_stop_event, thinking_model_state, attachment_progress_state))  # 逐行註解：啟動可顯示最新模型與附件進度的 Thinking 動畫。
        active_ai_run = register_active_ai_run(message.author.id, "DM 聊天", asyncio.current_task(), status_message=response_message, stop_event=thinking_stop_event)  # 逐行註解：登記這次 DM AI 任務，讓 /stop 可以取消。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            # 預設不設逾時：就一直等到 Ollama 回覆（避免回「逾時」）
            timeout_raw = (os.getenv("OLLAMA_TEXT_TIMEOUT_S", "0") or "").strip().lower()  # 逐行註解：設定 timeout_raw 這個變數，供後面的流程使用。
            # OLLAMA_TEXT_TIMEOUT_S=0 / none / off => 永不逾時（就一直等）
            if timeout_raw in {"0", "none", "off", "false", "no", ""}:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                timeout_s = None  # 逐行註解：設定 timeout_s 這個變數，供後面的流程使用。
            else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
                timeout_s = int(timeout_raw)  # 逐行註解：設定 timeout_s 這個變數，供後面的流程使用。
            started = time.monotonic()  # 逐行註解：設定 started 這個變數，供後面的流程使用。
            sep = "——————————————————"  # 逐行註解：設定 sep 這個變數，供後面的流程使用。
            author_name = (getattr(message.author, "global_name", None) or getattr(message.author, "display_name", None) or message.author.name or "").strip()  # 逐行註解：設定 author_name 這個變數，供後面的流程使用。
            author_account = str(message.author).strip()  # 逐行註解：設定 author_account 這個變數，供後面的流程使用。
            author_id = message.author.id  # 逐行註解：設定 author_id 這個變數，供後面的流程使用。
            thinking_process = ""  # 逐行註解：設定 thinking_process 這個變數，供後面的流程使用。
            chart_payload = None  # 逐行註解：預先建立圖表資料變數，只有 AI 回傳 chart JSON 時才會填入。
            if message_has_attachments:  # 逐行註解：如果使用者有上傳檔案，就自動分析所有附件，不需要 /pdf 或其他設定。
                ollama_reply, thinking_process, selected_model, attachment_info = await analyze_message_attachments(  # 逐行註解：下載並分析所有附件，必要時詢問是否切換 Gemma4。
                    message,  # 逐行註解：傳入原始 Discord 訊息，讓檔案分析器可以讀附件與送確認按鈕。
                    selected_model,  # 逐行註解：傳入目前使用者選的模型。
                    user_text,  # 逐行註解：傳入使用者附加文字，作為分析要求。
                    timeout_s,  # 逐行註解：沿用目前 Ollama 文字逾時設定。
                    progress_cb=update_attachment_progress,  # 逐行註解：傳入進度更新函式，顯示正在分析哪個檔案或 PDF 頁面。
                    model_state=thinking_model_state,  # 逐行註解：傳入模型狀態，按下切換後 Thinking 動畫會改顯示 gemma4_thinking。
                )  # 逐行註解：結束附件分析呼叫。
                ollama_reply = str(ollama_reply or "").strip()  # 逐行註解：整理附件分析結果文字。
            else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
                prompt_for_ollama = build_prompt_with_memory(author_id, selected_model, user_text)  # 逐行註解：設定 prompt_for_ollama 這個變數，供後面的流程使用。
                ollama_reply, thinking_process = await ask_ollama_text(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
                    selected_model,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    prompt_for_ollama,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    timeout_s=timeout_s,  # 逐行註解：設定 timeout_s 這個變數，供後面的流程使用。
                    include_thinking=True,  # 逐行註解：設定 include_thinking 這個變數，供後面的流程使用。
                )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
                ollama_reply = ollama_reply.strip()  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。
                attachment_info = ""  # 逐行註解：設定 attachment_info 這個變數，供後面的流程使用。
            response = ollama_reply  # 逐行註解：依除錯需求保留這次 AI 回覆原文變數。
            debug_ai_response(response)  # 逐行註解：印出 === AI RESPONSE === 與完整 AI 回覆。
            chart_payload = parse_chart_reply(ollama_reply, user_text)  # 逐行註解：檢查 AI 回覆圖表 JSON，失敗時用使用者原文解析。
            if not chart_payload:  # 逐行註解：如果模型沒有照規則輸出 JSON，就嘗試從使用者原文保底產生圖表。
                chart_payload = build_chart_payload_from_user_text(user_text)  # 逐行註解：支援「小明80」這類標籤數字黏在一起的資料。
            assistant_memory_text = chart_reply_summary(chart_payload) if chart_payload else ollama_reply  # 逐行註解：圖表回覆存記憶時改存完成訊息，不存原始 JSON。
            remember_conversation(author_id, selected_model, user_text, assistant_memory_text)  # 逐行註解：保存使用者訊息與 AI 回覆，圖表回覆不會把 JSON 放進短期記憶。
            thinking_sec = time.monotonic() - started  # 逐行註解：設定 thinking_sec 這個變數，供後面的流程使用。
            lines = [  # 逐行註解：開始建立一個跨多行的列表資料。
                sep,  # 逐行註解：這行是跨行資料或參數的一個項目。
                f"使用者名稱：{author_name}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                f"使用者帳號：{author_account}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                f"使用者ID：{author_id}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                f"使用者詢問：{user_text}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                f"工具：{'檔案分析' if attachment_info else '無'}",  # 逐行註解：有附件時後台標記為檔案分析，沒有附件時維持原本無工具。
                f"使用者選的模型：{selected_model}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            ]  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            if attachment_info:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                lines.append(f"附件：{attachment_info}")  # 逐行註解：後台列出本次分析的附件檔名與大小。
            if thinking_process:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                lines.append(f"完整 thinking process：\n{thinking_process}")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            lines.extend(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
                [  # 逐行註解：開始建立一個跨多行的列表資料。
                    f"AI回覆：{assistant_memory_text}",  # 逐行註解：後台記錄送給使用者的結果，圖表時不印出原始 JSON。
                    f"思考時間：{thinking_sec:.2f}秒",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    sep,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    "",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                ]  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            print("\n".join(lines))  # 逐行註解：把資訊印到終端機後台，方便觀察 bot 執行狀態。
        finally:  # 逐行註解：不管有沒有錯誤，最後都會執行這個區塊。
            thinking_stop_event.set()  # 逐行註解：AI 回覆已經準備好，先要求 Thinking 動畫停止。
            try:  # 逐行註解：等待動畫 coroutine 真的結束，避免後面逐行顯示時兩邊同時 edit。
                await thinking_task  # 逐行註解：等 Thinking 動畫 task 收尾完成。
            except Exception as e:  # 逐行註解：如果動畫收尾失敗，要印出錯誤，不用 pass 吃掉。
                print(f"Thinking 動畫停止失敗：{type(e).__name__}: {e}")  # 逐行註解：把動畫停止錯誤印到後台。

        # Discord 單則訊息上限約 2000 字；保守切段
        if not ollama_reply:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            ollama_reply = "（我沒有產生任何回覆）"  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。

        finish_active_ai_run(message.author.id, active_ai_run)  # 逐行註解：AI 思考已完成，先移除 /stop 登記，避免答案送出後仍被停止。
        active_ai_run = None  # 逐行註解：標記這次任務已經完成收尾。
        await show_temporary_thinking_process(response_message, thinking_process)  # 逐行註解：如果有 thinking process，就先用 code box 顯示 3 秒，下一步正式回答會覆蓋。
        if chart_payload:  # 逐行註解：如果 AI 回傳的是圖表 JSON，就改送 matplotlib 產生的圖片檔。
            await send_chart_payload_to_message_channel(message.channel, chart_payload, status_message=response_message)  # 逐行註解：用 BytesIO 和 discord.File 把圖表送到原 DM 頻道。
            async def _send_memory_offer(content: str, view: discord.ui.View):  # 逐行註解：建立 DM 圖表回覆後的記憶確認選單送出函式。
                await message.channel.send(content, view=view)  # 逐行註解：在同一個 DM 頻道送出「要不要記憶」按鈕。
            await offer_memory_suggestion_after_answer(author_id, selected_model, user_text, chart_reply_summary(chart_payload), _send_memory_offer)  # 逐行註解：圖表送完後才詢問是否保存永久記憶。
            return  # 逐行註解：圖表已送出後結束，不再把 JSON 當文字顯示。
        await stream_lines_to_message(response_message, ollama_reply)  # 逐行註解：正式回答開始後，一行一行 edit 原本的 Thinking 訊息。
        async def _send_memory_offer(content: str, view: discord.ui.View):  # 逐行註解：建立 DM 記憶確認選單的送出函式。
            await message.channel.send(content, view=view)  # 逐行註解：在同一個 DM 頻道送出「要不要記憶」按鈕。
        await offer_memory_suggestion_after_answer(author_id, selected_model, user_text, ollama_reply, _send_memory_offer)  # 逐行註解：正式回答送完並短暫等待後，才詢問是否保存永久記憶。
    except asyncio.CancelledError:  # 逐行註解：/stop 取消 DM AI 任務時走這裡，避免被一般錯誤處理成例外訊息。
        if active_ai_run is not None:  # 逐行註解：只有已登記的任務才需要更新停止狀態。
            status_message = active_ai_run.get("status_message")  # 逐行註解：取出原本的 Thinking 訊息。
            if status_message is not None:  # 逐行註解：如果有可編輯訊息，就顯示停止結果。
                await safe_edit_message(status_message, STOP_AI_MESSAGE)  # 逐行註解：把原本 Thinking 訊息改成已停止。
        return  # 逐行註解：停止後直接結束，不送任何 AI 回覆。
    except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
        await message.channel.send(f"（發生錯誤：{type(e).__name__}: {str(e)[:300]}）")  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
    finally:  # 逐行註解：不管正常、錯誤或停止，都要清掉 /stop 任務登記。
        finish_active_ai_run(message.author.id, active_ai_run)  # 逐行註解：如果目前登記仍是這次任務，就移除它。
    #!會傳到頻道裡的每個人
#######################指令#######################


async def shutdown_bot_from_quit_command():  # 逐行註解：定義非同步函式 shutdown_bot_from_quit_command，可以搭配 await 處理 Discord 或網路等待。
    """讓 /quit 回覆送出去後，再私訊並關閉 bot。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    await asyncio.sleep(1)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
    await send_shutdown_dm()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
    await bot.close()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。


class QuitPasswordModal(discord.ui.Modal, title="關閉 Discord Bot"):  # 逐行註解：定義類別 QuitPasswordModal，用來描述一種資料或 Discord UI 元件。
    password = discord.ui.TextInput(  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。
        label="請輸入關閉密碼",  # 逐行註解：設定 label 這個變數，供後面的流程使用。
        placeholder="請輸入 Mac 密碼",  # 逐行註解：設定 placeholder 這個變數，供後面的流程使用。
        required=True,  # 逐行註解：設定 required 這個變數，供後面的流程使用。
        max_length=200,  # 逐行註解：設定 max_length 這個變數，供後面的流程使用。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。

    async def on_submit(self, interaction: discord.Interaction):  # 逐行註解：定義非同步函式 on_submit，可以搭配 await 處理 Discord 或網路等待。
        if not require_super_user(interaction.user):  # 逐行註解：關閉 bot 是敏感功能，送出密碼前仍再次確認 SUPER_USERS。
            await interaction.response.send_message(SENSITIVE_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：非超級使用者不能使用關閉功能。
            return  # 逐行註解：沒有超級權限就停止流程。
        if not DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            await interaction.response.send_message(  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                "尚未設定 DISCORD_BOT_QUIT_PASSWORD，bot 不會關閉。",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                ephemeral=True,  # 逐行註解：設定 ephemeral 這個變數，供後面的流程使用。
            )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

        if self.password.value.strip() != DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            await interaction.response.send_message("密碼錯誤，bot 不會關閉。", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

        await interaction.response.send_message("密碼正確，正在關閉 Discord bot。", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        asyncio.create_task(shutdown_bot_from_quit_command())  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。


@tree.command(name="quit", description="輸入密碼後關閉 Discord bot")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def quit_bot(interaction: discord.Interaction):  # 逐行註解：定義非同步函式 quit_bot，可以搭配 await 處理 Discord 或網路等待。
    """輸入 /quit，先跳出密碼視窗；密碼正確才會關閉 bot。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if not require_super_user(interaction.user):  # 逐行註解：/quit 是敏感指令，只允許 SUPER_USERS 開啟密碼視窗。
        await interaction.response.send_message(SENSITIVE_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：非超級使用者回覆指定敏感功能拒絕文字。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    await interaction.response.send_modal(QuitPasswordModal())  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。


@tree.command(name="hello",description="Say hello to the bot")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def hello(interaction: discord.Interaction):  # 逐行註解：定義非同步函式 hello，可以搭配 await 處理 Discord 或網路等待。
    """輸入/hello，機器人會回傳hey!"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    # interaction 就是這次使用指令時送來的資料包
    # 裡面包含是誰按的，在哪裡暗的，指令相關資訊
    if not is_allowed_interaction_user(interaction):  # 逐行註解：hello slash 指令依目前情境檢查權限，統一走 ALLOWED_USERS 與 SUPER_USERS。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：告訴非白名單使用者沒有權限。
        return  # 逐行註解：沒有權限時直接結束，不執行 hello 指令。
    await interaction.response.send_message("Hey!") # 回覆這個指令，內容是 Hello, World!
    #!只會傳給使用者


@tree.command(name="stop", description="停止目前正在思考的 AI 任務")  # 逐行註解：註冊 /stop 指令，讓使用者可以停止自己的 AI 思考。
async def stop_ai(interaction: discord.Interaction):  # 逐行註解：定義 /stop 指令處理函式。
    if not is_allowed_interaction_user(interaction):  # 逐行註解：/stop 讓所有 ALLOWED_USERS 與 SUPER_USERS 都能使用。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：非授權使用者回覆無權限文字。
        return  # 逐行註解：沒有權限就停止指令。
    private_reply = interaction.guild is not None  # 逐行註解：伺服器中用私人回覆，DM 中用一般回覆。
    stopped = await stop_active_ai_run(interaction.user.id)  # 逐行註解：嘗試停止這位使用者目前登記中的 AI 任務。
    if stopped:  # 逐行註解：如果有任務被停止，就回覆成功訊息。
        await interaction.response.send_message(STOP_AI_MESSAGE, ephemeral=private_reply)  # 逐行註解：告知使用者 AI 思考已停止。
        return  # 逐行註解：成功回覆後結束指令。
    await interaction.response.send_message("目前沒有正在思考的 AI 任務。", ephemeral=private_reply)  # 逐行註解：沒有活躍任務時回覆目前無事可停。


@tree.command(name="model", description="(DM only) Select the model for DM chat")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
@discord.app_commands.choices(  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
    model=[  # 逐行註解：開始建立一個跨多行的列表資料。
        discord.app_commands.Choice(name="qwen2.5-coder:1.5b_chat (default text)", value="qwen2.5-coder:1.5b_chat"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="qwen2.5:7b (text)", value="qwen2.5:7b"),  # 逐行註解：加入 qwen2.5:7b 文字模型選項。
        discord.app_commands.Choice(name="gemma4_thinking (text)", value="gemma4_thinking"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="gemma4_Instant (text)", value="gemma4_Instant"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="gemma4_happy (text)", value="gemma4_happy"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="gemma4_angry (text)", value="gemma4_angry"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="gemma4_sad (text)", value="gemma4_sad"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="x/flux2-klein:latest (image)", value="x/flux2-klein:latest"),  # 逐行註解：這行是跨行資料或參數的一個項目。
    ]  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
)  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
async def model(interaction: discord.Interaction, model: discord.app_commands.Choice[str]):  # 逐行註解：定義非同步函式 model，可以搭配 await 處理 Discord 或網路等待。
    """在 DM 模式選擇模型：gemma4 系列文字模型或 x/flux2-klein:latest（生成圖片）"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if not is_allowed_interaction_user(interaction):  # 逐行註解：切換模型依目前情境檢查權限，統一走 ALLOWED_USERS 與 SUPER_USERS。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限時回覆提醒。
        return  # 逐行註解：沒有權限時停止，不切換模型。
    # 只允許 DM 裡使用（避免伺服器頻道亂掉）
    if interaction.guild is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await interaction.response.send_message("請在私訊(DM)裡使用 /model", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    chosen = (model.value or "").strip()  # 逐行註解：設定 chosen 這個變數，供後面的流程使用。
    if chosen not in DM_MODELS:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await interaction.response.send_message("模型不支援", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    dm_user_model[interaction.user.id] = chosen  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    await interaction.response.send_message(f"DM 模式模型已切換為：{chosen}", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。


@tree.command(name="ask", description="Ask the bot (server only); DM can just type directly")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def ask(interaction: discord.Interaction, question: str):  # 逐行註解：定義非同步函式 ask，可以搭配 await 處理 Discord 或網路等待。
    """
    伺服器頻道只允許用 /ask 觸發（避免你說話就回答）。
    回覆使用 ephemeral，避免公開洗版。
    """
    if interaction.guild is None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await interaction.response.send_message("你在 DM 直接打字就會回答，不用 /ask", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    # 只回覆白名單；這裡和一般訊息使用同一個 is_allowed_user，避免權限判斷不一致。
    if not is_allowed_interaction_user(interaction):  # 逐行註解：/ask 依目前情境檢查權限，統一走 ALLOWED_USERS 與 SUPER_USERS。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限時明確回覆，而不是直接不理。
        return  # 逐行註解：沒有權限時結束，不繼續呼叫 Ollama。

    q = (question or "").strip()  # 逐行註解：設定 q 這個變數，供後面的流程使用。
    if not q:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await interaction.response.send_message("請輸入問題", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    identity_answer = build_identity_answer(interaction.user.id, q)
    if identity_answer:
        remember_conversation(interaction.user.id, DEFAULT_CHAT_MODEL, q, identity_answer)
        await interaction.response.send_message(identity_answer, ephemeral=True)
        return

    temporary_memory_content = extract_temporary_memory_candidate(q)
    if temporary_memory_content:
        stored_content = f"使用者暫時記住：{temporary_memory_content}"
        remember_conversation(interaction.user.id, SHARED_MEMORY_MODEL, "短期/shared memory", stored_content)
        preview_item = build_memory_json_item(1, stored_content)
        await interaction.response.send_message(f"已寫入短期/shared memory：\n{format_memory_json_code_block([preview_item])}", ephemeral=True)
        return

    if user_text_has_memory_request(q):
        permanent_memory_content = extract_explicit_memory_candidate(q)
        if permanent_memory_content:
            async def _send_ask_memory_offer(content: str, view: discord.ui.View):
                await interaction.response.send_message(content, view=view, ephemeral=True)
            await send_memory_confirmation_offer(interaction.user.id, permanent_memory_content, _send_ask_memory_offer)
            return

    await interaction.response.defer(ephemeral=True, thinking=True)  # 逐行註解：先 defer，避免 Ollama 等太久讓 Discord 指令逾時。
    response_message = await interaction.followup.send(  # 逐行註解：建立同一則之後要反覆 edit 的 slash followup 訊息。
        thinking_animation_text(DEFAULT_CHAT_MODEL, THINKING_FRAMES[0]),  # 逐行註解：一開始先顯示目前模型名稱和第一格 Thinking 動畫。
        ephemeral=True,  # 逐行註解：/ask 原本是私人回覆，這裡保持 ephemeral。
        wait=True,  # 逐行註解：需要拿到 Message 物件，後面才能 edit 同一則。
    )  # 逐行註解：結束 followup.send 呼叫。
    thinking_stop_event = asyncio.Event()  # 逐行註解：建立停止 Thinking 動畫的事件。
    thinking_task = asyncio.create_task(run_thinking_animation(response_message, thinking_stop_event, DEFAULT_CHAT_MODEL))  # 逐行註解：啟動 /ask 專用 Thinking 動畫 task。
    active_ai_run = register_active_ai_run(interaction.user.id, "/ask", asyncio.current_task(), status_message=response_message, stop_event=thinking_stop_event)  # 逐行註解：登記這次 /ask AI 任務，讓 /stop 可以取消。

    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
        timeout_raw = (os.getenv("OLLAMA_TEXT_TIMEOUT_S", "0") or "").strip().lower()  # 逐行註解：設定 timeout_raw 這個變數，供後面的流程使用。
        if timeout_raw in {"0", "none", "off", "false", "no", ""}:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            timeout_s = None  # 逐行註解：設定 timeout_s 這個變數，供後面的流程使用。
        else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
            timeout_s = int(timeout_raw)  # 逐行註解：設定 timeout_s 這個變數，供後面的流程使用。

        started = time.monotonic()  # 逐行註解：設定 started 這個變數，供後面的流程使用。
        prompt_for_ollama = build_prompt_with_memory(interaction.user.id, DEFAULT_CHAT_MODEL, q)  # 逐行註解：設定 prompt_for_ollama 這個變數，供後面的流程使用。
        ollama_reply, thinking_process = await ask_ollama_text(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
            DEFAULT_CHAT_MODEL,  # 逐行註解：這行是跨行資料或參數的一個項目。
            prompt_for_ollama,  # 逐行註解：這行是跨行資料或參數的一個項目。
            timeout_s=timeout_s,  # 逐行註解：設定 timeout_s 這個變數，供後面的流程使用。
            include_thinking=True,  # 逐行註解：設定 include_thinking 這個變數，供後面的流程使用。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        ollama_reply = ollama_reply.strip()  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。
        response = ollama_reply  # 逐行註解：依除錯需求保留這次 AI 回覆原文變數。
        debug_ai_response(response)  # 逐行註解：印出 === AI RESPONSE === 與完整 AI 回覆。
        chart_payload = parse_chart_reply(ollama_reply, q)  # 逐行註解：檢查 /ask 圖表 JSON，失敗時用 slash 問題原文解析。
        if not chart_payload:  # 逐行註解：如果模型沒有照規則輸出 JSON，就嘗試從 slash 指令問題保底產生圖表。
            chart_payload = build_chart_payload_from_user_text(q)  # 逐行註解：支援「星期一10」這類標籤數字黏在一起的資料。
        assistant_memory_text = chart_reply_summary(chart_payload) if chart_payload else ollama_reply  # 逐行註解：圖表回覆存記憶時改存完成訊息。
        remember_conversation(interaction.user.id, DEFAULT_CHAT_MODEL, q, assistant_memory_text)  # 逐行註解：保存 /ask 對話，圖表回覆不保存原始 JSON。
        thinking_sec = time.monotonic() - started  # 逐行註解：設定 thinking_sec 這個變數，供後面的流程使用。
        sep = "——————————————————"  # 逐行註解：設定 sep 這個變數，供後面的流程使用。
        author_name = (getattr(interaction.user, "global_name", None) or getattr(interaction.user, "display_name", None) or interaction.user.name or "").strip()  # 逐行註解：設定 author_name 這個變數，供後面的流程使用。
        author_account = str(interaction.user).strip()  # 逐行註解：設定 author_account 這個變數，供後面的流程使用。
        print(  # 逐行註解：把資訊印到終端機後台，方便觀察 bot 執行狀態。
            "\n".join(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
                [  # 逐行註解：開始建立一個跨多行的列表資料。
                    sep,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    f"使用者名稱：{author_name}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"使用者帳號：{author_account}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"使用者ID：{interaction.user.id}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"使用者詢問：{q}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    "工具：無",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"使用者選的模型：{DEFAULT_CHAT_MODEL}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    *([f"完整 thinking process：\n{thinking_process}"] if thinking_process else []),  # 逐行註解：這行是跨行資料或參數的一個項目。
                    f"AI回覆：{assistant_memory_text}",  # 逐行註解：後台記錄送給使用者的結果，圖表時不印出原始 JSON。
                    f"思考時間：{thinking_sec:.2f}秒",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    sep,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    "",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                ]  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
    except asyncio.CancelledError:  # 逐行註解：/stop 取消 /ask 任務時走這裡，避免把停止當成錯誤。
        thinking_stop_event.set()  # 逐行註解：先停止 Thinking 動畫。
        try:  # 逐行註解：等待動畫 task 收尾，避免它繼續 edit。
            await thinking_task  # 逐行註解：確保動畫已停止。
        except Exception as stop_error:  # 逐行註解：如果動畫停止失敗，把原因印到後台。
            print(f"/ask Thinking 動畫停止失敗：{type(stop_error).__name__}: {stop_error}")  # 逐行註解：輸出動畫停止錯誤。
        await safe_edit_message(response_message, STOP_AI_MESSAGE)  # 逐行註解：把 /ask 的 Thinking 訊息改成已停止。
        return  # 逐行註解：停止後直接結束，不送 AI 回覆。
    except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
        thinking_stop_event.set()  # 逐行註解：發生錯誤時也要先停止 Thinking 動畫，避免它繼續 edit。
        try:  # 逐行註解：等待動畫 task 收尾。
            await thinking_task  # 逐行註解：確保動畫已經停止。
        except Exception as stop_error:  # 逐行註解：如果動畫停止失敗，把錯誤印到後台。
            print(f"/ask Thinking 動畫停止失敗：{type(stop_error).__name__}: {stop_error}")  # 逐行註解：輸出動畫停止錯誤。
        await safe_edit_message(response_message, f"（發生錯誤：{type(e).__name__}: {str(e)[:300]}）")  # 逐行註解：把同一則 Thinking 訊息改成錯誤訊息。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    finally:  # 逐行註解：不管 /ask 正常完成、錯誤或停止，都要清掉 /stop 任務登記。
        finish_active_ai_run(interaction.user.id, active_ai_run)  # 逐行註解：如果目前登記仍是這次 /ask 任務，就移除它。

    thinking_stop_event.set()  # 逐行註解：Ollama 回覆完成後，先停止 Thinking 動畫。
    try:  # 逐行註解：等待動畫 task 完全結束，避免逐行顯示同時 edit。
        await thinking_task  # 逐行註解：確保只有接下來的 stream_lines_to_message 在 edit response_message。
    except Exception as e:  # 逐行註解：動畫停止失敗時不要靜默，印出錯誤。
        print(f"/ask Thinking 動畫停止失敗：{type(e).__name__}: {e}")  # 逐行註解：把停止錯誤印到後台。

    if not ollama_reply:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        ollama_reply = "（我沒有產生任何回覆）"  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。

    await show_temporary_thinking_process(response_message, thinking_process)  # 逐行註解：如果有 thinking process，就先用 code box 顯示 3 秒，下一步正式回答會覆蓋。
    if chart_payload:  # 逐行註解：如果 /ask 回傳圖表 JSON，就送出實際圖表圖片，不送 JSON 文字。
        await send_chart_payload_to_interaction_channel(interaction, chart_payload, status_message=response_message, ephemeral=True)  # 逐行註解：用 BytesIO 圖表傳到 slash 指令原頻道。
        async def _send_memory_offer(content: str, view: discord.ui.View):  # 逐行註解：建立 /ask 圖表回覆後的記憶確認選單送出函式。
            await interaction.followup.send(content, view=view, ephemeral=True)  # 逐行註解：用 ephemeral followup 送出「要不要記憶」按鈕。
        await offer_memory_suggestion_after_answer(interaction.user.id, DEFAULT_CHAT_MODEL, q, chart_reply_summary(chart_payload), _send_memory_offer)  # 逐行註解：圖表送完後才詢問是否保存永久記憶。
        return  # 逐行註解：圖表已送出後結束，不再把 JSON 當文字顯示。
    await stream_lines_to_message(  # 逐行註解：把 /ask 正式回答一行一行顯示在同一則訊息上。
        response_message,  # 逐行註解：第一則要 edit 的訊息就是原本的 Thinking 訊息。
        ollama_reply,  # 逐行註解：要逐行顯示的 AI 正式回答。
        send_extra=lambda content: interaction.followup.send(content, ephemeral=True, wait=True),  # 逐行註解：如果超過單則長度，就用 ephemeral followup 發下一則。
    )  # 逐行註解：結束逐行顯示呼叫。
    async def _send_memory_offer(content: str, view: discord.ui.View):  # 逐行註解：建立 /ask 記憶確認選單的送出函式。
        await interaction.followup.send(content, view=view, ephemeral=True)  # 逐行註解：用 ephemeral followup 送出「要不要記憶」按鈕。
    await offer_memory_suggestion_after_answer(interaction.user.id, DEFAULT_CHAT_MODEL, q, ollama_reply, _send_memory_offer)  # 逐行註解：正式回答送完並短暫等待後，才詢問是否保存永久記憶。


async def update_web_search_progress(progress_message, content: str):  # 逐行註解：定義非同步函式 update_web_search_progress，可以搭配 await 處理 Discord 或網路等待。
    """更新 /web_search 的同一則進度訊息；失敗時不要中斷搜尋流程。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if progress_message is None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    await safe_edit_message(progress_message, content)  # 逐行註解：用共用安全 edit 更新進度，遇到 429 會尊重 retry_after。


STATE_APPLE_LOADING_ART = r'''
                         .8
                      .888
                    .8888'
                   .8888'
                   888'
                   8'
      .88888888888. .88888888888.
   .8888888888888888888888888888888.
 .8888888888888888888888888888888888.
.&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&'
&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&'
&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&'
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@:
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@:
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@:
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%.
`%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%.
 `00000000000000000000000000000000000'f
  `000000000000000000000000000000000'
   `0000000000000000000000000000000'
     `###########################'
       `#######################'
         `#########''########'
           `""""""'  `"""""'
'''  # 逐行註解：保存 /state 查資料前要顯示的 Apple ASCII 標誌；不要 strip/dedent，避免破壞原始空白與換行。
STATE_LOADING_MIN_SECONDS = 3.0  # 逐行註解：設定 /state Apple 標誌至少要顯示 3 秒。
STATE_REFRESH_INTERVAL_SECONDS = 3.0  # 逐行註解：設定 /state 監控面板每 3 秒重新抓資料並 edit 同一則訊息。


def make_code_block(text: str, lang: str = "txt") -> str:  # 逐行註解：定義一般 code block 包裝函式，集中處理 Discord terminal 風格文字。
    return f"```{lang}\n{text}\n```"  # 逐行註解：原樣放入 code block，不壓縮文字、不改空白。


def make_red_ansi_block(text: str) -> str:  # 逐行註解：定義紅色 ANSI code block，專門給 Apple ASCII logo 使用。
    red = "\u001b[31m"  # 逐行註解：Discord ANSI 紅色控制碼。
    reset = "\u001b[0m"  # 逐行註解：ANSI reset，避免後續文字延續紅色。
    return f"```ansi\n{red}{text}{reset}\n```"  # 逐行註解：用 ansi code block 包起原始文字，不改 logo 內容。


def split_ansi_art(text: str, max_len: int = 1800) -> list[str]:  # 逐行註解：定義 ANSI art 分段函式，避免 Discord 2000 字限制。
    chunks: list[str] = []  # 逐行註解：保存分段後的原始文字區塊。
    current = ""  # 逐行註解：保存目前正在累積的區塊。
    for line in text.splitlines(keepends=True):  # 逐行註解：依換行分段並保留換行符號，不在行中間切 logo。
        candidate = current + line  # 逐行註解：嘗試把目前行接到目前區塊後面。
        if current and len(make_red_ansi_block(candidate)) > max_len:  # 逐行註解：如果包成 ANSI block 後會太長，就先收掉前一段。
            chunks.append(current)  # 逐行註解：保存目前區塊，沒有 rstrip，避免破壞 ASCII 結尾。
            current = line  # 逐行註解：用目前行開新區塊。
        else:  # 逐行註解：如果還沒超過限制，就繼續累積。
            current = candidate  # 逐行註解：更新目前區塊。
    if current:  # 逐行註解：如果最後還有內容，就加入分段。
        chunks.append(current)  # 逐行註解：保存最後一段。
    return [make_red_ansi_block(chunk) for chunk in chunks]  # 逐行註解：每段都重新包紅色 ANSI code block。


async def send_red_ansi_followup(interaction: discord.Interaction, text: str, *, ephemeral: bool = True) -> list[discord.Message]:  # 逐行註解：送出紅色 ANSI code block，超長時依換行安全分段。
    messages: list[discord.Message] = []  # 逐行註解：保存送出的訊息，第一則之後會被 /state edit 成監控面板。
    for block in split_ansi_art(text):  # 逐行註解：逐段送出，不破壞 ASCII art 的行。
        sent = await interaction.followup.send(block, ephemeral=ephemeral, wait=True)  # 逐行註解：送出 ANSI code block 並取得 message 物件。
        messages.append(sent)  # 逐行註解：保存 message 物件。
    return messages  # 逐行註解：回傳所有送出的訊息。


def state_loading_embed() -> discord.Embed:  # 逐行註解：定義函式 state_loading_embed，把 Apple 標誌放進 Embed 避免手機版跑版。
    """把 Apple ASCII art 放進 Embed，在手機版本上會自動調整寬度，避免版面跳位。"""  # 逐行註解：說明這個函式用 Embed 替代 code block 來適配手機螢幕。
    embed = discord.Embed(  # 逐行註解：建立 Discord Embed 物件。
        title="🍎 查詢 Mac 狀態中...",  # 逐行註解：Embed 標題，提示使用者載入中。
        description=make_red_ansi_block(STATE_APPLE_LOADING_ART),  # 逐行註解：如果舊流程呼叫到，也用紅色 ANSI code block 並保留原始 art。
        color=discord.Color.from_rgb(255, 59, 48),  # 逐行註解：Embed 色條也用紅色。
    )  # 逐行註解：結束 Embed 物件建立。
    return embed  # 逐行註解：回傳 Embed 物件。


async def safe_edit_message_embed(message, *, content=None, embed=None, max_retries: int = 2) -> bool:  # 逐行註解：定義可同時編輯 content/embed 的安全 edit 函式。
    """安全編輯 Discord 訊息的 content/embed；遇到 429 會有限等待重試。"""  # 逐行註解：/state 會用它把 Apple 畫面換成監控 Embed。
    for attempt in range(max_retries + 1):  # 逐行註解：最多執行第一次加上有限重試。
        try:  # 逐行註解：開始嘗試 edit 訊息。
            await message.edit(content=content, embed=embed)  # 逐行註解：把同一則訊息換成指定文字或 Embed。
            return True  # 逐行註解：edit 成功就回傳 True。
        except discord.HTTPException as exc:  # 逐行註解：捕捉 Discord HTTP 錯誤。
            if getattr(exc, "status", None) == 429 and attempt < max_retries:  # 逐行註解：遇到 rate limit 且還能重試時，等待 retry_after。
                await asyncio.sleep(discord_retry_after(exc) or 1.0)  # 逐行註解：尊重 Discord 的 retry_after 秒數。
                continue  # 逐行註解：等待後重新嘗試 edit。
            print(f"Discord Embed edit 失敗：{type(exc).__name__}: {exc}")  # 逐行註解：把不可重試錯誤印到後台。
            return False  # 逐行註解：edit 失敗時回傳 False。
        except Exception as exc:  # 逐行註解：捕捉其他非預期錯誤。
            print(f"Discord Embed edit 非預期失敗：{type(exc).__name__}: {exc}")  # 逐行註解：不要靜默吞掉錯誤。
            return False  # 逐行註解：停止這次 edit。
    return False  # 逐行註解：理論上不會走到這裡，保留保險回傳。


def run_monitor_command(command: list[str], *, timeout: int = 5) -> tuple[bool, str, str]:  # 逐行註解：定義執行監控指令的共用函式。
    """執行 macOS 查詢指令；固定 timeout，避免 bot 卡住。"""  # 逐行註解：說明這裡所有 subprocess.run 都會有 timeout。
    try:  # 逐行註解：開始嘗試執行外部指令。
        completed = subprocess.run(  # 逐行註解：執行指定指令並收集 stdout/stderr。
            command,  # 逐行註解：傳入要執行的指令列表。
            capture_output=True,  # 逐行註解：把輸出收回 Python，不直接噴到終端機。
            text=True,  # 逐行註解：用文字模式讀取輸出，方便 regex 解析。
            timeout=timeout,  # 逐行註解：設定 timeout，避免 powermetrics 或其他工具卡住。
            stdin=subprocess.DEVNULL,  # 逐行註解：不允許互動輸入密碼，sudo 需要密碼時會直接失敗。
        )  # 逐行註解：結束 subprocess.run 呼叫。
        output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")  # 逐行註解：合併 stdout 和 stderr，方便 fallback 判斷。
        return completed.returncode == 0, output.strip(), ""  # 逐行註解：回傳成功與否、輸出文字和空錯誤。
    except subprocess.TimeoutExpired as e:  # 逐行註解：捕捉指令超時。
        return False, "", f"timeout after {timeout}s: {' '.join(command)}"  # 逐行註解：回傳 timeout 錯誤，讓呼叫者 fallback。
    except Exception as e:  # 逐行註解：捕捉指令不存在或其他執行錯誤。
        return False, "", f"{type(e).__name__}: {e}"  # 逐行註解：回傳錯誤文字，讓呼叫者 fallback。


def find_monitor_tool(name: str) -> str | None:  # 逐行註解：定義尋找監控工具路徑的函式。
    """尋找 Homebrew 或 user gem 安裝的 CLI 工具。"""  # 逐行註解：iStats 用 gem 安裝時不一定在 PATH，所以要額外找。
    path = shutil.which(name)  # 逐行註解：先用 PATH 找工具。
    if path:  # 逐行註解：如果 PATH 找得到，就直接回傳。
        return path  # 逐行註解：回傳工具完整路徑。
    user_gem_path = str(Path.home() / ".gem" / "ruby" / "2.6.0" / "bin" / name)  # 逐行註解：組出 macOS 系統 Ruby user gem 常見執行檔位置。
    if Path(user_gem_path).is_file():  # 逐行註解：如果 user gem 裡真的有這個執行檔，就使用它。
        return user_gem_path  # 逐行註解：回傳 user gem 工具路徑。
    return None  # 逐行註解：找不到工具時回傳 None。


def normalize_usage_percent(value) -> float | None:  # 逐行註解：定義使用率正規化函式。
    if value is None:  # 逐行註解：沒有值就回傳 None。
        return None  # 逐行註解：回傳沒有資料。
    value = float(value)  # 逐行註解：先轉成 float。
    return value * 100 if 0 <= value <= 1 else value  # 逐行註解：macmon 用 0~1，mactop 用 0~100，這裡統一成百分比。


def get_mactop_stats() -> dict | None:  # 逐行註解：定義讀取 mactop headless JSON 的函式。
    """mactop 是 Apple Silicon 專用工具，可無 sudo 取得 CPU/GPU/溫度/每 CPU core。"""  # 逐行註解：這是 /state 目前最可靠的主要資料來源。
    tool = find_monitor_tool("mactop")  # 逐行註解：尋找 mactop 執行檔。
    if not tool:  # 逐行註解：如果沒有安裝 mactop，就回傳 None 讓其他 fallback 接手。
        return None  # 逐行註解：回傳沒有 mactop 資料。
    ok, output, _ = run_monitor_command([tool, "--headless", "--format", "json", "--count", "1"], timeout=8)  # 逐行註解：執行一次 headless JSON 採樣。
    if not ok or not output:  # 逐行註解：如果 mactop 失敗或沒有輸出，就回傳 None。
        return None  # 逐行註解：回傳沒有 mactop 資料。
    try:  # 逐行註解：嘗試解析 JSON。
        parsed = json.loads(output)  # 逐行註解：把 mactop JSON 字串轉成 Python 資料。
    except json.JSONDecodeError:  # 逐行註解：如果 JSON 壞掉就回傳 None。
        return None  # 逐行註解：回傳沒有 mactop 資料。
    if isinstance(parsed, list) and parsed:  # 逐行註解：mactop --count 1 會回傳 list，取第一筆。
        return parsed[0] if isinstance(parsed[0], dict) else None  # 逐行註解：回傳第一筆 dict。
    if isinstance(parsed, dict):  # 逐行註解：如果工具版本直接回傳 dict，也支援。
        return parsed  # 逐行註解：回傳 mactop dict。
    return None  # 逐行註解：其他格式都視為沒有資料。


def get_macmon_stats() -> dict | None:  # 逐行註解：定義讀取 macmon JSON 的函式。
    """macmon 是 sudoless Apple Silicon 監控工具，作為 mactop 的備用來源。"""  # 逐行註解：當 mactop 失敗時仍可抓 CPU/GPU/RAM/溫度。
    tool = find_monitor_tool("macmon")  # 逐行註解：尋找 macmon 執行檔。
    if not tool:  # 逐行註解：如果沒有安裝 macmon，就回傳 None。
        return None  # 逐行註解：回傳沒有 macmon 資料。
    ok, output, _ = run_monitor_command([tool, "pipe", "--samples", "1", "--soc-info", "-i", "1000"], timeout=5)  # 逐行註解：執行一次 macmon JSON 採樣。
    if not ok or not output:  # 逐行註解：如果 macmon 失敗或沒有輸出，就回傳 None。
        return None  # 逐行註解：回傳沒有 macmon 資料。
    first_line = output.splitlines()[0] if output.splitlines() else output  # 逐行註解：macmon 每筆 JSON 一行，取第一行。
    try:  # 逐行註解：嘗試解析 JSON。
        parsed = json.loads(first_line)  # 逐行註解：把 JSON 字串轉成 dict。
    except json.JSONDecodeError:  # 逐行註解：JSON 解析失敗就回傳 None。
        return None  # 逐行註解：回傳沒有 macmon 資料。
    return parsed if isinstance(parsed, dict) else None  # 逐行註解：只有 dict 才是有效 macmon 資料。


def format_percent(value) -> str:  # 逐行註解：定義百分比格式化函式。
    if value is None:  # 逐行註解：如果沒有資料，就顯示 N/A。
        return "N/A"  # 逐行註解：回傳沒有資料的標記。
    return f"{float(value):.0f}%"  # 逐行註解：把數字轉成整數百分比字串。


def format_temperature(value) -> str:  # 逐行註解：定義溫度格式化函式。
    if value is None:  # 逐行註解：如果沒有溫度資料，就顯示 N/A。
        return "N/A"  # 逐行註解：回傳沒有資料的標記。
    return f"{float(value):.1f}°C"  # 逐行註解：把溫度統一成一位小數，避免顯示太長。


def usage_bar(value, *, width: int = 10) -> str:  # 逐行註解：定義工程師監控面板用的小長條。
    if value is None:  # 逐行註解：如果沒有使用率資料，就不偽造長條。
        return "N/A".ljust(width)  # 逐行註解：回傳 N/A 並補齊寬度。
    filled = max(0, min(width, round(float(value) / 100 * width)))  # 逐行註解：依百分比計算要填幾格。
    return "█" * filled + "░" * (width - filled)  # 逐行註解：用實心和空心方塊組成長條。


def format_bytes_gb(byte_count: int | float | None) -> str:  # 逐行註解：定義 bytes 轉 GB 的格式化函式。
    if byte_count is None:  # 逐行註解：沒有數值時顯示 N/A。
        return "N/A"  # 逐行註解：回傳沒有資料的標記。
    return f"{float(byte_count) / (1024 ** 3):.1f} GB"  # 逐行註解：把 bytes 換算成 GB。


def parse_first_float(patterns: list[str], text: str) -> float | None:  # 逐行註解：定義從文字中抓第一個浮點數的工具函式。
    for pattern in patterns:  # 逐行註解：逐一嘗試不同工具可能輸出的格式。
        match = re.search(pattern, text, re.IGNORECASE)  # 逐行註解：用 regex 搜尋目前格式。
        if match:  # 逐行註解：如果找到數字，就回傳。
            return float(match.group(1))  # 逐行註解：把抓到的數字轉成 float。
    return None  # 逐行註解：全部格式都找不到時回傳 None。


def latest_line_starting_with(text: str, prefix: str) -> str:  # 逐行註解：從指令輸出抓最後一行指定 prefix，top 第二筆 sample 會在後面。
    lines = [line for line in (text or "").splitlines() if line.startswith(prefix)]  # 逐行註解：保留所有符合 prefix 的行。
    return lines[-1] if lines else ""  # 逐行註解：回傳最後一行，沒有就回空字串。


def parse_top_cpu_usage(line: str) -> dict:  # 逐行註解：解析 top 的 CPU usage 行，取得 user/sys/idle。
    match = re.search(r"CPU usage:\s*([0-9.]+)% user,\s*([0-9.]+)% sys,\s*([0-9.]+)% idle", line or "")  # 逐行註解：比對 macOS top CPU 行。
    if not match:  # 逐行註解：如果格式不符合，就回傳空 dict。
        return {}  # 逐行註解：代表解析失敗。
    user = float(match.group(1))  # 逐行註解：讀取 user percentage。
    sys_value = float(match.group(2))  # 逐行註解：讀取 sys percentage。
    idle = float(match.group(3))  # 逐行註解：讀取 idle percentage。
    return {"user": user, "sys": sys_value, "idle": idle, "total": user + sys_value}  # 逐行註解：總使用率採 user + sys，對齊 Activity Monitor/top。


def memory_unit_to_bytes(value: str, unit: str) -> float:  # 逐行註解：把 top 的 K/M/G/T 記憶體單位轉成 bytes。
    multiplier = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}.get((unit or "B").upper(), 1)  # 逐行註解：依單位決定倍率。
    return float(value) * multiplier  # 逐行註解：回傳 bytes。


def parse_top_physmem(line: str) -> dict:  # 逐行註解：解析 top 的 PhysMem 行，作為 RAM 資料來源比對用。
    match = re.search(r"PhysMem:\s*([0-9.]+)([KMGT]?) used.*?,\s*([0-9.]+)([KMGT]?) unused", line or "", re.IGNORECASE)  # 逐行註解：抓 used 和 unused。
    if not match:  # 逐行註解：如果格式不符合，就回空 dict。
        return {}  # 逐行註解：代表解析失敗。
    used = memory_unit_to_bytes(match.group(1), match.group(2))  # 逐行註解：轉換 used bytes。
    unused = memory_unit_to_bytes(match.group(3), match.group(4))  # 逐行註解：轉換 unused bytes。
    total = used + unused if used is not None and unused is not None else None  # 逐行註解：top 顯示的總量是 used + unused 的近似。
    percent = used / total * 100 if total else None  # 逐行註解：計算 top 視角的使用百分比。
    return {"used": used, "unused": unused, "total": total, "percent": percent}  # 逐行註解：回傳解析結果。


def short_debug_text(text: str, limit: int = 1200) -> str:  # 逐行註解：把 debug raw output 控制長度，避免 Discord 爆字數。
    if not text:  # 逐行註解：沒有文字就回 N/A。
        return "N/A"  # 逐行註解：回傳無資料標記。
    return text if len(text) <= limit else text[:limit] + "\n...<truncated>"  # 逐行註解：只截 debug 顯示，不截原始 stats dict。


def get_cpu_stats(mactop_sample: dict | None = None, macmon_sample: dict | None = None, top_output: str = "") -> dict:  # 逐行註解：定義取得 CPU 使用率的函式。
    """CPU 總量優先用 top 第二筆 sample；per-core 用同一次 psutil percpu sample。"""  # 逐行註解：避免 total/per-core 用不同 timing 造成明顯不一致。
    top_line = latest_line_starting_with(top_output, "CPU usage:")  # 逐行註解：讀取 top 第二筆 CPU 行。
    top_parsed = parse_top_cpu_usage(top_line)  # 逐行註解：解析 top user/sys/idle。
    psutil_error = ""  # 逐行註解：保存 psutil 缺套件或讀取錯誤。
    psutil_total = None  # 逐行註解：保存 psutil per-core 平均值。
    cores: list[float] = []  # 逐行註解：保存每核心使用率。
    try:  # 逐行註解：嘗試使用 psutil 取得同一次 per-core sample。
        import psutil  # 逐行註解：psutil 負責每核心 CPU 使用率。
        cores = [float(value) for value in psutil.cpu_percent(interval=1, percpu=True)]  # 逐行註解：一次取得所有核心，不再另外取 total。
        psutil_total = sum(cores) / len(cores) if cores else None  # 逐行註解：psutil total 只當 debug 對照，不當主 total。
    except ImportError:  # 逐行註解：如果 psutil 沒安裝，就保留提示。
        psutil_error = "請先安裝：pip install psutil"  # 逐行註解：讓 /state 底部可提醒。
    except Exception as e:  # 逐行註解：其他 psutil 例外也不要讓 bot 崩潰。
        psutil_error = f"psutil error: {type(e).__name__}: {e}"  # 逐行註解：保存錯誤文字。
    if top_parsed.get("total") is not None:  # 逐行註解：top 成功時，CPU total 優先使用 top user+sys。
        return {"total": top_parsed["total"], "cores": cores, "source": "top + psutil", "error": psutil_error, "top_raw": top_line, "top_parsed": top_parsed, "psutil_total": psutil_total, "psutil_cores": cores}  # 逐行註解：回傳 top 主值和 psutil core。
    if psutil_total is not None:  # 逐行註解：top 失敗但 psutil 成功時，用 psutil per-core 平均。
        return {"total": psutil_total, "cores": cores, "source": "psutil", "error": psutil_error, "top_raw": top_line, "top_parsed": top_parsed, "psutil_total": psutil_total, "psutil_cores": cores}  # 逐行註解：回傳 psutil fallback。
    if mactop_sample:  # 逐行註解：psutil/top 都失敗時才 fallback 到 mactop。
        total = normalize_usage_percent(mactop_sample.get("cpu_usage"))  # 逐行註解：取得 mactop CPU 總使用率。
        mactop_cores = [normalize_usage_percent(value) for value in (mactop_sample.get("core_usages") or [])]  # 逐行註解：取得 mactop 每核心。
        if total is not None:  # 逐行註解：如果 mactop 有資料就使用。
            return {"total": total, "cores": [value for value in mactop_cores if value is not None], "source": "mactop fallback", "error": psutil_error, "top_raw": top_line, "top_parsed": top_parsed, "psutil_total": psutil_total, "psutil_cores": cores}  # 逐行註解：回傳 mactop fallback。
    if macmon_sample:  # 逐行註解：最後 fallback 到 macmon cluster。
        total = normalize_usage_percent(macmon_sample.get("cpu_usage_pct"))  # 逐行註解：取得 macmon CPU 總使用率。
        cluster_cores = []  # 逐行註解：建立 cluster 使用率清單。
        if isinstance(macmon_sample.get("ecpu_usage"), list) and len(macmon_sample["ecpu_usage"]) >= 2:  # 逐行註解：解析 E-core cluster。
            cluster_cores.append(normalize_usage_percent(macmon_sample["ecpu_usage"][1]))  # 逐行註解：加入 E-core cluster。
        if isinstance(macmon_sample.get("pcpu_usage"), list) and len(macmon_sample["pcpu_usage"]) >= 2:  # 逐行註解：解析 P-core cluster。
            cluster_cores.append(normalize_usage_percent(macmon_sample["pcpu_usage"][1]))  # 逐行註解：加入 P-core cluster。
        if total is not None:  # 逐行註解：如果 macmon 有資料就使用。
            return {"total": total, "cores": [value for value in cluster_cores if value is not None], "source": "macmon fallback", "error": psutil_error, "top_raw": top_line, "top_parsed": top_parsed, "psutil_total": psutil_total, "psutil_cores": cores}  # 逐行註解：回傳 macmon fallback。
    return {"total": None, "cores": [], "source": "N/A", "error": psutil_error, "top_raw": top_line, "top_parsed": top_parsed, "psutil_total": psutil_total, "psutil_cores": cores}  # 逐行註解：全部失敗才回傳 N/A。


def get_ram_stats(mactop_sample: dict | None = None, macmon_sample: dict | None = None, top_output: str = "") -> dict:  # 逐行註解：定義取得 RAM 使用量的函式。
    """使用 psutil available 口徑計算 RAM，並保留 top PhysMem raw 供內部比對。"""  # 逐行註解：避免 mem.used 和 mem.percent 在 macOS 上看起來互相矛盾。
    top_line = latest_line_starting_with(top_output, "PhysMem:")  # 逐行註解：讀取 top 第二筆 PhysMem 行。
    top_parsed = parse_top_physmem(top_line)  # 逐行註解：解析 top 記憶體 raw，供 debug 比對。
    try:  # 逐行註解：先嘗試匯入 psutil，符合 /state 原本 RAM 資料來源需求。
        import psutil  # 逐行註解：psutil 負責記憶體統計。
        mem = psutil.virtual_memory()  # 逐行註解：讀取目前記憶體狀態。
        used = mem.total - mem.available  # 逐行註解：用 total - available 對齊 psutil percent，避免 macOS mem.used 造成畫面不一致。
        return {"used": used, "total": mem.total, "percent": mem.percent, "source": "psutil", "error": "", "top_raw": top_line, "top_parsed": top_parsed}  # 逐行註解：回傳 psutil RAM 資料。
    except ImportError:  # 逐行註解：如果 psutil 沒安裝，先記錄錯誤，後面仍嘗試 mactop/macmon fallback。
        psutil_error = "請先安裝：pip install psutil"  # 逐行註解：保存缺套件提示。
    if mactop_sample and isinstance(mactop_sample.get("memory"), dict):  # 逐行註解：優先使用 mactop memory 資料。
        mem = mactop_sample["memory"]  # 逐行註解：取出 mactop memory dict。
        total = mem.get("total")  # 逐行註解：讀取 RAM 總量。
        used = mem.get("used")  # 逐行註解：讀取 RAM 使用量。
        if total and used is not None:  # 逐行註解：如果總量和使用量都有，就計算百分比。
            return {"used": used, "total": total, "percent": float(used) / float(total) * 100, "source": "mactop", "error": psutil_error, "top_raw": top_line, "top_parsed": top_parsed}  # 逐行註解：回傳 mactop RAM 資料。
    if macmon_sample and isinstance(macmon_sample.get("memory"), dict):  # 逐行註解：mactop 不可用時改用 macmon memory。
        mem = macmon_sample["memory"]  # 逐行註解：取出 macmon memory dict。
        total = mem.get("ram_total")  # 逐行註解：讀取 RAM 總量。
        used = mem.get("ram_usage")  # 逐行註解：讀取 RAM 使用量。
        if total and used is not None:  # 逐行註解：如果總量和使用量都有，就計算百分比。
            return {"used": used, "total": total, "percent": float(used) / float(total) * 100, "source": "macmon", "error": psutil_error, "top_raw": top_line, "top_parsed": top_parsed}  # 逐行註解：回傳 macmon RAM 資料。
    return {"used": None, "total": None, "percent": None, "source": "N/A", "error": psutil_error, "top_raw": top_line, "top_parsed": top_parsed}  # 逐行註解：全部來源都失敗時才回傳 N/A。


def get_battery_stats() -> dict:  # 逐行註解：定義取得電池狀態的函式。
    """優先使用 pmset -g batt 解析電量、供電來源、充電狀態與剩餘時間。"""  # 逐行註解：電池資料來源按需求使用 pmset。
    ok, output, error = run_monitor_command(["pmset", "-g", "batt"], timeout=3)  # 逐行註解：執行 pmset 查詢電池資訊。
    data = {"power": "N/A", "level": None, "state": "N/A", "is_plugged": "N/A", "time_remaining": "N/A", "source": "N/A"}  # 逐行註解：建立預設 N/A 結果。
    if not ok and not output:  # 逐行註解：如果 pmset 沒有成功也沒有輸出，就回傳 N/A。
        data["error"] = error  # 逐行註解：保留錯誤原因給後台或顯示使用。
        return data  # 逐行註解：回傳電池資料。
    power_match = re.search(r"Now drawing from '([^']+)'", output)  # 逐行註解：解析 AC Power 或 Battery Power。
    percent_match = re.search(r"(\d+)%", output)  # 逐行註解：解析電池百分比。
    state_match = re.search(r";\s*([^;,\n]+)", output)  # 逐行註解：解析 charging、charged、discharging、not charging 等狀態。
    time_match = re.search(r"(\d+:\d+)\s+remaining", output)  # 逐行註解：解析剩餘時間，如果 pmset 有提供。
    if power_match:  # 逐行註解：如果有解析到供電來源，就保存。
        data["power"] = power_match.group(1)  # 逐行註解：設定 Power 欄位。
        data["is_plugged"] = "Yes" if data["power"] == "AC Power" else "No"  # 逐行註解：依 AC Power 判斷是否接電。
    if percent_match:  # 逐行註解：如果有解析到百分比，就保存。
        data["level"] = float(percent_match.group(1))  # 逐行註解：設定電池百分比。
    if state_match:  # 逐行註解：如果有解析到充電狀態，就保存。
        data["state"] = state_match.group(1).strip()  # 逐行註解：設定 charging/charged/discharging 等狀態。
    if time_match:  # 逐行註解：如果有解析到剩餘時間，就保存。
        data["time_remaining"] = time_match.group(1)  # 逐行註解：設定剩餘時間。
    data["source"] = "pmset"  # 逐行註解：記錄資料來源是 pmset。
    data["raw"] = output  # 逐行註解：保留原始輸出，方便後續排查。
    return data  # 逐行註解：回傳電池資料。


def parse_temperature_from_text(text: str, *, kind: str) -> float | None:  # 逐行註解：定義從工具輸出解析 CPU/GPU 溫度的函式。
    label = "GPU" if kind == "gpu" else "CPU"  # 逐行註解：依 kind 決定要找 CPU 或 GPU。
    return parse_first_float(  # 逐行註解：用多個 regex fallback 抓溫度。
        [
            rf"{label}[^\n:]*temperature[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*(?:C|°C)?",  # 逐行註解：解析 powermetrics 常見 temperature 格式。
            rf"{label}[^\n:]*temp[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*(?:C|°C)?",  # 逐行註解：解析 istats 常見 temp 格式。
            rf"{label}[^\n]*die[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*(?:C|°C)?",  # 逐行註解：解析 die temperature 格式。
        ],
        text,  # 逐行註解：傳入要解析的輸出文字。
    )  # 逐行註解：結束 parse_first_float 呼叫。


def parse_mactop_dump_temps(text: str) -> tuple[float | None, float | None]:  # 逐行註解：定義解析 mactop --dump-temps 的函式。
    cpu_values: list[float] = []  # 逐行註解：保存所有 CPU 相關溫度。
    gpu_values: list[float] = []  # 逐行註解：保存所有 GPU 相關溫度。
    for line in text.splitlines():  # 逐行註解：逐行解析 mactop 的溫度表。
        if "CPU" not in line and "GPU" not in line:  # 逐行註解：不是 CPU/GPU 溫度行就跳過。
            continue  # 逐行註解：繼續下一行。
        match = re.search(r"(-?[0-9]+(?:\.[0-9]+)?)°C", line)  # 逐行註解：抓出攝氏溫度。
        if not match:  # 逐行註解：沒有溫度數字就跳過。
            continue  # 逐行註解：繼續下一行。
        value = float(match.group(1))  # 逐行註解：把溫度轉成 float。
        if value <= 0:  # 逐行註解：0 或負數通常是無效感測器，不當成真實溫度。
            continue  # 逐行註解：跳過無效值。
        if "GPU" in line:  # 逐行註解：如果這行是 GPU 類別，就放入 GPU 溫度。
            gpu_values.append(value)  # 逐行註解：加入 GPU 溫度清單。
        if "CPU" in line:  # 逐行註解：如果這行是 CPU 類別，就放入 CPU 溫度。
            cpu_values.append(value)  # 逐行註解：加入 CPU 溫度清單。
    return (max(cpu_values) if cpu_values else None, max(gpu_values) if gpu_values else None)  # 逐行註解：回傳 CPU/GPU 最高溫度。


def temperatures_from_mactop_sample(mactop_sample: dict | None) -> tuple[float | None, float | None]:  # 逐行註解：從 mactop JSON 抓 CPU/GPU 最高溫度。
    if not mactop_sample:  # 逐行註解：沒有 mactop sample 就回空值。
        return None, None  # 逐行註解：回傳沒有溫度資料。
    cpu_values: list[float] = []  # 逐行註解：保存 CPU 相關感測器溫度。
    gpu_values: list[float] = []  # 逐行註解：保存 GPU 相關感測器溫度。
    for item in mactop_sample.get("temperatures") or []:  # 逐行註解：mactop temperatures 會列出多組感測器。
        if not isinstance(item, dict):  # 逐行註解：不是 dict 就跳過。
            continue  # 逐行註解：繼續下一個感測器群組。
        group = str(item.get("group") or "").lower()  # 逐行註解：讀取感測器群組名稱。
        value = item.get("max_celsius", item.get("avg_celsius"))  # 逐行註解：優先取最高溫，沒有才取平均溫。
        if value is None:  # 逐行註解：沒有溫度數字就跳過。
            continue  # 逐行註解：繼續下一個感測器群組。
        value = float(value)  # 逐行註解：轉成 float。
        if value <= 0:  # 逐行註解：0 或負數通常是無效感測器。
            continue  # 逐行註解：跳過無效溫度。
        if "cpu" in group:  # 逐行註解：CPU 群組放入 CPU 清單。
            cpu_values.append(value)  # 逐行註解：加入 CPU 溫度。
        if "gpu" in group:  # 逐行註解：GPU 群組放入 GPU 清單。
            gpu_values.append(value)  # 逐行註解：加入 GPU 溫度。
    soc = mactop_sample.get("soc_metrics") or {}  # 逐行註解：如果 temperatures 沒有，fallback 到 SoC metrics。
    if soc.get("cpu_temp") is not None:  # 逐行註解：讀取 SoC CPU 溫度。
        cpu_values.append(float(soc["cpu_temp"]))  # 逐行註解：加入 CPU 溫度。
    if soc.get("gpu_temp") is not None:  # 逐行註解：讀取 SoC GPU 溫度。
        gpu_values.append(float(soc["gpu_temp"]))  # 逐行註解：加入 GPU 溫度。
    return (max(cpu_values) if cpu_values else None, max(gpu_values) if gpu_values else None)  # 逐行註解：回傳 CPU/GPU 最高溫。


def get_temperature_stats(mactop_sample: dict | None = None, macmon_sample: dict | None = None, smc_output: str = "") -> dict:  # 逐行註解：定義取得 CPU/GPU 最高溫度的函式。
    """優先嘗試非互動 powermetrics smc；失敗後才 fallback mactop/macmon/其他工具。"""  # 逐行註解：全部失敗才顯示 N/A，不偽造數值。
    attempts = ["powermetrics smc"]  # 逐行註解：記錄第一順位資料來源。
    cpu_temp = parse_temperature_from_text(smc_output, kind="cpu") if smc_output else None  # 逐行註解：從 powermetrics smc 解析 CPU 溫度。
    gpu_temp = parse_temperature_from_text(smc_output, kind="gpu") if smc_output else None  # 逐行註解：從 powermetrics smc 解析 GPU 溫度。
    if cpu_temp is not None or gpu_temp is not None:  # 逐行註解：powermetrics 有任何溫度就使用。
        return {"cpu_max": cpu_temp, "gpu_max": gpu_temp, "source": "powermetrics smc", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：回傳 powermetrics 溫度。
    if mactop_sample:  # 逐行註解：powermetrics 失敗時，fallback 到 mactop headless JSON。
        attempts.append("mactop")  # 逐行註解：記錄嘗試過 mactop。
        cpu_temp, gpu_temp = temperatures_from_mactop_sample(mactop_sample)  # 逐行註解：讀取 mactop CPU/GPU 最高溫。
        if cpu_temp is not None or gpu_temp is not None:  # 逐行註解：如果 mactop 有溫度資料就回傳。
            return {"cpu_max": cpu_temp, "gpu_max": gpu_temp, "source": "mactop", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：回傳 mactop 溫度資料。
    if find_monitor_tool("mactop"):  # 逐行註解：如果 mactop 存在，再用 dump-temps 取得更多 SMC 溫度。
        attempts.append("mactop --dump-temps")  # 逐行註解：記錄嘗試過 mactop dump。
        ok_mt, out_mt, _ = run_monitor_command([find_monitor_tool("mactop"), "--dump-temps"], timeout=5)  # 逐行註解：執行 mactop 溫度診斷輸出。
        cpu_dump, gpu_dump = parse_mactop_dump_temps(out_mt) if out_mt else (None, None)  # 逐行註解：解析 mactop 溫度表。
        if ok_mt and (cpu_dump is not None or gpu_dump is not None):  # 逐行註解：如果 dump-temps 有任何有效資料，就回傳。
            return {"cpu_max": cpu_dump, "gpu_max": gpu_dump, "source": "mactop --dump-temps", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：回傳 mactop dump 溫度資料。
    if macmon_sample and isinstance(macmon_sample.get("temp"), dict):  # 逐行註解：mactop 不可用時使用 macmon 溫度。
        attempts.append("macmon")  # 逐行註解：記錄嘗試過 macmon。
        temp = macmon_sample["temp"]  # 逐行註解：取出 macmon temp dict。
        cpu_temp = temp.get("cpu_temp_avg")  # 逐行註解：讀取 CPU 平均溫度。
        gpu_temp = temp.get("gpu_temp_avg")  # 逐行註解：讀取 GPU 平均溫度。
        if cpu_temp is not None or gpu_temp is not None:  # 逐行註解：如果 macmon 有溫度資料，就回傳。
            return {"cpu_max": cpu_temp, "gpu_max": gpu_temp, "source": "macmon", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：回傳 macmon 溫度資料。
    if find_monitor_tool("istats"):  # 逐行註解：如果有 istats，就嘗試解析溫度。
        attempts.append("istats")  # 逐行註解：記錄嘗試過 istats。
        ok_i, out_i, _ = run_monitor_command([find_monitor_tool("istats"), "--no-graphs"], timeout=5)  # 逐行註解：執行 istats。
        cpu_temp = parse_temperature_from_text(out_i, kind="cpu") if out_i else None  # 逐行註解：解析 CPU 溫度。
        gpu_temp = parse_temperature_from_text(out_i, kind="gpu") if out_i else None  # 逐行註解：解析 GPU 溫度。
        if ok_i and (cpu_temp is not None or gpu_temp is not None):  # 逐行註解：如果 istats 有資料就回傳。
            return {"cpu_max": cpu_temp, "gpu_max": gpu_temp, "source": "istats", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：回傳 istats 溫度。
    if find_monitor_tool("osx-cpu-temp"):  # 逐行註解：如果 CPU 溫度仍沒有且有 osx-cpu-temp，就嘗試它。
        attempts.append("osx-cpu-temp")  # 逐行註解：記錄嘗試過 osx-cpu-temp。
        ok_c, out_c, _ = run_monitor_command([find_monitor_tool("osx-cpu-temp")], timeout=3)  # 逐行註解：執行 osx-cpu-temp。
        cpu_temp = parse_first_float([r"([0-9]+(?:\.[0-9]+)?)\s*°?C"], out_c) if out_c else None  # 逐行註解：解析 osx-cpu-temp 輸出。
        if ok_c and cpu_temp is not None:  # 逐行註解：如果成功取得 CPU 溫度就回傳。
            return {"cpu_max": cpu_temp, "gpu_max": None, "source": "osx-cpu-temp", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：回傳 CPU 溫度，GPU 仍 N/A。
    attempts.append("ioreg")  # 逐行註解：最後記錄 ioreg fallback；macOS 通常不暴露 CPU/GPU 溫度。
    return {"cpu_max": None, "gpu_max": None, "source": "N/A", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：全部取不到才回傳 N/A。


def parse_fans_from_text(text: str) -> list[dict[str, str]]:  # 逐行註解：定義解析風扇 RPM 的函式。
    fans: list[dict[str, str]] = []  # 逐行註解：建立風扇資料清單。
    for index, match in enumerate(re.finditer(r"(?:Fan\s*(\d+)?[^\n:]*[: ]\s*)?([0-9]{1,5})\s*RPM", text, re.IGNORECASE), start=1):  # 逐行註解：尋找所有 RPM 數字，0 RPM 也算實際讀到的值。
        fan_id = match.group(1) or str(index)  # 逐行註解：如果工具有提供風扇編號就使用，沒有就依序編號。
        fans.append({"name": f"Fan {fan_id}", "rpm": match.group(2)})  # 逐行註解：加入風扇名稱和 RPM。
    return fans  # 逐行註解：回傳風扇清單。


def get_fan_stats(mactop_sample: dict | None = None, smc_output: str = "") -> dict:  # 逐行註解：定義取得風扇 RPM 的函式。
    """優先嘗試非互動 powermetrics smc；失敗後 fallback mactop、istats、smc。"""  # 逐行註解：全部失敗才回傳 N/A。
    attempts = ["powermetrics smc"]  # 逐行註解：保存嘗試過的資料來源。
    fans = parse_fans_from_text(smc_output) if smc_output else []  # 逐行註解：先解析 powermetrics smc 的 fan RPM。
    if fans:  # 逐行註解：如果 powermetrics 有風扇資料，就直接回傳。
        return {"fans": fans, "source": "powermetrics smc", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：回傳 powermetrics 風扇資料。
    if mactop_sample and isinstance(mactop_sample.get("fans"), list):  # 逐行註解：powermetrics 失敗時 fallback 到 mactop JSON 內的風扇資料。
        attempts.append("mactop")  # 逐行註解：記錄嘗試過 mactop。
        fans = []  # 逐行註解：建立 mactop 風扇資料清單。
        for index, fan in enumerate(mactop_sample["fans"], start=1):  # 逐行註解：逐一處理 mactop 回傳的 fan dict。
            if not isinstance(fan, dict):  # 逐行註解：如果項目不是 dict，就跳過。
                continue  # 逐行註解：繼續下一個 fan。
            rpm = fan.get("rpm")  # 逐行註解：讀取目前 RPM。
            if rpm is None:  # 逐行註解：沒有 RPM 就跳過。
                continue  # 逐行註解：繼續下一個 fan。
            name = fan.get("name") or f"Fan {fan.get('id', index)}"  # 逐行註解：優先使用工具提供名稱，沒有就用編號。
            fans.append({"name": str(name), "rpm": str(rpm)})  # 逐行註解：加入風扇名稱和 RPM；0 RPM 也是真實資料。
        if fans:  # 逐行註解：如果 mactop 有風扇資料，就直接回傳。
            return {"fans": fans, "source": "mactop", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：回傳 mactop 風扇資料。
    istats_tool = find_monitor_tool("istats")  # 逐行註解：先找 user gem 或 PATH 裡的 istats。
    if istats_tool:  # 逐行註解：如果有 istats，就優先使用，因為這台機器已實測可回傳 Fan 0 speed。
        ok_i, out_i, _ = run_monitor_command([istats_tool, "--no-graphs"], timeout=5)  # 逐行註解：執行 istats 並關掉圖形輸出。
        attempts.append("istats")  # 逐行註解：記錄嘗試過 istats。
        fans = parse_fans_from_text(out_i) if out_i else []  # 逐行註解：解析 istats 風扇輸出。
        if fans:  # 逐行註解：如果 istats 有資料，就回傳；0 RPM 也是工具實際讀到的值。
            return {"fans": fans, "source": "istats", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：回傳風扇資料與來源。
    smc_tool = find_monitor_tool("smc")  # 逐行註解：尋找 smc 工具。
    if smc_tool:  # 逐行註解：如果有 smc 工具，就最後嘗試。
        ok_s, out_s, _ = run_monitor_command([smc_tool, "-f"], timeout=5)  # 逐行註解：執行 smc 查風扇。
        attempts.append("smc")  # 逐行註解：記錄嘗試過 smc。
        fans = parse_fans_from_text(out_s) if out_s else []  # 逐行註解：解析 smc 風扇輸出。
        if fans:  # 逐行註解：如果 smc 有資料，就回傳。
            return {"fans": fans, "source": "smc", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：回傳風扇資料與來源。
    return {"fans": [], "source": "N/A", "attempts": attempts, "powermetrics_raw": smc_output}  # 逐行註解：全部失敗才回傳 N/A。


def parse_gpu_usage_from_text(text: str) -> float | None:  # 逐行註解：定義從輸出解析 GPU 總使用率的函式。
    return parse_first_float(  # 逐行註解：用多種 powermetrics 可能格式解析 GPU 使用率。
        [
            r"GPU\s+active\s+residency[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%",  # 逐行註解：解析 GPU active residency。
            r"GPU\s+Busy[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%",  # 逐行註解：解析 GPU Busy。
            r"GPU[^\n]*usage[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%",  # 逐行註解：解析 GPU usage。
        ],
        text,  # 逐行註解：傳入要解析的輸出文字。
    )  # 逐行註解：結束 parse_first_float 呼叫。


def parse_gpu_core_usage_from_text(text: str) -> list[float]:  # 逐行註解：定義解析 GPU 每核心使用率的函式。
    cores: list[float] = []  # 逐行註解：建立 GPU 核心使用率清單。
    for match in re.finditer(r"GPU\s*(?:Core|HW)\s*(\d+)[^\n%]*?([0-9]+(?:\.[0-9]+)?)\s*%", text, re.IGNORECASE):  # 逐行註解：搜尋工具可能提供的 GPU Core 使用率。
        cores.append(float(match.group(2)))  # 逐行註解：加入這個 GPU 核心使用率。
    return cores  # 逐行註解：回傳 GPU 核心使用率清單。


def get_gpu_stats(mactop_sample: dict | None = None, macmon_sample: dict | None = None, gpu_power_output: str = "", gpu_all_output: str = "") -> dict:  # 逐行註解：定義取得 GPU 使用率的函式。
    """優先嘗試 powermetrics gpu_power；Apple Silicon fallback 一律標成 estimate。"""  # 逐行註解：避免把 mactop/macmon aggregate active 假裝成精準 Activity Monitor 數字。
    attempts = ["powermetrics gpu_power"]  # 逐行註解：保存嘗試來源。
    total = parse_gpu_usage_from_text(gpu_power_output) if gpu_power_output else None  # 逐行註解：解析 powermetrics gpu_power。
    cores = parse_gpu_core_usage_from_text(gpu_power_output) if gpu_power_output else []  # 逐行註解：解析 powermetrics GPU core 資料。
    if total is not None or cores:  # 逐行註解：如果 powermetrics 有資料，就用它但仍標 estimate。
        return {"total": total, "cores": cores, "core_count": len(cores), "source": "powermetrics gpu_power", "name": "Apple GPU", "freq_mhz": None, "estimate": True, "attempts": attempts, "powermetrics_raw": gpu_power_output}  # 逐行註解：回傳 GPU estimate。
    attempts.append("powermetrics all")  # 逐行註解：第二順位嘗試 powermetrics all。
    total = parse_gpu_usage_from_text(gpu_all_output) if gpu_all_output else None  # 逐行註解：解析 powermetrics all。
    cores = parse_gpu_core_usage_from_text(gpu_all_output) if gpu_all_output else []  # 逐行註解：解析 powermetrics all core 資料。
    if total is not None or cores:  # 逐行註解：如果 powermetrics all 有資料就使用。
        return {"total": total, "cores": cores, "core_count": len(cores), "source": "powermetrics all", "name": "Apple GPU", "freq_mhz": None, "estimate": True, "attempts": attempts, "powermetrics_raw": gpu_all_output}  # 逐行註解：回傳 GPU estimate。
    if mactop_sample:  # 逐行註解：powermetrics 失敗時 fallback 到 mactop，這是 aggregate active estimate。
        attempts.append("mactop")  # 逐行註解：記錄嘗試過 mactop。
        total = normalize_usage_percent(mactop_sample.get("gpu_usage"))  # 逐行註解：取得 GPU 總使用率。
        gpu_info = mactop_sample.get("system_info") or {}  # 逐行註解：取出 GPU 核心數等資訊。
        gpu_core_count = int(gpu_info.get("gpu_core_count") or 0)  # 逐行註解：讀取 GPU 核心數。
        gpu_metrics = mactop_sample.get("gpu_metrics") or {}  # 逐行註解：取出 GPU 頻率等指標。
        if total is not None:  # 逐行註解：如果 mactop 有 GPU 使用率，就回傳。
            return {  # 逐行註解：回傳 mactop GPU 資料。
                "total": total,  # 逐行註解：GPU 總使用率。
                "cores": [],  # 逐行註解：mactop/btop 的 Apple Silicon GPU 使用率是 aggregate active，不提供獨立每 GPU core 使用率。
                "core_count": gpu_core_count,  # 逐行註解：保存偵測到的 GPU core 數量。
                "source": "mactop",  # 逐行註解：資料來源。
                "name": (gpu_info.get("name") or mactop_sample.get("system_info", {}).get("name") or "Apple GPU"),  # 逐行註解：GPU/SoC 名稱。
                "freq_mhz": gpu_metrics.get("freq_mhz"),  # 逐行註解：GPU 頻率。
                "estimate": True,  # 逐行註解：mactop 的 GPU active 是估算/aggregate，不當成精準總量。
                "attempts": attempts,  # 逐行註解：記錄嘗試來源。
                "powermetrics_raw": gpu_power_output or gpu_all_output,  # 逐行註解：保留 powermetrics raw/debug。
            }  # 逐行註解：結束 mactop GPU 回傳。
    if macmon_sample:  # 逐行註解：mactop 不可用時改用 macmon。
        attempts.append("macmon")  # 逐行註解：記錄嘗試過 macmon。
        gpu_usage = macmon_sample.get("gpu_usage")  # 逐行註解：macmon 的 gpu_usage 通常是 [freq, active_fraction]。
        total = None  # 逐行註解：建立 GPU 總使用率預設值。
        freq_mhz = None  # 逐行註解：建立 GPU 頻率預設值。
        if isinstance(gpu_usage, list) and len(gpu_usage) >= 2:  # 逐行註解：解析 macmon list 格式。
            freq_mhz = gpu_usage[0]  # 逐行註解：第一個值是頻率。
            total = normalize_usage_percent(gpu_usage[1])  # 逐行註解：第二個值是使用率。
        soc = macmon_sample.get("soc") or {}  # 逐行註解：取出 SoC 資訊。
        gpu_core_count = int(soc.get("gpu_cores") or 0)  # 逐行註解：讀取 GPU 核心數。
        if total is not None:  # 逐行註解：如果 macmon 有 GPU 使用率，就回傳。
            return {"total": total, "cores": [], "core_count": gpu_core_count, "source": "macmon", "name": soc.get("chip_name") or "Apple GPU", "freq_mhz": freq_mhz, "estimate": True, "attempts": attempts, "powermetrics_raw": gpu_power_output or gpu_all_output}  # 逐行註解：回傳 macmon GPU 資料。
    ok_sp, out_sp, _ = run_monitor_command(["system_profiler", "SPDisplaysDataType"], timeout=8)  # 逐行註解：第三順位嘗試 system_profiler。
    attempts.append("system_profiler")  # 逐行註解：記錄嘗試過 system_profiler。
    if ok_sp and out_sp:  # 逐行註解：system_profiler 通常只能提供 GPU 型號，不能提供使用率。
        gpu_name_match = re.search(r"Chipset Model:\\s*(.+)", out_sp)  # 逐行註解：解析 GPU 型號，作為非使用率補充資訊。
        gpu_name = gpu_name_match.group(1).strip() if gpu_name_match else "N/A"  # 逐行註解：設定 GPU 型號。
    else:  # 逐行註解：system_profiler 失敗時，GPU 型號也只能 N/A。
        gpu_name = "N/A"  # 逐行註解：設定 GPU 型號為 N/A。
    ok_io, out_io, _ = run_monitor_command(["ioreg", "-l"], timeout=5)  # 逐行註解：最後順位嘗試 ioreg。
    attempts.append("ioreg")  # 逐行註解：記錄嘗試過 ioreg。
    total = parse_gpu_usage_from_text(out_io) if out_io else None  # 逐行註解：嘗試從 ioreg 解析 GPU 使用率。
    cores = parse_gpu_core_usage_from_text(out_io) if out_io else []  # 逐行註解：嘗試從 ioreg 解析 GPU 每核心使用率。
    if total is not None or cores:  # 逐行註解：如果 ioreg 有資料，就回傳。
        return {"total": total, "cores": cores, "core_count": len(cores), "source": "ioreg", "name": gpu_name, "estimate": True, "attempts": attempts, "powermetrics_raw": gpu_power_output or gpu_all_output}  # 逐行註解：回傳 GPU 資料。
    return {"total": None, "cores": [], "core_count": 0, "source": "N/A", "name": gpu_name, "estimate": True, "attempts": attempts, "powermetrics_raw": gpu_power_output or gpu_all_output}  # 逐行註解：全部取不到使用率才回傳 N/A。


def first_fan_rpm_text(fans: dict) -> str:  # 逐行註解：把風扇清單轉成主畫面的單行顯示。
    fan_items = fans.get("fans") or []  # 逐行註解：取出風扇清單。
    if not fan_items:  # 逐行註解：沒有風扇資料就顯示 N/A。
        return "N/A"  # 逐行註解：回傳無資料標記。
    return f"{fan_items[0].get('rpm', 'N/A')} RPM"  # 逐行註解：主畫面只顯示第一顆風扇 RPM，單風扇不顯示 Fan 0。


def max_available_temperature(temp: dict) -> float | None:  # 逐行註解：取得 CPU/GPU 中可用的最高溫。
    values = [value for value in (temp.get("cpu_max"), temp.get("gpu_max")) if value is not None]  # 逐行註解：只保留真實讀到的溫度。
    return max(values) if values else None  # 逐行註解：有資料就回最高值，否則回 None。


def build_computer_embed(stats: dict) -> discord.Embed:  # 逐行註解：定義建立 /state Discord Embed 的函式。
    """把 Mac 狀態整理成完整 terminal 監控面板。"""  # 逐行註解：顯示完整硬體監控資訊。

    cpu = stats["cpu"]  # 逐行註解：取出 CPU 統計資料。
    ram = stats["ram"]  # 逐行註解：取出 RAM 統計資料。
    gpu = stats["gpu"]  # 逐行註解：取出 GPU 統計資料。
    temp = stats["temperature"]  # 逐行註解：取出溫度統計資料。
    fans = stats["fans"]  # 逐行註解：取出風扇統計資料。
    battery = stats.get("battery", {})  # 逐行註解：取出電池資料。
    chip_name = stats.get("system_name") or gpu.get("name") or "Mac"  # 逐行註解：顯示 Apple Silicon 名稱。

    gpu_value = gpu.get("total")  # 逐行註解：GPU 使用率。
    gpu_label = format_percent(gpu_value) if gpu_value is not None else "N/A"  # 逐行註解：GPU 百分比文字。

    lines = [  # 逐行註解：建立 terminal monitor 內容。

        "🖥️ Mac System Monitor",
        "━━━━━━━━━━━━━━━━━━━━",
        "",

        "CPU",
        f"Total：{usage_bar(cpu.get('total'), width=10)}  {format_percent(cpu.get('total'))}",

        *[
            f"Core {i+1:<2} {usage_bar(v, width=10)}  {format_percent(v)}"
            for i, v in enumerate(cpu.get("cores", []))
        ],

        "",
        "RAM",
        f"{ram.get('used', 0) / (1024**3):.1f} GB / {ram.get('total', 0) / (1024**3):.1f} GB",
        f"{format_percent(ram.get('percent'))}",

        "",
        "GPU",
        f"Total：{usage_bar(gpu_value, width=10)}  {gpu_label}",
        f"GPU Cores：{gpu.get('core_count', 'N/A')} cores detected",
        f"Per-Core Usage：aggregate only",
        f"GPU Name：{gpu.get('name', chip_name)}",
        f"GPU Freq：{gpu.get('freq_mhz', 'N/A')} MHz",

        "",
        "Temperature",
        f"CPU Max：{format_temperature(temp.get('cpu_max'))}",
        f"GPU Max：{format_temperature(temp.get('gpu_max'))}",

        "",
        "Fans",
        f"Fan：{first_fan_rpm_text(fans)}",

        "",
        "Battery",
        f"Power：{battery.get('power', 'N/A')}",
        f"Level：{battery.get('level', 'N/A')}%",
        f"Plugged：{battery.get('is_plugged', 'N/A')}",
        f"State：{battery.get('state', 'N/A')}",

        "",
        "Sources",
        f"CPU：{cpu.get('source', 'psutil')}",
        f"RAM：{ram.get('source', 'psutil')}",
        f"Battery：{battery.get('source', 'pmset')}",
        f"Temperature：{temp.get('source', 'mactop')}",
        f"Fans：{fans.get('source', 'mactop') if isinstance(fans, dict) else 'mactop'}",
        f"GPU：{gpu.get('source', 'mactop')}",

        "━━━━━━━━━━━━━━━━━━━━",
    ]  # 逐行註解：結束 monitor lines。

    if cpu.get("error") or ram.get("error"):  # 逐行註解：如果 psutil 出錯則顯示錯誤。
        lines.extend([
            "",
            cpu.get("error") or ram.get("error")
        ])  # 逐行註解：加入錯誤訊息。

    body = make_code_block("\n".join(lines), "txt")  # 逐行註解：轉成 Discord code block。

    embed = discord.Embed(
        title="Mac System Monitor",
        description=body,
        color=0x2F81F7
    )  # 逐行註解：建立 Discord Embed。

    embed.set_footer(
        text="Raw sensor data is kept internal."
    )  # 逐行註解：底部說明。

    return embed  # 逐行註解：回傳 Embed。


def collect_computer_stats() -> dict:  # 逐行註解：定義整合所有 Mac 狀態資料的函式。
    """集中呼叫各個 helper，方便 /computer 用 asyncio.to_thread 執行。"""  # 逐行註解：外部指令與 psutil 採樣放到 thread，避免卡住 Discord event loop。
    ok_top, top_output, top_error = run_monitor_command(["top", "-l", "2", "-n", "0"], timeout=8)  # 逐行註解：用 top 第二筆 sample 當 CPU total 來源。
    ok_gpu, gpu_power_output, gpu_power_error = run_monitor_command(["sudo", "-n", "powermetrics", "--samplers", "gpu_power", "-i", "1000", "-n", "1"], timeout=8)  # 逐行註解：非互動嘗試 GPU powermetrics。
    gpu_all_output = ""  # 逐行註解：建立 powermetrics all raw 預設值。
    gpu_all_error = ""  # 逐行註解：建立 powermetrics all error 預設值。
    if not ok_gpu or parse_gpu_usage_from_text(gpu_power_output) is None:  # 逐行註解：gpu_power 沒讀到使用率時才跑 all fallback。
        _, gpu_all_output, gpu_all_error = run_monitor_command(["sudo", "-n", "powermetrics", "--samplers", "all", "-i", "1000", "-n", "1"], timeout=8)  # 逐行註解：非互動嘗試 powermetrics all。
    ok_smc, smc_output, smc_error = run_monitor_command(["sudo", "-n", "powermetrics", "--samplers", "smc", "-i", "1000", "-n", "1"], timeout=8)  # 逐行註解：非互動嘗試 SMC 溫度/風扇。
    mactop_sample = get_mactop_stats()  # 逐行註解：先讀 mactop，這是目前 Apple Silicon 最完整且不需要 sudo 的來源。
    macmon_sample = get_macmon_stats() if mactop_sample is None else None  # 逐行註解：只有 mactop 失敗時才讀 macmon，減少額外採樣時間。
    system_info = (mactop_sample or {}).get("system_info") or (macmon_sample or {}).get("soc") or {}  # 逐行註解：取出 Apple M 系列名稱。
    return {  # 逐行註解：回傳所有監控資料。
        "cpu": get_cpu_stats(mactop_sample, macmon_sample, top_output),  # 逐行註解：取得 CPU 使用率。
        "ram": get_ram_stats(mactop_sample, macmon_sample, top_output),  # 逐行註解：取得 RAM 使用量。
        "gpu": get_gpu_stats(mactop_sample, macmon_sample, gpu_power_output, gpu_all_output),  # 逐行註解：取得 GPU 使用率。
        "temperature": get_temperature_stats(mactop_sample, macmon_sample, smc_output),  # 逐行註解：取得 CPU/GPU 溫度。
        "fans": get_fan_stats(mactop_sample, smc_output),  # 逐行註解：取得風扇 RPM。
        "battery": get_battery_stats(),  # 逐行註解：取得電池狀態。
        "system_name": system_info.get("name") or system_info.get("chip_name") or "",  # 逐行註解：保存晶片名稱。
        "raw": {  # 逐行註解：保存內部資料來源比對用的原始資料。
            "top_ok": ok_top,  # 逐行註解：top 是否成功。
            "top_error": top_error,  # 逐行註解：top 錯誤。
            "top_output": top_output,  # 逐行註解：top raw。
            "powermetrics_gpu_ok": ok_gpu,  # 逐行註解：gpu_power 是否成功。
            "powermetrics_gpu_error": gpu_power_error,  # 逐行註解：gpu_power 錯誤。
            "powermetrics_gpu_power": gpu_power_output,  # 逐行註解：gpu_power raw。
            "powermetrics_gpu_all_error": gpu_all_error,  # 逐行註解：gpu all 錯誤。
            "powermetrics_gpu_all": gpu_all_output,  # 逐行註解：gpu all raw。
            "powermetrics_smc_ok": ok_smc,  # 逐行註解：smc 是否成功。
            "powermetrics_smc_error": smc_error,  # 逐行註解：smc 錯誤。
            "powermetrics_smc": smc_output,  # 逐行註解：smc raw。
        },  # 逐行註解：結束 raw dict。
    }  # 逐行註解：結束資料 dict。


async def send_state_monitor_after_password(interaction: discord.Interaction, *, show_apple_loading: bool):  # 逐行註解：定義 /state 密碼驗證通過後真正查詢 Mac 狀態的函式。
    """密碼驗證成功後，依使用者選擇顯示 Apple 載入畫面，並每 3 秒刷新 Mac 狀態。"""  # 逐行註解：把查詢流程從 slash command 拆出來，讓 Modal submit 也能共用。
    if show_apple_loading:  # 逐行註解：如果使用者選擇顯示 Apple 標誌，就先送紅色 ANSI code block。
        loading_messages = await send_red_ansi_followup(interaction, STATE_APPLE_LOADING_ART, ephemeral=True)  # 逐行註解：原樣送出 Apple ASCII，不用 Embed、不改空白。
        loading_message = loading_messages[0]  # 逐行註解：第一則訊息之後會被 edit 成監控面板。
    else:  # 逐行註解：如果使用者選擇不顯示 Apple 標誌，就直接顯示查詢中訊息。
        loading_message = await interaction.followup.send("正在讀取 Mac 狀態…", ephemeral=True, wait=True)  # 逐行註解：建立同一則之後要被監控面板 edit 的訊息。
    loading_started = time.monotonic()  # 逐行註解：記錄 Apple 標誌開始顯示的時間，用來確保至少顯示 3 秒。
    first_update = show_apple_loading  # 逐行註解：只有有顯示 Apple 標誌時，第一次更新前才需要補足 3 秒。
    while True:  # 逐行註解：持續刷新 /state 監控面板，直到 edit 失敗或 bot 關閉。
        try:  # 逐行註解：開始查詢 Mac 狀態。
            stats = await asyncio.to_thread(collect_computer_stats)  # 逐行註解：把可能阻塞的 subprocess 與 psutil 採樣放到 thread。
            if first_update:  # 逐行註解：第一次更新前要確保 Apple 標誌至少顯示 3 秒。
                remaining_loading_time = STATE_LOADING_MIN_SECONDS - (time.monotonic() - loading_started)  # 逐行註解：計算 Apple 標誌還需要補顯示多久才滿 3 秒。
                if remaining_loading_time > 0:  # 逐行註解：如果資料太快抓完，就補足剩餘秒數。
                    await asyncio.sleep(remaining_loading_time)  # 逐行註解：至少讓 Apple code block 顯示 3 秒。
            embed = build_computer_embed(stats)  # 逐行註解：把查到的資料整理成 Embed。
            edited = await safe_edit_message_embed(loading_message, content=None, embed=embed)  # 逐行註解：把同一則訊息更新成最新監控面板 Embed。
            if not edited:  # 逐行註解：如果 edit 失敗，就不要無限重試或洗新訊息。
                print("/state 監控面板 edit 失敗，停止自動刷新。")  # 逐行註解：把停止原因印到後台，方便排查。
                return  # 逐行註解：停止 /state 自動刷新。
            first_update = False  # 逐行註解：第一次更新已完成，之後不再補 Apple 標誌顯示時間。
            await asyncio.sleep(STATE_REFRESH_INTERVAL_SECONDS)  # 逐行註解：每 3 秒重新抓一次資料並更新同一則訊息。
        except asyncio.CancelledError:  # 逐行註解：如果 bot 關閉或 task 被取消，讓取消訊號正常往外傳。
            raise  # 逐行註解：不要吞掉取消錯誤。
        except Exception as e:  # 逐行註解：捕捉整體查詢失敗，避免 bot 崩潰。
            await safe_edit_message(loading_message, f"（查詢 Mac 狀態失敗：{type(e).__name__}: {str(e)[:300]}）")  # 逐行註解：把監控訊息改成錯誤訊息。
            return  # 逐行註解：查詢出錯後停止自動刷新。


class StatePasswordModal(discord.ui.Modal, title="查看 Mac 狀態"):  # 逐行註解：定義 /state 專用密碼視窗，避免密碼出現在 slash command 參數或聊天記錄。
    password = discord.ui.TextInput(  # 逐行註解：建立密碼輸入欄位，流程和 /quit 的 Modal 一樣。
        label="請輸入查看狀態密碼",  # 逐行註解：設定 Modal 欄位標題。
        placeholder="請輸入 Mac 密碼",  # 逐行註解：提示使用者使用既有敏感指令密碼。
        required=True,  # 逐行註解：密碼欄位必填。
        max_length=200,  # 逐行註解：限制密碼長度，避免不必要的超長輸入。
    )  # 逐行註解：結束 TextInput 設定。

    def __init__(self, *, show_apple_loading: bool):  # 逐行註解：初始化 /state 密碼視窗，保存使用者是否要顯示 Apple 標誌。
        super().__init__()  # 逐行註解：先執行 discord.ui.Modal 原本的初始化流程。
        self.show_apple_loading = show_apple_loading  # 逐行註解：記錄按鈕選擇，密碼通過後交給狀態監控流程。

    async def on_submit(self, interaction: discord.Interaction):  # 逐行註解：定義使用者送出 Modal 後要執行的流程。
        if not require_super_user(interaction.user):  # 逐行註解：再次檢查 SUPER_USERS，避免非超級使用者使用 /state。
            await interaction.response.send_message(sensitive_permission_message(), ephemeral=True)  # 逐行註解：沒有敏感指令權限就只回覆執行者。
            return  # 逐行註解：停止 /state 流程。
        if not DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：如果 .env 沒設定敏感指令密碼，就拒絕查詢。
            await interaction.response.send_message("尚未設定 DISCORD_BOT_QUIT_PASSWORD，無法使用 /state。", ephemeral=True)  # 逐行註解：提醒使用者去 .env 設密碼。
            return  # 逐行註解：停止 /state 流程。
        if self.password.value.strip() != DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：比對 Modal 裡輸入的密碼和 .env 密碼。
            await interaction.response.send_message("密碼錯誤，無法查看這台 Mac 的狀態。", ephemeral=True)  # 逐行註解：密碼錯誤時只回覆執行者。
            return  # 逐行註解：停止 /state 流程。
        author_name = (getattr(interaction.user, "global_name", None) or getattr(interaction.user, "display_name", None) or interaction.user.name or "").strip()  # 逐行註解：取得使用者顯示名稱，給 /state 後台紀錄使用。
        author_account = str(interaction.user).strip()  # 逐行註解：取得 Discord 帳號字串，給 /state 後台紀錄使用。
        print(  # 逐行註解：把哪個使用者使用 /state 工具印到後台，但不印出密碼。
            "\n".join(  # 逐行註解：把多行後台紀錄組成一整段文字。
                [  # 逐行註解：開始建立 /state 後台紀錄內容。
                    "——————————————————",  # 逐行註解：後台紀錄分隔線。
                    f"使用者名稱：{author_name}",  # 逐行註解：顯示使用者名稱。
                    f"使用者帳號：{author_account}",  # 逐行註解：顯示使用者帳號。
                    f"使用者ID：{interaction.user.id}",  # 逐行註解：顯示使用者 Discord ID。
                    "使用者詢問：/state",  # 逐行註解：顯示使用者使用的指令。
                    "工具：state",  # 逐行註解：顯示這次使用的是 state 工具。
                    f"狀態：密碼驗證通過，開始每 3 秒刷新 Mac 狀態（Apple 標誌：{'顯示' if self.show_apple_loading else '不顯示'}）",  # 逐行註解：顯示 /state 已開始監控刷新和 Apple 標誌選擇。
                    "——————————————————",  # 逐行註解：後台紀錄分隔線。
                    "",  # 逐行註解：最後留空行，讓下一段後台紀錄比較好讀。
                ]  # 逐行註解：結束 /state 後台紀錄內容。
            )  # 逐行註解：結束 join。
        )  # 逐行註解：結束 print。
        await interaction.response.defer(ephemeral=True)  # 逐行註解：密碼正確後先 defer，避免 Mac 狀態查詢超過 Discord 時限。
        asyncio.create_task(send_state_monitor_after_password(interaction, show_apple_loading=self.show_apple_loading))  # 逐行註解：建立背景監控 task，讓 /state 每 3 秒持續刷新同一則訊息。


async def update_terminal_display(user_id: int):  # 逐行註解：定義非同步函式 update_terminal_display，每1.5秒更新一次終端顯示。
    """每1.5秒更新一次終端顯示訊息。"""  # 逐行註解：說明這個背景任務的用途。
    while user_id in terminal_sessions:  # 逐行註解：只要使用者還在終端模式，就持續重複執行下面的程式。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            await asyncio.sleep(1.5)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            session = terminal_sessions.get(user_id)  # 逐行註解：取得這個使用者的終端會話資訊。
            if not session:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                break  # 逐行註解：停止迴圈。

            # 組合輸出內容
            output_lines = session.get("output", [])  # 逐行註解：從會話中取出所有輸出行。
            output_text = "```\n進入終端模式\n再輸入 /run 可退出\n\n" + "\n".join(output_lines[-20:]) + "\n```"  # 逐行註解：組合成要顯示的文字，最多顯示最後20行。

            # Discord 消息有2000字符限制
            if len(output_text) > 1980:  # 逐行註解：判斷文字是否超過 Discord 限制。
                output_text = "```\n...\n" + output_text[-1950:] + "\n```"  # 逐行註解：截取最後部分，保持在字符限制內。

            try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                msg = session.get("message")  # 逐行註解：取得終端訊息物件。
                if msg:  # 逐行註解：判斷訊息是否存在。
                    await msg.edit(content=output_text)  # 逐行註解：編輯訊息顯示最新輸出。
            except:  # 逐行註解：捕捉編輯訊息時發生的任何錯誤。
                break  # 逐行註解：如果編輯失敗，就停止自動更新。
        except asyncio.CancelledError:  # 逐行註解：捕捉非同步工作被取消的信號。
            break  # 逐行註解：停止迴圈。
        except:  # 逐行註解：捕捉其他任何錯誤，避免 bot 崩潰。
            break  # 逐行註解：停止迴圈。


class RunPasswordModal(discord.ui.Modal, title="進入終端模式"):  # 逐行註解：定義類別 RunPasswordModal，用來讓使用者輸入密碼進入終端。
    password = discord.ui.TextInput(  # 逐行註解：建立密碼輸入欄位。
        label="請輸入進入終端密碼",  # 逐行註解：設定 Modal 欄位標題。
        placeholder="請輸入 Mac 密碼",  # 逐行註解：提示使用者輸入密碼。
        required=True,  # 逐行註解：密碼欄位必填。
        max_length=200,  # 逐行註解：限制密碼長度。
    )  # 逐行註解：結束 TextInput 設定。

    async def on_submit(self, interaction: discord.Interaction):  # 逐行註解：定義使用者送出 Modal 後要執行的流程。
        if not require_super_user(interaction.user):  # 逐行註解：再次檢查 SUPER_USERS，避免非超級使用者使用 /run。
            await interaction.response.send_message(sensitive_permission_message(), ephemeral=True)  # 逐行註解：沒有敏感指令權限就只回覆執行者。
            return  # 逐行註解：停止流程。
        if not DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：如果 .env 沒設定密碼，就拒絕進入。
            await interaction.response.send_message("尚未設定 DISCORD_BOT_QUIT_PASSWORD，無法使用 /run。", ephemeral=True)  # 逐行註解：提醒使用者去 .env 設密碼。
            return  # 逐行註解：停止流程。
        if self.password.value.strip() != DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：比對輸入的密碼和 .env 密碼。
            await interaction.response.send_message("密碼錯誤，無法進入終端模式。", ephemeral=True)  # 逐行註解：密碼錯誤時只回覆執行者。
            return  # 逐行註解：停止流程。

        # 密碼正確，初始化終端會話
        await interaction.response.defer(ephemeral=True)  # 逐行註解：先 defer，避免超過 Discord 時限。

        terminal_msg = await interaction.followup.send(  # 逐行註解：發送初始終端訊息。
            "```\n進入終端模式\n使用者：{}\n再輸入 /run 可退出\n\n等待輸入...\n```".format(interaction.user.name),  # 逐行註解：顯示終端的歡迎訊息。
            ephemeral=True,  # 逐行註解：只有執行者可以看到。
            wait=True  # 逐行註解：等待訊息發送完成才回傳訊息物件。
        )  # 逐行註解：結束發送訊息。

        # 建立會話
        terminal_sessions[interaction.user.id] = {  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            "message": terminal_msg,  # 逐行註解：儲存終端訊息物件。
            "channel": interaction.channel,  # 逐行註解：儲存頻道物件。
            "output": [],  # 逐行註解：初始化輸出清單。
            "started_at": time.monotonic(),  # 逐行註解：記錄會話開始時間。
        }  # 逐行註解：結束會話資訊。

        # 後台紀錄使用者
        author_name = (getattr(interaction.user, "global_name", None) or getattr(interaction.user, "display_name", None) or interaction.user.name or "").strip()  # 逐行註解：取得使用者顯示名稱。
        author_account = str(interaction.user).strip()  # 逐行註解：取得 Discord 帳號字串。
        print(  # 逐行註解：把哪個使用者使用 /run 工具印到後台，但不印出密碼。
            "\n".join(  # 逐行註解：把多行後台紀錄組成一整段文字。
                [  # 逐行註解：開始建立 /run 後台紀錄內容。
                    "——————————————————",  # 逐行註解：後台紀錄分隔線。
                    f"使用者名稱：{author_name}",  # 逐行註解：顯示使用者名稱。
                    f"使用者帳號：{author_account}",  # 逐行註解：顯示使用者帳號。
                    f"使用者ID：{interaction.user.id}",  # 逐行註解：顯示使用者 Discord ID。
                    "使用者詢問：/run",  # 逐行註解：顯示使用者使用的指令。
                    "工具：run",  # 逐行註解：顯示這次使用的是 run 工具。
                    "狀態：密碼驗證通過，進入終端模式",  # 逐行註解：顯示已進入終端模式。
                    "——————————————————",  # 逐行註解：後台紀錄分隔線。
                    "",  # 逐行註解：最後留空行，讓下一段後台紀錄比較好讀。
                ]  # 逐行註解：結束 /run 後台紀錄內容。
            )  # 逐行註解：結束 join。
        )  # 逐行註解：結束 print。

        # 啟動後台更新任務
        asyncio.create_task(update_terminal_display(interaction.user.id))  # 逐行註解：建立背景任務，每1.5秒更新一次終端顯示。


class AgentPasswordModal(discord.ui.Modal, title="進入 Agent Mode"):  # 逐行註解：定義 /agent 專用密碼視窗，登入方式和 /run、/state 一樣。
    password = discord.ui.TextInput(  # 逐行註解：建立密碼輸入欄位。
        label="請輸入 Agent 密碼",  # 逐行註解：設定 Modal 欄位標題。
        placeholder="請輸入 Mac 密碼",  # 逐行註解：提示使用者輸入同一套敏感指令密碼。
        required=True,  # 逐行註解：密碼欄位必填。
        max_length=200,  # 逐行註解：限制密碼長度。
    )  # 逐行註解：結束 TextInput 設定。

    async def on_submit(self, interaction: discord.Interaction):  # 逐行註解：定義使用者送出 Agent 密碼後要執行的流程。
        if not require_super_user(interaction.user):  # 逐行註解：再次檢查 SUPER_USERS，避免非超級使用者使用 /agent。
            await interaction.response.send_message(sensitive_permission_message(), ephemeral=True)  # 逐行註解：沒有敏感指令權限就只回覆執行者。
            return  # 逐行註解：停止流程。
        if not DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：如果 .env 沒設定密碼，就拒絕進入。
            await interaction.response.send_message("尚未設定 DISCORD_BOT_QUIT_PASSWORD，無法使用 /agent。", ephemeral=True)  # 逐行註解：提醒使用者去 .env 設密碼。
            return  # 逐行註解：停止流程。
        if self.password.value.strip() != DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：比對輸入的密碼和 .env 密碼。
            await interaction.response.send_message("密碼錯誤，無法進入 agent mode。", ephemeral=True)  # 逐行註解：密碼錯誤時只回覆執行者。
            return  # 逐行註解：停止流程。
        agent_sessions[interaction.user.id] = {  # 逐行註解：建立 Agent session，後續訊息會被當成 Agent 任務。
            "channel": interaction.channel,  # 逐行註解：保存進入 Agent mode 的頻道。
            "task_history": [],  # 逐行註解：保存任務和 terminal output 歷史。
            "command_history": [],  # 逐行註解：保存 command 歷史。
            "current_task": "",  # 逐行註解：保存目前正在處理的任務。
            "agent_model": AGENT_MODEL,  # 逐行註解：保存這個 session 固定使用的 Agent 專用模型，使用者不能用聊天模型選單改掉。
            "retry_count": 0,  # 逐行註解：保存目前 retry 次數。
            "started_at": time.monotonic(),  # 逐行註解：記錄 session 開始時間。
        }  # 逐行註解：結束 Agent session。
        author_name = (getattr(interaction.user, "global_name", None) or getattr(interaction.user, "display_name", None) or interaction.user.name or "").strip()  # 逐行註解：取得使用者顯示名稱。
        author_account = str(interaction.user).strip()  # 逐行註解：取得 Discord 帳號字串。
        print(  # 逐行註解：把哪個使用者使用 /agent 工具印到後台，但不印密碼。
            "\n".join(  # 逐行註解：組合多行後台紀錄。
                [  # 逐行註解：開始建立 /agent 後台紀錄。
                    "——————————————————",  # 逐行註解：後台紀錄分隔線。
                    f"使用者名稱：{author_name}",  # 逐行註解：顯示使用者名稱。
                    f"使用者帳號：{author_account}",  # 逐行註解：顯示使用者帳號。
                    f"使用者ID：{interaction.user.id}",  # 逐行註解：顯示使用者 Discord ID。
                    "使用者詢問：/agent",  # 逐行註解：顯示使用者使用的指令。
                    "工具：agent",  # 逐行註解：顯示這次使用的是 agent 工具。
                    f"Agent固定模型：{AGENT_MODEL}",  # 逐行註解：後台明確記錄 Agent 一律使用專用模型，不受使用者聊天模型設定影響。
                    "狀態：密碼驗證通過，進入 agent mode",  # 逐行註解：顯示已進入 Agent mode。
                    "——————————————————",  # 逐行註解：後台紀錄分隔線。
                    "",  # 逐行註解：最後留空行。
                ]  # 逐行註解：結束後台紀錄清單。
            )  # 逐行註解：結束 join。
        )  # 逐行註解：結束 print。
        await interaction.response.send_message("已進入 agent mode\n接下來的訊息會被當作 agent 任務。再次輸入 /agent 可退出。", ephemeral=True)  # 逐行註解：提示使用者已進入 Agent mode。


class StateAppleChoiceView(discord.ui.View):  # 逐行註解：定義 /state 用的按鈕選單，讓使用者先選要不要顯示 Apple 標誌。
    def __init__(self, target_user_id: int):  # 逐行註解：初始化按鈕選單，記錄這次 /state 是哪個使用者叫出的。
        super().__init__(timeout=60)  # 逐行註解：設定 60 秒沒按就讓按鈕失效。
        self.target_user_id = target_user_id  # 逐行註解：保存使用者 ID，避免其他人按到同一組按鈕。

    async def _open_password_modal(self, interaction: discord.Interaction, *, show_apple_loading: bool):  # 逐行註解：共用按鈕 callback，依選擇開啟密碼視窗。
        if interaction.user.id != self.target_user_id:  # 逐行註解：如果不是原本呼叫 /state 的人，就拒絕操作。
            await interaction.response.send_message("這不是你的 /state 選項。", ephemeral=True)  # 逐行註解：只提醒按錯的人。
            return  # 逐行註解：停止流程。
        await interaction.response.send_modal(StatePasswordModal(show_apple_loading=show_apple_loading))  # 逐行註解：依使用者選擇開啟 /state 密碼視窗；Modal 必須是按鈕互動的第一個回應。
        for child in self.children:  # 逐行註解：選完後把按鈕停用，避免重複點擊。
            child.disabled = True  # 逐行註解：停用這顆按鈕。
        try:  # 逐行註解：嘗試把原本選項訊息更新成已選擇狀態。
            await interaction.message.edit(content=f"Apple 標誌：{'顯示' if show_apple_loading else '不顯示'}，請在跳出的視窗輸入密碼。", view=self)  # 逐行註解：編輯原訊息並停用按鈕。
        except Exception as e:  # 逐行註解：如果 ephemeral message edit 失敗，不影響後續密碼視窗。
            print(f"/state Apple 選項訊息更新失敗：{type(e).__name__}: {e}")  # 逐行註解：把錯誤印到後台。

    @discord.ui.button(label="是", style=discord.ButtonStyle.primary)  # 逐行註解：建立「是」按鈕，代表要顯示 Apple 標誌。
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):  # 逐行註解：處理使用者按下「是」。
        await self._open_password_modal(interaction, show_apple_loading=True)  # 逐行註解：開啟密碼視窗並記錄要顯示 Apple 標誌。

    @discord.ui.button(label="否", style=discord.ButtonStyle.secondary)  # 逐行註解：建立「否」按鈕，代表不要顯示 Apple 標誌。
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):  # 逐行註解：處理使用者按下「否」。
        await self._open_password_modal(interaction, show_apple_loading=False)  # 逐行註解：開啟密碼視窗並記錄不要顯示 Apple 標誌。


@tree.command(name="state", description="查看這台 Mac 的狀態")  # 逐行註解：新增 /state slash command，不再把密碼放在指令參數裡。
async def state(interaction: discord.Interaction):  # 逐行註解：定義 /state 指令，輸入後會跳出密碼視窗。
    """輸入 /state，先選是否顯示 Apple 標誌，再輸入密碼，密碼正確才會顯示 Mac 狀態。"""  # 逐行註解：說明這個敏感指令的用途。
    if not require_super_user(interaction.user):  # 逐行註解：先用 SUPER_USERS 檢查使用者，非超級使用者不能打開 /state 密碼視窗。
        await interaction.response.send_message(sensitive_permission_message(), ephemeral=True)  # 逐行註解：沒有敏感指令權限就回覆沒有權限。
        return  # 逐行註解：停止指令。
    await interaction.response.send_message("是否顯示 Apple 標誌？", view=StateAppleChoiceView(interaction.user.id), ephemeral=True)  # 逐行註解：先讓使用者選是或否，選完才跳密碼視窗。


@tree.command(name="web_search", description="Search the web and answer with Ollama")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
@discord.app_commands.choices(  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
    model=[  # 逐行註解：開始建立一個跨多行的列表資料。
        discord.app_commands.Choice(name="qwen2.5-coder:1.5b_chat (default text)", value="qwen2.5-coder:1.5b_chat"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="qwen2.5:7b (text)", value="qwen2.5:7b"),  # 逐行註解：加入 qwen2.5:7b 文字模型選項。
        discord.app_commands.Choice(name="gemma4_thinking (text)", value="gemma4_thinking"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="gemma4_Instant (text)", value="gemma4_Instant"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="gemma4_happy (text)", value="gemma4_happy"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="gemma4_angry (text)", value="gemma4_angry"),  # 逐行註解：這行是跨行資料或參數的一個項目。
        discord.app_commands.Choice(name="gemma4_sad (text)", value="gemma4_sad"),  # 逐行註解：這行是跨行資料或參數的一個項目。
    ]  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
)  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
async def web_search(interaction: discord.Interaction, question: str, model: discord.app_commands.Choice[str]):  # 逐行註解：定義非同步函式 web_search，可以搭配 await 處理 Discord 或網路等待。
    """輸入 /web_search <問題>，先搜尋網頁，再讓 Ollama 根據搜尋結果回答。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    private_reply = interaction.guild is not None  # 逐行註解：設定 private_reply 這個變數，供後面的流程使用。

    if not is_allowed_interaction_user(interaction):  # 逐行註解：/web_search 依目前情境檢查權限，統一走 ALLOWED_USERS 與 SUPER_USERS。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=private_reply)  # 逐行註解：沒有權限時明確回覆給使用者。
        return  # 逐行註解：沒有權限時結束，不進行搜尋和 Ollama 回答。

    q = (question or "").strip()  # 逐行註解：設定 q 這個變數，供後面的流程使用。
    if not q:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await interaction.response.send_message("請輸入要搜尋的問題", ephemeral=private_reply)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    selected_model = (model.value or "").strip()  # 逐行註解：設定 selected_model 這個變數，供後面的流程使用。
    if selected_model not in DM_MODELS or selected_model == "x/flux2-klein:latest":  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await interaction.response.send_message("web_search 只能選文字模型，不能選生成圖片模型。", ephemeral=private_reply)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    await interaction.response.defer(ephemeral=private_reply, thinking=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
    progress_message = None  # 逐行註解：設定 progress_message 這個變數，供後面的流程使用。
    active_ai_run = None  # 逐行註解：保存這次 /web_search AI 任務的 /stop 登記，結束時要清掉。

    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
        started = time.monotonic()  # 逐行註解：設定 started 這個變數，供後面的流程使用。
        # 建立一則可以反覆 edit 的進度訊息，後面每個階段都更新同一則。
        progress_message = await interaction.followup.send(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
            "/web_search 進度\n1. 正在搜尋網頁…",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            ephemeral=private_reply,  # 逐行註解：設定 ephemeral 這個變數，供後面的流程使用。
            wait=True,  # 逐行註解：設定 wait 這個變數，供後面的流程使用。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        active_ai_run = register_active_ai_run(interaction.user.id, "/web_search", asyncio.current_task(), status_message=progress_message)  # 逐行註解：登記這次 /web_search 任務，讓 /stop 可以取消搜尋與 AI 回答流程。

        # 第一階段：送 DuckDuckGo HTML 搜尋，先拿到標題、摘要和網址。
        results = await search_web_results(q, limit=8)  # 逐行註解：設定 results 這個變數，供後面的流程使用。
        if not results:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            await update_web_search_progress(progress_message, "找不到可用的網頁搜尋結果。")  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

        await update_web_search_progress(  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            progress_message,  # 逐行註解：這行是跨行資料或參數的一個項目。
            f"/web_search 進度\n1. 搜尋完成：找到 {len(results)} 筆結果\n2. 正在篩選網頁…",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        search_context = format_search_results_for_log(results)  # 逐行註解：設定 search_context 這個變數，供後面的流程使用。
        search_urls = format_search_urls_for_log(results)  # 逐行註解：設定 search_urls 這個變數，供後面的流程使用。
        # 第二階段：先看標題/摘要/網址，挑出最值得實際打開的連結。
        fetch_candidates = select_results_for_fetch(q, results, limit=5)  # 逐行註解：設定 fetch_candidates 這個變數，供後面的流程使用。
        fetch_plan_context = format_fetch_plan_for_log(fetch_candidates)  # 逐行註解：設定 fetch_plan_context 這個變數，供後面的流程使用。
        await update_web_search_progress(  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            progress_message,  # 逐行註解：這行是跨行資料或參數的一個項目。
            "/web_search 進度\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            f"1. 搜尋完成：找到 {len(results)} 筆結果\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            f"2. 篩選完成：挑出 {len(fetch_candidates)} 個候選連結\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            "3. 正在打開連結讀取網頁內容…",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        # 第三階段：真的打開網頁讀文字；如果前幾個失敗，會繼續試到至少一個成功。
        page_reads = await fetch_web_pages(fetch_candidates, question=q, limit=5, min_attempts=3, min_successful=1)  # 逐行註解：設定 page_reads 這個變數，供後面的流程使用。
        page_read_context = format_page_reads_for_log(page_reads)  # 逐行註解：設定 page_read_context 這個變數，供後面的流程使用。
        page_read_success = has_successful_page_read(page_reads)  # 逐行註解：設定 page_read_success 這個變數，供後面的流程使用。
        read_success_count = sum(1 for page in page_reads if (page.get("text") or "").strip())  # 逐行註解：設定 read_success_count 這個變數，供後面的流程使用。
        await update_web_search_progress(  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            progress_message,  # 逐行註解：這行是跨行資料或參數的一個項目。
            "/web_search 進度\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            f"1. 搜尋完成：找到 {len(results)} 筆結果\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            f"2. 篩選完成：挑出 {len(fetch_candidates)} 個候選連結\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            f"3. 網頁讀取完成：成功讀到 {read_success_count} 個網頁\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            "4. 正在整理資料並產生回答…",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        memory_context = format_conversation_memory(interaction.user.id, selected_model)  # 逐行註解：設定 memory_context 這個變數，供後面的流程使用。
        
        # 先收集是否有自動產生的圖表，用來調整 prompt。
        all_auto_charts = []  # 逐行註解：建立暫存清單。
        for page in page_reads:  # 逐行註解：遍歷所有已讀取的網頁結果。
            if "auto_charts" in page and page["auto_charts"]:  # 逐行註解：若有自動偵測到的圖表。
                all_auto_charts.extend(page["auto_charts"])  # 逐行註解：加入總清單。
        
        # 動態調整圖表規則 prompt。
        if all_auto_charts:  # 逐行註解：若 Python 已成功從資料檔算出數據。
            chart_prompt_rule = "9. 程式已成功從資料檔（CSV/Excel/JSON）擷取並精確計算出圖表數據，你只需在回答中針對數據內容進行文字分析與解說即可。"
        else:  # 逐行註解：若 Python 無法從網頁中找到或讀取資料檔。
            chart_prompt_rule = "9. 【重要】目前無法從網頁中取得結構化資料檔（如 CSV/Excel），請不要輸出任何 JSON、不要輸出 {\"type\":\"chart\"}、不要自行猜測或虛構圖表數據。請直接在回答中說明資料取得失敗的原因（如：下載失敗、找不到連結等）。"

        # gemma4_thinking 可以顯示 thinking；其他 gemma4 系列會要求不要輸出 thinking process。
        thinking_rule = (  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
            "4. 這次選用 gemma4_thinking，允許輸出 thinking process，最後仍要給清楚的正式回答。"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            if selected_model in THINKING_MODELS  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            else "4. 不要輸出 thinking process、推理過程、草稿、自我對話。"  # 逐行註解：前面條件都不成立時，執行這個備用分支。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        prompt = f"""
你要根據「實際讀到的網頁內容」回答使用者問題。
規則：
1. 使用繁體中文回答。
2. 你已經先看過搜尋標題與摘要，並挑選最適合的連結實際打開；回答不能只介紹網址。
3. 優先使用「實際讀到的網頁內容」整理答案；如果有讀到內容，不要只說「網站沒有寫」。
{thinking_rule}
5. 回答最後加上「來源」清單，列出有用到的編號與網址。
6. 如果使用者問天氣、價格、新聞這類即時問題，要直接整理目前讀到的資訊，不要只叫使用者自己去點網址。
7. 如果所有連結都讀取失敗或沒有可用文字，才可以說沒有成功讀到網頁，並簡短說明已嘗試哪些來源。
8. 如果使用者問天氣但沒有提供地點，要明確說缺少地點；若搜尋結果仍有明確地點資料，可以先整理查到的內容並提醒地點可能不是使用者要的。
{chart_prompt_rule}

使用者問題：
{q}

對話記憶：
{memory_context}

搜尋摘要：
{search_context}

挑選要實際打開的連結：
{fetch_plan_context}

實際讀到的網頁內容：
{page_read_context}
""".strip()

        timeout_raw = (os.getenv("OLLAMA_TEXT_TIMEOUT_S", "0") or "").strip().lower()  # 逐行註解：設定 timeout_raw 這個變數，供後面的流程使用。
        if timeout_raw in {"0", "none", "off", "false", "no", ""}:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            timeout_s = None  # 逐行註解：設定 timeout_s 這個變數，供後面的流程使用。
        else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
            timeout_s = int(timeout_raw)  # 逐行註解：設定 timeout_s 這個變數，供後面的流程使用。
        await update_web_search_progress(  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            progress_message,  # 逐行註解：這行是跨行資料或參數的一個項目。
            "/web_search 進度\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            f"1. 搜尋完成：找到 {len(results)} 筆結果\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            f"2. 篩選完成：挑出 {len(fetch_candidates)} 個候選連結\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            f"3. 網頁讀取完成：成功讀到 {read_success_count} 個網頁\n"  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            "4. 正在等待 Ollama 回答…",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        # 第四階段：把搜尋摘要、已讀取網頁、對話記憶整理成 prompt，交給 Ollama 回答。
        ollama_reply, thinking_process = await ask_ollama_text(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
            selected_model,  # 逐行註解：這行是跨行資料或參數的一個項目。
            prompt,  # 逐行註解：這行是跨行資料或參數的一個項目。
            timeout_s=timeout_s,  # 逐行註解：設定 timeout_s 這個變數，供後面的流程使用。
            include_thinking=True,  # 逐行註解：設定 include_thinking 這個變數，供後面的流程使用。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        ollama_reply = ollama_reply.strip()  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。
        response = ollama_reply  # 逐行註解：依除錯需求保留這次 AI 回覆原文變數。
        debug_ai_response(response)  # 逐行註解：印出 === AI RESPONSE === 與完整 AI 回覆。
        # 來源連結由程式端強制附加，不只依賴模型自己列來源，避免 Discord 回答沒有網址。
        source_links = format_web_search_source_links(page_reads, fetch_candidates)  # 逐行註解：設定 source_links 這個變數，供後面的流程使用。
        
        # 收集所有可能的圖表（嚴禁使用 Ollama 生成的 JSON，改為純 Python 計算）：
        # 1. 來自讀取網頁資料集時，由 Python 自動精確計算產生的圖表。
        chart_payloads = []  # 逐行註解：初始化圖表 payload 清單。
        for page in page_reads:  # 逐行註解：遍歷所有讀取的網頁。
            if "auto_charts" in page and page["auto_charts"]:  # 逐行註解：若該頁面有 Python 自動產生的精確圖表。
                chart_payloads.extend(page["auto_charts"])  # 逐行註解：將自動產生的圖表加入發送清單。
        
        # 2. 若沒有自動圖表，才嘗試從使用者問題中直接解析標籤數值（例如：「蘋果10 橘子20」）。
        if not chart_payloads:  # 逐行註解：若目前尚無任何自動產生的數據圖表。
            fallback_payload = build_chart_payload_from_user_text(q)  # 逐行註解：嘗試從使用者原始問題中解析手打資料。
            if fallback_payload:  # 逐行註解：若解析成功。
                chart_payloads = [fallback_payload]  # 逐行註解：將該手動資料圖表存入清單。
        
        # 記憶體與結果處理：
        if not chart_payloads:  # 逐行註解：最終若沒有任何圖表要顯示。
            ollama_reply = append_source_links_to_reply(ollama_reply, source_links)  # 逐行註解：僅將來源連結加在 Ollama 的文字分析後。
            assistant_memory_text = ollama_reply  # 逐行註解：存入記憶的內容為完整文字回答。
        else:  # 逐行註解：若有成功的 Python 數據圖表。
            summaries = [chart_reply_summary(p) for p in chart_payloads]  # 逐行註解：產生每張圖表的完成摘要文字。
            assistant_memory_text = append_source_links_to_reply("\n".join(summaries), source_links)  # 逐行註解：記憶存入圖表摘要與來源。

        # 這裡故意存進共享記憶，不存進單一模型記憶，讓使用者換模型後仍能問「剛剛查到什麼」。
        web_search_memory_reply = f"這是上一筆 /web_search 查到並回答過的內容，後續使用者說「剛剛查到的」或「統整一下」時要接續這筆資料。\n\n{assistant_memory_text}"  # 逐行註解：把 web_search 回答包成更明確的記憶文字，讓後續聊天模型知道這是剛剛查到的資料。
        remember_conversation(interaction.user.id, SHARED_MEMORY_MODEL, f"/web_search {q}", web_search_memory_reply)  # 逐行註解：把 web_search 結果存進共享記憶，讓之後換模型聊天也能讀到剛剛查到的內容。
        thinking_sec = time.monotonic() - started  # 逐行註解：設定 thinking_sec 這個變數，供後面的流程使用。

        sep = "——————————————————"  # 逐行註解：設定 sep 這個變數，供後面的流程使用。
        author_name = (getattr(interaction.user, "global_name", None) or getattr(interaction.user, "display_name", None) or interaction.user.name or "").strip()  # 逐行註解：設定 author_name 這個變數，供後面的流程使用。
        author_account = str(interaction.user).strip()  # 逐行註解：設定 author_account 這個變數，供後面的流程使用。
        print(  # 逐行註解：把資訊印到終端機後台，方便觀察 bot 執行狀態。
            "\n".join(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
                [  # 逐行註解：開始建立一個跨多行的列表資料。
                    sep,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    f"使用者名稱：{author_name}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"使用者帳號：{author_account}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"使用者ID：{interaction.user.id}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"使用者詢問：/web_search {q}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    "工具：web_search",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"使用者選的模型：{selected_model}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"使用者填的問題：{q}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"Ollama查詢：{q}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"Ollama看的網址：\n{search_urls}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"搜尋結果數：{len(results)}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"Ollama查到的東西：\n{search_context}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"Ollama挑選要實際打開的連結：\n{fetch_plan_context}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"Ollama是否成功讀到至少一個網頁：{'是' if page_read_success else '否'}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"Ollama實際讀到的網頁內容：\n{page_read_context}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    *([f"完整 thinking process：\n{thinking_process}"] if thinking_process else []),  # 逐行註解：這行是跨行資料或參數的一個項目。
                    f"AI回覆：{assistant_memory_text}",  # 逐行註解：後台記錄送給使用者的結果，圖表時不印出原始 JSON。
                    f"思考時間：{thinking_sec:.2f}秒",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    sep,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    "",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                ]  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
    except asyncio.CancelledError:  # 逐行註解：/stop 取消 /web_search 任務時走這裡，避免把停止當成錯誤。
        if progress_message is not None:  # 逐行註解：如果進度訊息已建立，就把它改成停止提示。
            await update_web_search_progress(progress_message, STOP_AI_MESSAGE)  # 逐行註解：在原進度訊息顯示已停止。
        return  # 逐行註解：停止後直接結束，不送 AI 回覆。
    except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
        error_message = f"（發生錯誤：{type(e).__name__}: {str(e)[:300]}）"  # 逐行註解：設定 error_message 這個變數，供後面的流程使用。
        if progress_message is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            await update_web_search_progress(progress_message, error_message)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
            await interaction.followup.send(error_message, ephemeral=private_reply)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    finally:  # 逐行註解：不管 /web_search 正常完成、錯誤或停止，都要清掉 /stop 任務登記。
        finish_active_ai_run(interaction.user.id, active_ai_run)  # 逐行註解：如果目前登記仍是這次 /web_search 任務，就移除它。

    if not ollama_reply:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        ollama_reply = "（我沒有產生任何回覆）"  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。

    if chart_payloads:  # 逐行註解：如果 /web_search 回傳圖表資料，就送實際圖表圖片。
        await send_multiple_charts_to_interaction(interaction, chart_payloads, status_message=progress_message, ephemeral=private_reply)  # 逐行註解：一次發送所有產生的圖表圖片。
        if source_links:  # 逐行註解：圖表之外仍保留程式端整理出的來源連結。
            await send_text_to_interaction_channel(interaction, source_links, ephemeral=private_reply)  # 逐行註解：把來源連結送到同一個原頻道或 followup 備援。
        return  # 逐行註解：圖表已送出後結束，不再把 JSON 當文字顯示。

    chunks = textwrap.wrap(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
        ollama_reply,  # 逐行註解：這行是跨行資料或參數的一個項目。
        width=1800,  # 逐行註解：設定 width 這個變數，供後面的流程使用。
        break_long_words=False,  # 逐行註解：提前跳出目前這個迴圈。
        replace_whitespace=False,  # 逐行註解：設定 replace_whitespace 這個變數，供後面的流程使用。
    ) or [ollama_reply[:1800]]  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    await send_followup_chunks_with_temporary_thinking(  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        interaction,  # 逐行註解：這行是跨行資料或參數的一個項目。
        chunks,  # 逐行註解：送出全部分段，不再只顯示前三段，避免長回答被截斷。
        ephemeral=private_reply,  # 逐行註解：設定 ephemeral 這個變數，供後面的流程使用。
        thinking_text=thinking_process,  # 逐行註解：設定 thinking_text 這個變數，供後面的流程使用。
        first_message=progress_message,  # 逐行註解：設定 first_message 這個變數，供後面的流程使用。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。


@tree.command(name="run", description="進入終端模式執行指令")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def run_terminal(interaction: discord.Interaction):  # 逐行註解：定義非同步函式 run_terminal，可以搭配 await 處理 Discord 或網路等待。
    """輸入 /run，先跳出密碼視窗；密碼正確後進入終端模式，可輸入指令執行。"""  # 逐行註解：說明這個指令的用途。
    if not require_super_user(interaction.user):  # 逐行註解：先用 SUPER_USERS 檢查使用者，非超級使用者不能打開 /run 密碼視窗。
        await interaction.response.send_message(sensitive_permission_message(), ephemeral=True)  # 逐行註解：沒有敏感指令權限就回覆沒有權限。
        return  # 逐行註解：停止指令。

    if interaction.user.id in terminal_sessions:  # 逐行註解：判斷使用者是否已經在終端模式。
        # 退出終端模式
        session = terminal_sessions[interaction.user.id]  # 逐行註解：取得這個使用者的終端會話。
        del terminal_sessions[interaction.user.id]  # 逐行註解：從全局字典中刪除會話。

        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            await session["message"].edit(content="```\n終端模式已退出\n```")  # 逐行註解：編輯終端訊息表示已退出。
        except:  # 逐行註解：捕捉編輯訊息時發生的任何錯誤。
            pass  # 逐行註解：忽略編輯失敗的錯誤。

        await interaction.response.send_message("已退出終端模式", ephemeral=True)  # 逐行註解：回覆使用者已退出。
    else:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        # 進入終端模式 - 顯示密碼 Modal
        await interaction.response.send_modal(RunPasswordModal())  # 逐行註解：顯示密碼輸入 Modal。


@tree.command(name="agent", description="進入 Discord AI Agent 模式")  # 逐行註解：新增 /agent slash command，用來登入或退出 Agent mode。
async def agent(interaction: discord.Interaction):  # 逐行註解：定義 /agent 指令。
    """輸入 /agent，密碼正確後進入 Agent mode；再次輸入 /agent 會退出。"""  # 逐行註解：說明 Agent 指令用途。
    if not require_super_user(interaction.user):  # 逐行註解：先用 SUPER_USERS 檢查使用者，非超級使用者不能打開 /agent 密碼視窗。
        await interaction.response.send_message(sensitive_permission_message(), ephemeral=True)  # 逐行註解：沒有敏感指令權限就回覆沒有權限。
        return  # 逐行註解：停止指令。
    if interaction.user.id in agent_sessions:  # 逐行註解：如果使用者已經在 Agent mode，就把這次 /agent 當成退出。
        del agent_sessions[interaction.user.id]  # 逐行註解：移除 Agent session。
        await interaction.response.send_message("已退出 agent mode", ephemeral=True)  # 逐行註解：提示已退出。
        return  # 逐行註解：停止指令。
    await interaction.response.send_modal(AgentPasswordModal())  # 逐行註解：進入 Agent mode 前先跳出密碼視窗，流程和 /run 一樣。


#######################天氣功能#######################
def weather_api_missing_message() -> str:  # 建立天氣 API 金鑰缺少時的 Discord 安全提示。
    return f"尚未設定天氣 API 金鑰，無法查詢天氣資訊。\n目前讀取的 .env：{ENV_PATH if ENV_PATH else '未找到 .env'}\n支援名稱：API_KEY、WEATHER_API_KEY、OPENWEATHER_API_KEY、OPENWEATHERMAP_API_KEY"  # 回傳不含金鑰內容的提示文字。


def weather_value_text(value, suffix: str = "") -> str:  # 將天氣欄位值轉成顯示文字。
    if value is None or value == "":  # 如果欄位缺少資料，就不要顯示 None 或空字串。
        return "無資料"  # 回傳無資料。
    return f"{value}{suffix}"  # 回傳值加單位。


def parse_openweather_json_response(response: requests.Response, label: str) -> dict:  # 將 OpenWeather HTTP 回應轉成安全 JSON dict。
    try:  # 嘗試解析 API 回傳 JSON。
        data = response.json()  # 將 OpenWeather 回應轉成 dict。
    except ValueError as exc:  # 如果 API 回傳不是 JSON，就轉成人類可讀錯誤。
        raise ValueError(f"{label} 回傳格式不是 JSON，無法解析預報資料。") from exc  # 丟出安全錯誤，不把原始內容傳到 Discord。
    if not isinstance(data, dict):  # OpenWeather 應該回傳 JSON object。
        raise ValueError(f"{label} 回傳格式不是物件，無法解析預報資料。")  # 丟出安全錯誤。
    if response.status_code >= 400:  # HTTP 錯誤時要取出 OpenWeather 的 message。
        error_message = data.get("message", f"HTTP {response.status_code}") if isinstance(data, dict) else f"HTTP {response.status_code}"  # 取得安全錯誤摘要。
        raise ValueError(f"{label} 查詢失敗：{error_message}")  # 丟出人類可讀錯誤。
    return data  # 回傳解析後的 JSON dict。


def fetch_openweather_hourly_forecast(city_name: str) -> dict | None:  # 優先嘗試 OpenWeather hourly forecast API。
    global _hourly_forecast_error_shown  # 取用全域錯誤旗標。
    params = {"q": city_name, "appid": weather_api.api_key, "units": weather_api.units, "lang": weather_api.lang, "cnt": 48}  # 準備 hourly forecast 查詢參數，抓 48 小時方便湊完整 24 小時。
    last_error = ""  # 保存最後一個 hourly endpoint 失敗原因。
    for endpoint in OPENWEATHER_HOURLY_FORECAST_URLS:  # 依序嘗試可用的 hourly forecast endpoint。
        try:  # hourly endpoint 可能因方案權限回 401，所以不能讓整個 weather 失敗。
            response = requests.get(endpoint, params=params, timeout=20)  # 送出 hourly forecast API 請求。
            data = parse_openweather_json_response(response, "Hourly Forecast")  # 解析 hourly forecast 回應。
            if str(data.get("cod")) != "200":  # OpenWeather forecast 成功時 cod 應該是 200。
                last_error = str(data.get("message", "未知錯誤"))  # 保存 API message。
                continue  # 嘗試下一個 endpoint。
            if isinstance(data.get("list"), list) and data.get("list"):  # hourly forecast list 存在時才可使用。
                data["source_endpoint"] = endpoint  # 保存來源 endpoint，方便後台測試確認。
                return data  # 回傳真正 hourly forecast JSON。
            last_error = "hourly list 為空"  # 保存 list 缺失原因。
        except Exception as exc:  # 捕捉任何 hourly endpoint 失敗，之後可退回 forecast。
            last_error = f"{type(exc).__name__}: {str(exc)[:120]}"  # 保存安全錯誤摘要。
    if not _hourly_forecast_error_shown:  # 只在第一次時列印錯誤。
        print(f"Hourly Forecast 不可用，已改用一般 forecast。此訊息只顯示一次。原因：{last_error}")  # 後台說明 fallback 原因，不傳到 Discord。
        _hourly_forecast_error_shown = True  # 標記錯誤已顯示，避免重複列印。
    return None  # 回傳 None 讓呼叫端改用 forecast。


def fetch_openweather_forecast(city_name: str) -> dict:  # 呼叫 OpenWeather forecast API 取得 5 天 / 3 小時預報。
    params = {"q": city_name, "appid": weather_api.api_key, "units": weather_api.units, "lang": weather_api.lang, "cnt": 40}  # 準備 forecast API 查詢參數，抓滿 40 筆。
    response = requests.get(OPENWEATHER_FORECAST_URL, params=params, timeout=20)  # 送出 forecast API 請求並設定 timeout。
    data = parse_openweather_json_response(response, "Forecast")  # 解析 forecast API 回應。
    if str(data.get("cod")) != "200":  # OpenWeather forecast 成功時 cod 是字串 200。
        raise ValueError(f"Forecast 查詢失敗：{data.get('message', '未知錯誤')}")  # 丟出 API message，不傳原始 JSON。
    if not isinstance(data.get("list"), list) or not data.get("list"):  # forecast list 是後續表格和圖表的必要資料。
        raise ValueError("天氣 API 沒有 hourly/forecast list 資料，無法產生分時天氣表格或圖表。")  # 提供清楚錯誤。
    return data  # 回傳 forecast 原始 JSON 給 weather_utils 處理。


def fetch_weather_report_data(city_name: str) -> dict:  # 同步取得目前天氣與分時預報資料。
    if not weather_api or not weather_api.api_key:  # 如果沒有 API key，就不能查 OpenWeather。
        raise RuntimeError(weather_api_missing_message())  # 丟出設定錯誤，呼叫端會安全顯示。
    city = (city_name or "").strip()  # 整理城市名稱。
    if not city:  # 城市名稱不可空白。
        raise ValueError("請提供城市名稱。")  # 丟出清楚錯誤。
    hourly_data = fetch_openweather_hourly_forecast(city)  # 優先嘗試真正 hourly forecast。
    forecast_data = fetch_openweather_forecast(city)  # 仍然取得 5 天 forecast，讓整週表格不被 hourly 48 小時限制。
    hourly_source = hourly_data or forecast_data  # hourly 不可用時，24 小時圖表改用 3 小時 forecast 內插。
    first_item = hourly_source["list"][0]  # 使用第一筆分時預報建立摘要，不再呼叫 current weather endpoint。
    main_data = first_item.get("main", {}) if isinstance(first_item.get("main"), dict) else {}  # 取出第一筆 main 區塊。
    weather_items = first_item.get("weather", []) if isinstance(first_item.get("weather"), list) else []  # 取出第一筆 weather 清單。
    weather_item = weather_items[0] if weather_items and isinstance(weather_items[0], dict) else {}  # 取出第一筆天氣描述。
    wind_data = first_item.get("wind", {}) if isinstance(first_item.get("wind"), dict) else {}  # 取出第一筆 wind 區塊。
    city_data = forecast_data.get("city", {}) if isinstance(forecast_data.get("city"), dict) else {}  # 取出 forecast city 區塊。
    current_summary = {  # 建立摘要用 current-like 資料，但來源是 forecast 第一筆。
        "city_name": city_data.get("name") or city,  # 保存城市名稱。
        "country": city_data.get("country", ""),  # 保存國家代碼。
        "temperature_celsius": round(main_data["temp"], 1) if isinstance(main_data.get("temp"), (int, float)) else None,  # 保存實際溫度。
        "feels_like": round(main_data["feels_like"], 1) if isinstance(main_data.get("feels_like"), (int, float)) else None,  # 保存體感溫度。
        "temp_min": round(main_data["temp_min"], 1) if isinstance(main_data.get("temp_min"), (int, float)) else None,  # 保存最低溫。
        "temp_max": round(main_data["temp_max"], 1) if isinstance(main_data.get("temp_max"), (int, float)) else None,  # 保存最高溫。
        "humidity": main_data.get("humidity"),  # 保存濕度。
        "pressure": main_data.get("pressure"),  # 保存氣壓。
        "wind_speed": round(wind_data["speed"], 1) if isinstance(wind_data.get("speed"), (int, float)) else None,  # 保存風速。
        "clouds": first_item.get("clouds", {}).get("all") if isinstance(first_item.get("clouds"), dict) else None,  # 保存雲量。
        "description": weather_item.get("description", ""),  # 保存天氣描述。
        "icon_code": weather_item.get("icon", ""),  # 保存天氣圖示代碼。
        "raw_data": {"dt": first_item.get("dt"), "timezone": city_data.get("timezone", 0), "main": main_data, "weather": weather_items, "wind": wind_data, "name": city_data.get("name", city), "sys": {"country": city_data.get("country", "")}},  # 保存 forecast 轉出的 current-like 原始資料。
    }  # 結束摘要資料。
    return {"city_name": city, "current": current_summary, "current_raw": current_summary["raw_data"], "forecast": forecast_data, "hourly_forecast": hourly_source}  # 回傳完整天氣報告資料。


async def load_weather_report_data(city_name: str) -> dict:  # 非同步包裝天氣查詢，避免 requests 卡住 Discord event loop。
    return await asyncio.to_thread(fetch_weather_report_data, city_name)  # 把同步 API 查詢丟到背景執行緒。


def weather_report_city_label(weather_data: dict, fallback_city: str = "") -> str:  # 建立天氣報告標題用城市名稱。
    current = weather_data.get("current", {}) if isinstance(weather_data, dict) else {}  # 取出目前天氣摘要。
    forecast = weather_data.get("forecast", {}) if isinstance(weather_data, dict) else {}  # 取出 forecast JSON。
    forecast_city = forecast.get("city", {}) if isinstance(forecast.get("city"), dict) else {}  # 取出 forecast city 區塊。
    city = current.get("city_name") or forecast_city.get("name") or fallback_city or "指定城市"  # 依序取得城市名稱。
    country = current.get("country") or forecast_city.get("country") or ""  # 取得國家代碼。
    return f"{city}, {country}".strip(" ,")  # 回傳城市標籤。


def weather_icon_url_from_data(weather_data: dict) -> str:  # 從目前天氣資料取得 OpenWeather 圖示 URL。
    current = weather_data.get("current", {}) if isinstance(weather_data, dict) else {}  # 取出目前天氣摘要。
    icon_code = str(current.get("icon_code") or "").strip()  # 取出圖示代碼。
    if weather_api and icon_code:  # 只有在 weather_api 和 icon_code 都存在時才組圖示網址。
        return weather_api.get_icon_url(icon_code)  # 回傳 OpenWeather 圖示網址。
    return ""  # 沒有圖示時回傳空字串。


def forecast_day_max_rain_chance_text(weather_data: dict) -> str:  # 從完整 24 小時分時資料整理最高降雨機率文字。
    try:  # 分時資料可能不存在，所以用 try 保護摘要 Embed。
        headers, rows = get_today_hourly_table(weather_data)  # 取得今天每 3 小時表格。
        pop_index = headers.index("降雨機率")  # 找出降雨機率欄位位置。
        values = []  # 建立可比較的降雨機率數字清單。
        for row in rows:  # 逐列讀取降雨機率。
            text = str(row[pop_index] if len(row) > pop_index else "").replace("%", "").strip()  # 清掉百分比符號。
            if text.isdigit():  # 只處理純數字百分比。
                values.append(int(text))  # 加入數字清單。
        return f"{max(values)}%" if values else "無資料"  # 回傳最高降雨機率或無資料。
    except Exception:  # 如果分時資料缺少欄位，就不要讓摘要 Embed 崩潰。
        return "無資料"  # 回傳無資料。


def build_weather_summary_embed_from_data(weather_data: dict, fallback_city: str = "") -> discord.Embed:  # 建立當天天氣摘要 Embed。
    current = weather_data.get("current", {}) if isinstance(weather_data, dict) else {}  # 取出目前天氣摘要。
    summary_text = get_current_weather_summary(weather_data)  # 用 weather_utils 產生 deterministic 天氣摘要。
    description = str(current.get("description") or "").strip()  # 取出目前天氣描述。
    symbol = weather_symbol_for_text(description)  # 依描述挑選天氣符號。
    fields = [  # 建立 Embed 欄位清單。
        {"name": f"{WEATHER_TEMP} 目前溫度", "value": weather_value_text(current.get("temperature_celsius"), "°C"), "inline": True},  # 顯示目前溫度。
        {"name": f"{WEATHER_TEMP} 體感溫度", "value": weather_value_text(current.get("feels_like"), "°C"), "inline": True},  # 顯示體感溫度，缺值會變無資料。
        {"name": f"{WEATHER_HUMIDITY} 濕度", "value": weather_value_text(current.get("humidity"), "%"), "inline": True},  # 顯示濕度。
        {"name": f"{WEATHER_WIND} 風速", "value": weather_value_text(current.get("wind_speed"), "m/s"), "inline": True},  # 顯示風速，單位不留空白避免表格或 Embed 換行怪異。
        {"name": f"{WEATHER_TEMP} 最高 / 最低", "value": f"{weather_value_text(current.get('temp_max'), '°C')} / {weather_value_text(current.get('temp_min'), '°C')}", "inline": True},  # 顯示最高與最低溫。
        {"name": f"{WEATHER_UMBRELLA} 今日降雨機率", "value": forecast_day_max_rain_chance_text(weather_data), "inline": True},  # 顯示今日最高降雨機率。
        {"name": f"{WEATHER_CLOUD} 雲量", "value": weather_value_text(current.get("clouds"), "%"), "inline": True},  # 顯示雲量。
    ]  # 結束 Embed 欄位清單。
    return make_weather_summary_embed(f"{symbol} {weather_report_city_label(weather_data, fallback_city)} 天氣摘要", summary_text, fields=fields, thumbnail_url=weather_icon_url_from_data(weather_data))  # 回傳天氣摘要 Embed。


async def send_weather_summary_part(interaction: discord.Interaction, weather_data: dict, city_name: str) -> None:  # 傳送當天天氣摘要 Embed。
    embed = build_weather_summary_embed_from_data(weather_data, city_name)  # 建立摘要 Embed。
    await interaction.followup.send(embed=embed)  # 傳送摘要 Embed。


async def send_weather_table_part(interaction: discord.Interaction, title: str, headers: list[str], rows: list[list[str]], filename: str) -> None:  # 傳送 PNG 天氣表格圖片。
    if not rows:  # 如果表格沒有資料列，就提醒使用者。
        await interaction.followup.send(f"{ERROR} {title} 沒有可顯示的資料。")  # 傳送安全錯誤，不顯示原始 JSON。
        return  # 停止表格傳送。
    try:  # matplotlib 表格可能因資料或字型問題失敗，所以要捕捉。
        buffer = make_table_image(title, headers, rows)  # 用 matplotlib.table 在 BytesIO 產生 PNG 表格。
    except Exception as exc:  # 圖片表格產生失敗時不能讓 bot 崩潰。
        print(f"天氣表格圖片產生失敗：{type(exc).__name__}: {exc}")  # 後台印出錯誤摘要。
        traceback.print_exc()  # 完整印出 traceback 方便追蹤 matplotlib 問題。
        await interaction.followup.send(f"{ERROR} {title} 圖片產生失敗：{str(exc)[:300]}")  # Discord 只顯示安全錯誤。
        return  # 停止傳送。
    await interaction.followup.send(file=discord.File(buffer, filename=filename))  # 直接用 BytesIO 上傳 PNG 表格，不寫本機檔案。


async def send_week_table_part(interaction: discord.Interaction, weather_data: dict) -> None:  # 傳送整週天氣表格。
    headers, rows = get_weekly_weather_table(weather_data)  # 取得整週天氣表格資料。
    await send_weather_table_part(interaction, "整週天氣表格", headers, rows, "forecast_week_table.png")  # 傳送 PNG 表格。


async def send_weather_temperature_chart_part(interaction: discord.Interaction, weather_data: dict, city_name: str) -> None:  # 傳送當天氣溫雙線折線圖。
    try:  # 圖表資料或 matplotlib 可能失敗，所以要完整捕捉。
        times, real_temps, feels_like_temps = extract_today_temperature_series(weather_data)  # 取出今天溫度圖表序列。
        title = f"{weather_report_city_label(weather_data, city_name)} 當天氣溫"  # 建立圖表標題。
        buffer = make_temperature_line_chart(title, times, real_temps, feels_like_temps)  # 用 matplotlib 在 BytesIO 產生圖表。
    except Exception as exc:  # 任何圖表錯誤都不能讓 bot 崩潰。
        print(f"天氣氣溫圖表產生失敗：{type(exc).__name__}: {exc}")  # 後台印出錯誤摘要。
        traceback.print_exc()  # 依需求完整印出 traceback。
        await interaction.followup.send(f"{ERROR} 氣溫圖表產生失敗：{str(exc)[:300]}")  # Discord 只顯示安全錯誤。
        return  # 停止傳檔。
    await interaction.followup.send(file=discord.File(buffer, filename="weather_temperature.png"))  # 用 BytesIO 傳送氣溫圖，不存本機檔案。


async def send_humidity_chart_part(interaction: discord.Interaction, weather_data: dict, city_name: str) -> None:  # 傳送當天濕度折線圖。
    try:  # 圖表資料或 matplotlib 可能失敗，所以要完整捕捉。
        times, humidity_values = extract_today_humidity_series(weather_data)  # 取出今天濕度圖表序列。
        title = f"{weather_report_city_label(weather_data, city_name)} 當天濕度"  # 建立圖表標題。
        buffer = make_humidity_line_chart(title, times, humidity_values)  # 用 matplotlib 在 BytesIO 產生圖表。
    except Exception as exc:  # 任何圖表錯誤都不能讓 bot 崩潰。
        print(f"天氣濕度圖表產生失敗：{type(exc).__name__}: {exc}")  # 後台印出錯誤摘要。
        traceback.print_exc()  # 依需求完整印出 traceback。
        await interaction.followup.send(f"{ERROR} 濕度圖表產生失敗：{str(exc)[:300]}")  # Discord 只顯示安全錯誤。
        return  # 停止傳檔。
    await interaction.followup.send(file=discord.File(buffer, filename="weather_humidity.png"))  # 用 BytesIO 傳送濕度圖，不存本機檔案。


async def send_weather_period_part(interaction: discord.Interaction, weather_data: dict) -> None:  # 傳送當天相似天氣時段表格。
    headers, rows = group_today_weather_periods(weather_data)  # 取得幾點到幾點的相似天氣分組表格。
    await send_weather_table_part(interaction, "當天完整分時段天氣表格", headers, rows, "weather_period_table.png")  # 傳送 PNG 表格。


async def send_weather_hourly_part(interaction: discord.Interaction, weather_data: dict) -> None:  # 傳送當天每 3 小時原始表格。
    headers, rows = get_today_hourly_table(weather_data)  # 取得今天逐筆分時資料。
    await send_weather_table_part(interaction, "當天每小時天氣表格", headers, rows, "weather_hourly_table.png")  # 傳送 PNG 表格。


async def send_integrated_weather_report(interaction: discord.Interaction, city_name: str) -> str:  # 依序傳送完整天氣報告。
    weather_data = await load_weather_report_data(city_name)  # 先取得 current 與 forecast 真實 API 資料。
    memory_summary = f"{weather_report_city_label(weather_data, city_name)} 完整天氣報告：{get_current_weather_summary(weather_data)}"
    await send_weather_summary_part(interaction, weather_data, city_name)  # 1. 傳送當天天氣摘要。
    await send_week_table_part(interaction, weather_data)  # 2. 傳送整週天氣表格。
    await send_weather_temperature_chart_part(interaction, weather_data, city_name)  # 3. 傳送實際溫度與體感溫度折線圖。
    await send_humidity_chart_part(interaction, weather_data, city_name)  # 4. 傳送濕度折線圖。
    await send_weather_period_part(interaction, weather_data)  # 5. 傳送幾點到幾點的分時段表格。
    return memory_summary


def weather_rows_to_prompt_table(headers: list[str], rows: list[list[str]], max_rows: int | None = None) -> str:  # 將天氣表格資料轉成給 AI 讀的精簡文字表格。
    safe_headers = [str(header) for header in headers]  # 將表頭全部轉成字串，避免 None 進入 prompt。
    safe_rows = rows[:max_rows] if max_rows is not None else rows  # 依需求限制列數，None 代表全部保留。
    lines = [" | ".join(safe_headers)]  # 先加入表頭列。
    for row in safe_rows:  # 逐列把資料轉成固定分隔格式。
        normalized_row = [str(cell) for cell in row]  # 將每個欄位轉成字串。
        lines.append(" | ".join(normalized_row))  # 加入一列資料文字。
    if max_rows is not None and len(rows) > max_rows:  # 如果有被截斷，就在 prompt 標記還有更多資料。
        lines.append(f"（另有 {len(rows) - max_rows} 列未列出）")  # 加入截斷說明。
    return "\n".join(lines) if lines else "無資料"  # 回傳表格文字，沒有資料時回傳無資料。


def weather_alerts_prompt_text(weather_data: dict) -> str:  # 將主動警報判斷整理成 AI 可讀文字。
    alerts = get_weather_alert_messages(weather_data)  # 使用同一套危險天氣判斷，避免 AI 自己亂猜警報。
    if not alerts:  # 如果目前沒有達到警報門檻。
        return "目前 API 資料未達大雨、打雷、強風、颱風、暴風雨、龍卷風或土石流主動警報門檻。"  # 回傳清楚狀態。
    return "\n".join(alerts)  # 有警報時逐條列出。


def build_weather_question_context(weather_data: dict) -> str:  # 建立 /weather 問答模式的天氣資料上下文。
    summary_text = get_current_weather_summary(weather_data)  # 取得 deterministic 摘要，含穿著建議與警示。
    week_headers, week_rows = get_weekly_weather_table(weather_data)  # 取得整週天氣表格資料。
    hourly_headers, hourly_rows = get_today_hourly_table(weather_data)  # 取得完整 24 小時或分時資料。
    period_headers, period_rows = group_today_weather_periods(weather_data)  # 取得 00-24 的分時段整理資料。
    context_parts = [  # 用區塊組 prompt，讓模型知道每段資料用途。
        "【當天天氣摘要】",  # 標示摘要區塊。
        summary_text,  # 加入摘要文字。
        "【整週天氣表格】",  # 標示週表區塊。
        weather_rows_to_prompt_table(week_headers, week_rows),  # 加入整週表格文字。
        "【今天完整分時資料】",  # 標示逐時資料區塊。
        weather_rows_to_prompt_table(hourly_headers, hourly_rows),  # 加入 24 小時資料。
        "【今天 3 小時時段整理】",  # 標示時段資料區塊。
        weather_rows_to_prompt_table(period_headers, period_rows),  # 加入 8 段表格資料。
        "【危險天氣主動警報判斷】",  # 標示警報區塊。
        weather_alerts_prompt_text(weather_data),  # 加入警報判斷結果。
    ]  # 結束 prompt 區塊清單。
    return "\n".join(context_parts).strip()  # 回傳完整上下文。


def weather_action_rules_prompt() -> str:  # 建立 AI 可回傳的天氣專用動作 JSON 規則。
    lines = [  # 用清單組規則，避免多行字串難維護。
        "如果使用者問題明確要求天氣圖表或天氣表格，而且只要輸出該視覺化，請只輸出 JSON，不要加 Markdown 或解釋。",  # 說明何時使用天氣專用動作。
        "天氣動作 JSON 格式只能是：",  # 說明下面是固定格式。
        '{"type":"weather_action","action":"temperature_chart","message":"這是今天實際溫度與體感溫度折線圖。"}',  # 提供溫度圖動作範例。
        '{"type":"weather_action","action":"humidity_chart","message":"這是今天濕度折線圖。"}',  # 提供濕度圖動作範例。
        '{"type":"weather_action","action":"week_table","message":"這是整週天氣 PNG 表格。"}',  # 提供週表動作範例。
        '{"type":"weather_action","action":"period_table","message":"這是今天完整分時段 PNG 表格。"}',  # 提供分時段表格動作範例。
        '{"type":"weather_action","action":"full_report","message":"這是完整天氣報告。"}',  # 提供完整報告動作範例。
        "action 只能是 temperature_chart、humidity_chart、week_table、period_table、full_report。",  # 限制動作名稱。
        "如果使用者是在問建議、風險、需不需要帶傘、穿什麼、幾點適合出門，就直接用繁體中文回答，不要輸出 JSON。",  # 說明一般問答不要用動作 JSON。
    ]  # 結束規則清單。
    return "\n".join(lines).strip()  # 回傳天氣動作規則。


def weather_question_wants_visual(question: str) -> bool:  # 判斷使用者是否明確要求天氣圖表、表格或完整報告。
    text = (question or "").strip().lower()  # 整理問題文字並轉小寫，方便同時比對中英文。
    visual_keywords = (  # 建立會觸發視覺化輸出的關鍵字清單。
        "圖",  # 支援中文「圖」。
        "圖表",  # 支援中文「圖表」。
        "折線",  # 支援折線圖。
        "曲線",  # 支援曲線圖說法。
        "表格",  # 支援表格要求。
        "png",  # 支援使用者直接要求 PNG。
        "視覺化",  # 支援視覺化要求。
        "完整報告",  # 支援要求完整報告。
        "full report",  # 支援英文完整報告。
        "chart",  # 支援英文 chart。
        "graph",  # 支援英文 graph。
        "plot",  # 支援英文 plot。
        "table",  # 支援英文 table。
    )  # 結束視覺化關鍵字清單。
    return any(keyword in text for keyword in visual_keywords)  # 只要命中任一關鍵字就視為明確要求視覺化。


def weather_question_requests_rain_table(question: str) -> bool:  # 判斷使用者是否要求整天降雨量或降雨機率表格。
    text = (question or "").strip().lower()  # 整理問題文字。
    has_rain_word = any(word in text for word in ("雨", "降雨", "雨量", "rain", "precipitation"))  # 判斷是否和雨或降雨有關。
    has_table_word = any(word in text for word in ("表", "表格", "table", "列表"))  # 判斷是否明確要求表格。
    has_all_day_word = any(word in text for word in ("整天", "全天", "今天", "24", "每小時", "hourly", "整日"))  # 判斷是否要求整天或每小時。
    return has_rain_word and has_table_word and has_all_day_word  # 三個條件都成立才產生降雨量表。


def weather_question_requests_temperature_chart(question: str) -> bool:  # 判斷使用者是否要求溫度圖。
    text = (question or "").strip().lower()  # 整理問題文字。
    has_temp_word = any(word in text for word in ("溫度", "氣溫", "體感", "temperature", "temp"))  # 判斷是否和溫度有關。
    has_chart_word = any(word in text for word in ("圖", "圖表", "折線", "曲線", "chart", "graph", "plot"))  # 判斷是否要求圖表。
    return has_temp_word and has_chart_word  # 同時命中才產生溫度圖。


def weather_question_requests_humidity_chart(question: str) -> bool:  # 判斷使用者是否要求濕度圖。
    text = (question or "").strip().lower()  # 整理問題文字。
    has_humidity_word = any(word in text for word in ("濕度", "humidity"))  # 判斷是否和濕度有關。
    has_chart_word = any(word in text for word in ("圖", "圖表", "折線", "曲線", "chart", "graph", "plot"))  # 判斷是否要求圖表。
    return has_humidity_word and has_chart_word  # 同時命中才產生濕度圖。


def weather_question_requests_week_table(question: str) -> bool:  # 判斷使用者是否要求整週表格。
    text = (question or "").strip().lower()  # 整理問題文字。
    has_week_word = any(word in text for word in ("整週", "一週", "本週", "week", "weekly", "七天", "7天"))  # 判斷是否和整週有關。
    has_table_word = any(word in text for word in ("表", "表格", "table", "列表"))  # 判斷是否要求表格。
    return has_week_word and has_table_word  # 同時命中才產生整週表格。


def weather_question_requests_period_table(question: str) -> bool:  # 判斷使用者是否要求今天分時段表格。
    text = (question or "").strip().lower()  # 整理問題文字。
    has_period_word = any(word in text for word in ("時段", "分時", "每小時", "整天", "全天", "hourly", "period"))  # 判斷是否和分時有關。
    has_table_word = any(word in text for word in ("表", "表格", "table", "列表"))  # 判斷是否要求表格。
    has_rain_word = any(word in text for word in ("雨", "降雨", "雨量", "rain", "precipitation"))  # 判斷是否是降雨表，避免和一般分時段表混淆。
    return has_period_word and has_table_word and not has_rain_word  # 非降雨的分時需求才產生一般時段表。


async def send_weather_question_requested_visuals(interaction: discord.Interaction, weather_data: dict, city_name: str, question: str) -> list[str]:  # 依使用者問題直接傳送相關 PNG 圖表或表格。
    sent_labels: list[str] = []  # 記錄已傳送的視覺化項目，後續讓 AI 用文字解讀。
    if weather_question_requests_rain_table(question):  # 如果問題要求整天降雨量表。
        headers, rows = get_today_rain_table(weather_data)  # 取得今天 24 小時降雨量表資料。
        await send_weather_table_part(interaction, "今天整天降雨量表", headers, rows, "weather_rain_table.png")  # 傳送降雨量 PNG 表格。
        sent_labels.append("今天整天降雨量 PNG 表格")  # 記錄已傳送項目。
    if weather_question_requests_temperature_chart(question):  # 如果問題要求溫度圖。
        await send_weather_temperature_chart_part(interaction, weather_data, city_name)  # 傳送實際溫度與體感溫度折線圖。
        sent_labels.append("今天溫度雙線折線圖")  # 記錄已傳送項目。
    if weather_question_requests_humidity_chart(question):  # 如果問題要求濕度圖。
        await send_humidity_chart_part(interaction, weather_data, city_name)  # 傳送濕度折線圖。
        sent_labels.append("今天濕度折線圖")  # 記錄已傳送項目。
    if weather_question_requests_week_table(question):  # 如果問題要求整週表格。
        await send_week_table_part(interaction, weather_data)  # 傳送整週天氣 PNG 表格。
        sent_labels.append("整週天氣 PNG 表格")  # 記錄已傳送項目。
    if weather_question_requests_period_table(question):  # 如果問題要求分時段表格。
        await send_weather_period_part(interaction, weather_data)  # 傳送今天分時段 PNG 表格。
        sent_labels.append("今天分時段天氣 PNG 表格")  # 記錄已傳送項目。
    return sent_labels  # 回傳已傳送視覺化清單。


def weather_question_rules_prompt(question: str, force_text: bool = False) -> str:  # 依使用者問題決定要不要提供 JSON 圖表規則。
    if force_text:  # 如果程式已經直接傳送相關圖表或表格。
        return "系統已經依使用者問題傳送相關 PNG 圖表或表格；請只用 3 到 6 句繁體中文解讀重點與建議，不要輸出 JSON、Markdown code block、action 格式、Markdown 圖片連結、假圖片連結，也不要重新列出表格原文。"  # 強制 AI 只回答文字與結論。
    if weather_question_wants_visual(question):  # 使用者明確要求圖表、表格或完整報告時才開放 JSON 動作。
        return f"{weather_action_rules_prompt()}\n\n{chart_output_rules_prompt()}"  # 回傳天氣專用動作規則與既有圖表規則。
    return "這次使用者沒有明確要求圖表、表格或完整報告；請一定用一般繁體中文文字回答，不要輸出 JSON、Markdown code block 或任何 action 格式。"  # 一般問答禁止 JSON，避免「會不會下雨」誤觸動作格式。


def build_weather_question_prompt(city_name: str, question: str, weather_data: dict, sent_visuals: list[str] | None = None) -> str:  # 建立 /weather 可選問題的 AI prompt。
    city_label = weather_report_city_label(weather_data, city_name)  # 取得城市標籤。
    weather_context = build_weather_question_context(weather_data)  # 取得整理後天氣資料上下文。
    visual_labels = sent_visuals or []  # 取得已由程式傳送的視覺化清單。
    output_rules = weather_question_rules_prompt(question, force_text=bool(visual_labels))  # 依問題類型取得輸出規則，一般問題不再給 JSON 範例。
    visual_note = f"系統已另外傳送：{'、'.join(visual_labels)}。\n" if visual_labels else ""  # 將已傳送的圖表或表格告知 AI。
    return (  # 回傳完整 prompt 給 Ollama。
        "你是 Discord 天氣助理，必須根據下方 OpenWeather API 真實資料回答。\n"  # 指定角色與資料來源。
        "請使用繁體中文，不能把錯誤 JSON 或原始 API JSON 直接貼給使用者。\n"  # 限制輸出語言和資料格式。
        "如果資料不足，請明確說哪些資料不足，不要自行編造官方警報。\n"  # 避免模型捏造不存在的警報。
        "回答天氣建議時，要包含可執行建議，例如穿著、雨具、通勤或戶外活動注意事項。\n"  # 確保問答模式也有實用建議。
        "遇到大雨、雷雨、強風、颱風、暴風雨、龍卷風、土石流等字眼或警報資料，要用明確警告語氣提醒。\n\n"  # 要求危險天氣提醒。
        f"查詢城市：{city_label}\n"  # 放入城市名稱。
        f"使用者問題：{question.strip()}\n\n"  # 放入使用者問題。
        f"{visual_note}"  # 放入已傳送視覺化提示，沒有時是空字串。
        f"{output_rules}\n\n"  # 放入這次問題對應的輸出規則。
        f"{weather_context}\n"  # 放入整理後天氣資料。
    )  # 結束 prompt。


def weather_percent_to_int(text: str) -> int | None:  # 將「75%」這類文字安全轉成整數百分比。
    cleaned = str(text or "").replace("%", "").strip()  # 移除百分比符號與空白。
    if not cleaned.isdigit():  # 如果不是純數字，就代表沒有可用百分比。
        return None  # 回傳 None 讓呼叫端忽略。
    return int(cleaned)  # 回傳整數百分比。


def weather_text_contains_rain(text: str) -> bool:  # 判斷天氣描述是否包含雨或雷。
    normalized = str(text or "").lower()  # 整理描述文字並轉小寫。
    rain_words = ("雨", "雷", "storm", "rain", "shower", "thunder")  # 定義中英文降雨與雷雨關鍵字。
    return any(word in normalized for word in rain_words)  # 命中任一關鍵字就視為可能下雨。


def build_weather_rain_fallback_answer(city_name: str, weather_data: dict) -> str:  # 在 AI 回壞 JSON 時，用資料直接產生「會不會下雨」回答。
    city_label = weather_report_city_label(weather_data, city_name)  # 取得城市標籤。
    headers, rows = get_today_hourly_table(weather_data)  # 取得今天完整分時資料。
    time_index = headers.index("時間") if "時間" in headers else 0  # 找出時間欄位位置。
    weather_index = headers.index("天氣狀況") if "天氣狀況" in headers else 1  # 找出天氣欄位位置。
    pop_index = headers.index("降雨機率") if "降雨機率" in headers else 5  # 找出降雨機率欄位位置。
    rain_rows = []  # 建立可能下雨的時段清單。
    pop_values = []  # 建立所有可比較的降雨機率清單。
    for row in rows:  # 逐列檢查每個分時資料。
        pop_value = weather_percent_to_int(row[pop_index] if len(row) > pop_index else "")  # 讀取該列降雨機率。
        weather_text = str(row[weather_index] if len(row) > weather_index else "")  # 讀取該列天氣描述。
        if pop_value is not None:  # 如果降雨機率可用。
            pop_values.append(pop_value)  # 加入比較清單。
        if weather_text_contains_rain(weather_text) or (pop_value is not None and pop_value >= 30):  # 描述有雨雷或機率達 30% 就列為可能下雨。
            rain_rows.append((str(row[time_index] if len(row) > time_index else "未知時段"), weather_text, pop_value))  # 保存可能下雨時段。
    max_pop = max(pop_values) if pop_values else None  # 取得今日最高降雨機率。
    if rain_rows:  # 如果有可能下雨的時段。
        period_text = "、".join(f"{time_text} {weather_text} {pop_value if pop_value is not None else '無資料'}%" for time_text, weather_text, pop_value in rain_rows[:6])  # 整理前幾個重點時段。
        return f"{city_label} 今天有下雨機會，最高降雨機率約 {max_pop if max_pop is not None else '無資料'}%。較需要注意的時段是：{period_text}。建議出門帶摺疊傘或輕便雨衣，鞋子選防滑一點；如果要騎車或久待戶外，先看即時雷達，遇到雷聲或短時強降雨就先進室內。"  # 回傳有雨建議。
    return f"{city_label} 目前今天分時預報看起來不太會下雨，最高降雨機率約 {max_pop if max_pop is not None else '無資料'}%。可以不必特地帶大傘，但午後天氣仍可能變化，長時間在外建議放一把小摺疊傘備用；若看到天空快速轉暗、風變強或有雷聲，就先避開空曠處。"  # 回傳低雨機率建議。


def build_weather_general_fallback_answer(city_name: str, weather_data: dict) -> str:  # 在 AI 回壞 JSON 且不是雨量問題時，提供安全文字備援。
    city_label = weather_report_city_label(weather_data, city_name)  # 取得城市標籤。
    summary_text = get_current_weather_summary(weather_data)  # 取得 deterministic 天氣摘要。
    return f"{city_label} 天氣資料已查到，但 AI 回覆格式不正確，所以改用資料摘要回答：{summary_text}"  # 回傳不含 JSON 的安全備援。


def build_weather_question_fallback_answer(city_name: str, question: str, weather_data: dict) -> str:  # 依問題類型產生壞 JSON 時的文字備援。
    question_text = str(question or "")  # 將問題轉成字串。
    if weather_text_contains_rain(question_text) or "下雨" in question_text or "帶傘" in question_text or "雨傘" in question_text:  # 使用者問下雨或帶傘時用降雨專用答案。
        return build_weather_rain_fallback_answer(city_name, weather_data)  # 回傳降雨備援答案。
    return build_weather_general_fallback_answer(city_name, weather_data)  # 其他問題回傳摘要備援。


def weather_ai_reply_is_bad_visual_text(reply: str) -> bool:  # 判斷 AI 是否把已上傳的圖表或表格錯誤貼成文字。
    text = str(reply or "")  # 將回覆安全轉成字串。
    bad_patterns = (  # 建立不應出現在已傳 PNG 後文字回答中的模式。
        "![",  # Markdown 圖片語法代表模型在假裝插圖。
        "你的png",  # 假圖片連結常見文字。
        "圖片連結",  # 假圖片連結描述。
        "時間 | 天氣",  # 表格原文外洩。
        "時間|天氣",  # 表格原文外洩的無空格版本。
        "日期 | 天氣",  # 週表原文外洩。
        "日期|天氣",  # 週表原文外洩的無空格版本。
        "最高溫 | 最低溫",  # 週表欄位原文外洩。
        "降雨量表如下",  # 模型錯把已上傳的 PNG 表格重列成文字。
        "【今天完整分時資料】",  # prompt 區塊被模型直接複製。
        "【整週天氣表格】",  # prompt 區塊被模型直接複製。
        "weather_action",  # 動作 JSON 外洩。
    )  # 結束模式清單。
    lowered = text.lower()  # 轉小寫方便比對英文或混合文字。
    has_table_pipe_dump = text.count("|") >= 4  # 如果直線分隔符大量出現，通常代表模型把表格貼成文字。
    return has_table_pipe_dump or any(pattern.lower() in lowered for pattern in bad_patterns)  # 命中任一模式就視為不合格回答。


def parse_weather_ai_action(raw_text: str) -> dict | None:  # 解析 AI 是否要求傳送天氣專用圖表或表格。
    response = str(raw_text or "")  # 先把回覆轉成字串。
    lowered = response.lower()  # 轉成小寫方便辨識模型輸出的動作關鍵字。
    weather_action_names = {"temperature_chart", "humidity_chart", "week_table", "period_table", "full_report"}  # 定義可執行的天氣動作名稱。
    if "weather_action" not in lowered and not any(action_name in lowered for action_name in weather_action_names):  # 沒有天氣動作關鍵字就不是天氣專用動作。
        return None  # 回傳 None 代表走一般文字或既有圖表流程。
    try:  # JSON 解析可能失敗，所以要保護。
        json_text = extract_first_json_object_text(response)  # 從回覆抽出第一個 JSON object。
        if not json_text:  # 如果抓不到 JSON object。
            print_chart_traceback("找不到可解析的 weather_action JSON object")  # 後台印完整 traceback。
            return None  # 回傳 None 讓呼叫端顯示安全錯誤。
        data = json.loads(json_text)  # 將 JSON 文字轉成 dict。
    except Exception as exc:  # 捕捉 JSON 解析失敗。
        print(f"天氣 AI 動作 JSON 解析失敗：{type(exc).__name__}: {exc}")  # 後台印出錯誤摘要。
        traceback.print_exc()  # 完整印出 traceback。
        return None  # 回傳 None 讓呼叫端顯示安全錯誤。
    if not isinstance(data, dict):  # 動作資料必須是 dict。
        return None  # 格式不合時不處理。
    data_type = str(data.get("type") or "").strip().lower()  # 取出模型輸出的 type。
    action = str(data.get("action") or data.get("chart_type") or "").strip().lower()  # 同時支援 action 與模型誤寫的 chart_type。
    if data_type == "chart" and action in weather_action_names:  # 模型有時會誤把天氣動作寫成一般 chart。
        data["type"] = "weather_action"  # 轉成天氣專用動作格式。
        data["action"] = action  # 保存標準化 action。
        return data  # 回傳修正後的動作資料。
    if data_type != "weather_action":  # 只接受 type=weather_action。
        return None  # 不是天氣動作就交回一般流程。
    if action and action != str(data.get("action") or "").strip().lower():  # 如果 action 來自 chart_type。
        data["action"] = action  # 將 chart_type 補成 action。
    return data  # 回傳可執行的天氣動作資料。


def looks_like_weather_action_json(raw_text: str) -> bool:  # 判斷回覆是否像天氣動作 JSON，避免解析失敗後洩漏原文。
    response = str(raw_text or "")  # 將輸入轉成字串。
    lowered = response.lower()  # 轉小寫方便搜尋。
    weather_action_names = ("weather_action", "temperature_chart", "humidity_chart", "week_table", "period_table", "full_report")  # 定義需要攔截的天氣動作關鍵字。
    return "{" in response and any(action_name in lowered for action_name in weather_action_names)  # 只要像天氣動作 JSON 就攔截，避免格式破損時洩漏原文。


async def send_weather_ai_action(interaction: discord.Interaction, weather_data: dict, city_name: str, action_data: dict) -> bool:  # 執行 AI 決定的天氣專用圖表或表格動作。
    action = str(action_data.get("action") or "").strip().lower()  # 取出 action 名稱。
    message = str(action_data.get("message") or "").strip()  # 取出可選的說明文字。
    if message:  # 如果 AI 有提供說明文字。
        await send_interaction_text_chunks(interaction, force_common_traditional_chinese(message), ephemeral=False)  # 先傳送簡短說明。
    if action == "temperature_chart":  # 使用者要溫度雙線圖。
        await send_weather_temperature_chart_part(interaction, weather_data, city_name)  # 傳送既有實際溫度與體感溫度圖。
        return True  # 表示已處理。
    if action == "humidity_chart":  # 使用者要濕度圖。
        await send_humidity_chart_part(interaction, weather_data, city_name)  # 傳送既有濕度圖。
        return True  # 表示已處理。
    if action == "week_table":  # 使用者要整週 PNG 表格。
        await send_week_table_part(interaction, weather_data)  # 傳送整週表格圖片。
        return True  # 表示已處理。
    if action == "period_table":  # 使用者要當天分時段 PNG 表格。
        await send_weather_period_part(interaction, weather_data)  # 傳送分時段表格圖片。
        return True  # 表示已處理。
    if action == "full_report":  # 使用者明確要求完整報告。
        await send_weather_summary_part(interaction, weather_data, city_name)  # 傳送摘要 Embed。
        await send_week_table_part(interaction, weather_data)  # 傳送整週 PNG 表格。
        await send_weather_temperature_chart_part(interaction, weather_data, city_name)  # 傳送溫度圖。
        await send_humidity_chart_part(interaction, weather_data, city_name)  # 傳送濕度圖。
        await send_weather_period_part(interaction, weather_data)  # 傳送分時段 PNG 表格。
        return True  # 表示已處理。
    return False  # 不支援的 action 交給呼叫端處理。


async def answer_weather_question(interaction: discord.Interaction, city_name: str, question: str) -> str:  # /weather 有填問題時，用天氣資料交給 AI 回答，並回傳可寫入聊天記憶的摘要。
    weather_data = await load_weather_report_data(city_name)  # 先查 OpenWeather 真實資料。
    city_label = weather_report_city_label(weather_data, city_name)  # 取得城市標籤，讓聊天記憶保存清楚地點。
    wants_visual = weather_question_wants_visual(question)  # 先判斷這次問題是否明確要求圖表、表格或完整報告。
    sent_visuals = await send_weather_question_requested_visuals(interaction, weather_data, city_name, question)  # 先由程式直接傳送可確定的相關 PNG 圖表或表格。
    prompt = build_weather_question_prompt(city_name, question, weather_data, sent_visuals=sent_visuals)  # 建立含表格、時段、警報和輸出規則的 prompt。
    reply = await ask_ollama_text(DEFAULT_CHAT_MODEL, prompt)  # 使用預設文字模型回答天氣問題。
    reply = force_common_traditional_chinese(str(reply or "").strip())  # 確保回覆是繁體中文且去掉空白。
    if not reply:  # 如果模型沒有回任何內容。
        reply = "（AI 沒有產生任何回答。）"  # 提供安全備援訊息。
    if sent_visuals and weather_ai_reply_is_bad_visual_text(reply):  # 如果已傳 PNG 後模型仍貼出假圖或表格原文。
        reply = build_weather_question_fallback_answer(city_name, question, weather_data)  # 改用真實資料產生乾淨文字答案。
    action_data = parse_weather_ai_action(reply)  # 先檢查 AI 是否要求傳送天氣專用視覺化。
    if action_data and wants_visual and not sent_visuals:  # 只有尚未由程式傳送視覺化時才執行 weather_action。
        if await send_weather_ai_action(interaction, weather_data, city_name, action_data):  # 執行圖表或表格動作。
            action_label = str(action_data.get("action") or "weather_action").strip()  # 保存已執行動作名稱，讓後續 summary memory 看得懂。
            action_message = force_common_traditional_chinese(str(action_data.get("message") or "").strip())  # 保存 AI 提供的簡短說明。
            if action_message:  # 如果 action 有附說明，就把說明寫入記憶。
                return f"{city_label} 天氣問題「{question.strip()}」：{action_message}"  # 回傳給聊天記憶。
            return f"{city_label} 天氣問題「{question.strip()}」已傳送 {action_label} 視覺化。"  # 動作已送出就回傳記憶摘要。
        unsupported_reply = f"{ERROR} 不支援的天氣動作：{str(action_data.get('action') or '')[:80]}"  # 不支援時顯示安全錯誤。
        await send_interaction_text_chunks(interaction, unsupported_reply, ephemeral=False)  # 傳送安全錯誤。
        return unsupported_reply  # 避免把 JSON 原文送出，也讓記憶知道這次失敗。
    if action_data and (not wants_visual or sent_visuals):  # 一般問題或已傳圖表時不應該執行模型誤吐的 weather_action。
        fallback_reply = build_weather_question_fallback_answer(city_name, question, weather_data)  # 用真實資料產生文字備援。
        await send_interaction_text_chunks(interaction, fallback_reply, ephemeral=False)  # 傳送文字答案，不顯示 JSON。
        return fallback_reply  # 結束一般問答流程，並回傳給聊天記憶。
    if looks_like_weather_action_json(reply):  # 如果像 weather_action 但解析失敗。
        fallback_reply = build_weather_question_fallback_answer(city_name, question, weather_data)  # 不再叫使用者換句話，直接用資料回答。
        await send_interaction_text_chunks(interaction, fallback_reply, ephemeral=False)  # 傳送安全文字備援。
        return fallback_reply  # 避免把 JSON 原文送出，並回傳給聊天記憶。
    await send_interaction_text_chunks(interaction, reply, ephemeral=False)  # 一般回答或既有 chart JSON 交給共用傳送流程。
    return reply  # 回傳實際送出的文字，讓 /summary_memory 可讀到這次 weather 結果。


def sanitized_requests_error_summary(exc: requests.RequestException) -> str:  # 建立不含 URL 和 API key 的 requests 錯誤摘要。
    response = getattr(exc, "response", None)  # requests HTTPError 通常會帶 response 物件。
    status_code = getattr(response, "status_code", None)  # 從 response 取出 HTTP 狀態碼。
    if status_code is not None:  # 如果有狀態碼，就用狀態碼描述錯誤。
        return f"{type(exc).__name__}: HTTP {status_code}"  # 回傳不含 URL 的錯誤摘要。
    return type(exc).__name__  # 沒有狀態碼時只回傳錯誤類型，避免洩漏 query string。


async def handle_weather_command_error(interaction: discord.Interaction, exc: Exception) -> None:  # 統一處理 weather 指令錯誤。
    if isinstance(exc, requests.RequestException):  # requests 網路錯誤要顯示網路請求失敗。
        print(f"天氣網路請求失敗：{sanitized_requests_error_summary(exc)}")  # 後台也不印可能含 API key 的 URL。
        message = f"{ERROR} 網路請求失敗：請確認城市名稱或稍後再試。"  # Discord 端使用安全訊息，避免 HTTPError URL 洩漏 API key。
    elif isinstance(exc, RuntimeError):  # RuntimeError 多半是設定缺少 API key。
        message = f"{ERROR} {str(exc)[:1500]}"  # 建立安全錯誤訊息。
    elif isinstance(exc, ValueError):  # ValueError 是可預期的資料或使用者輸入錯誤。
        message = f"{ERROR} 查詢失敗：{str(exc)[:1500]}"  # 建立安全錯誤訊息。
    else:  # 其他錯誤要完整印 traceback。
        print(f"天氣功能發生非預期錯誤：{type(exc).__name__}: {exc}")  # 後台印出錯誤摘要。
        traceback.print_exc()  # 完整印出 traceback，方便修正。
        message = f"{ERROR} 發生錯誤：{type(exc).__name__}: {str(exc)[:300]}"  # Discord 只顯示安全摘要。
    await interaction.followup.send(message)  # 傳送安全錯誤訊息，不把錯誤 JSON 直接丟到 Discord。


async def defer_weather_command(interaction: discord.Interaction) -> bool:  # 共用 weather slash command 的權限檢查與 defer。
    if not is_allowed_interaction_user(interaction):  # 先依目前情境檢查權限，統一走 ALLOWED_USERS 與 SUPER_USERS。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 沒有權限就私下提醒。
        return False  # 回傳 False 讓呼叫端停止。
    await interaction.response.defer()  # 天氣 API 和圖表產生可能超過 3 秒，所以先 defer。
    return True  # 回傳 True 代表後續可以使用 followup。


@tree.command(name="weather", description="查詢城市天氣，可留白問題顯示完整報告")  # 註冊唯一 /weather 指令，支援完整報告與可選 AI 問答。
@discord.app_commands.describe(city_name="城市名稱", question="可選問題，留白就顯示完整天氣報告")  # 替 /weather 的城市與可選問題加上 Discord 顯示說明。
async def weather(interaction: discord.Interaction, city_name: str, question: str = ""):  # 定義 /weather 指令處理函式，question 有預設值所以可留白。
    if not await defer_weather_command(interaction):  # 權限不通過時停止。
        return  # 停止指令。
    try:  # 天氣查詢和傳送流程可能失敗。
        weather_question = (question or "").strip()  # 整理可選問題，空白代表走原本完整報告。
        if weather_question:  # 如果使用者有填問題，就改走 AI 天氣問答。
            weather_memory_text = await answer_weather_question(interaction, city_name, weather_question)  # 用真實天氣資料交給 AI 回答或產生視覺化。
            remember_conversation(interaction.user.id, SHARED_MEMORY_MODEL, f"/weather {city_name} {weather_question}", weather_memory_text)  # 把天氣問答寫進共享記憶，後面可直接要求總結。
            return  # 問答模式完成後不再送原本固定格式。
        weather_memory_text = await send_integrated_weather_report(interaction, city_name)  # 沒填問題時維持原本完整天氣報告。
        remember_conversation(interaction.user.id, SHARED_MEMORY_MODEL, f"/weather {city_name}", weather_memory_text)  # 把完整天氣報告摘要寫進共享記憶，讓 summary memory 可整理。
    except Exception as exc:  # 捕捉所有錯誤，避免 bot 崩潰。
        await handle_weather_command_error(interaction, exc)  # 用安全訊息回覆錯誤。


#######################啟動#######################
async def run_bot():  # 逐行註解：定義非同步函式 run_bot，可以搭配 await 處理 Discord 或網路等待。
    token = os.getenv("DC_BOT_TOKEN")  # 逐行註解：設定 token 這個變數，供後面的流程使用。
    if not token:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        raise RuntimeError("找不到 DC_BOT_TOKEN，請先設定 .env")  # 逐行註解：主動丟出錯誤，提醒設定或流程有問題。

    shutdown_event = asyncio.Event()  # 逐行註解：設定 shutdown_event 這個變數，供後面的流程使用。
    loop = asyncio.get_running_loop()  # 逐行註解：設定 loop 這個變數，供後面的流程使用。

    def _request_shutdown():  # 逐行註解：定義函式 _request_shutdown，把一段會重複使用的流程包起來。
        shutdown_event.set()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    for sig in (signal.SIGINT, signal.SIGTERM):  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            loop.add_signal_handler(sig, _request_shutdown)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        except NotImplementedError:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
            pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。

    bot_task = asyncio.create_task(bot.start(token))  # 逐行註解：設定 bot_task 這個變數，供後面的流程使用。
    shutdown_task = asyncio.create_task(shutdown_event.wait())  # 逐行註解：設定 shutdown_task 這個變數，供後面的流程使用。
    done, pending = await asyncio.wait(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
        {bot_task, shutdown_task},  # 逐行註解：這行是跨行資料或參數的一個項目。
        return_when=asyncio.FIRST_COMPLETED,  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。

    if shutdown_task in done and not bot_task.done():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await send_shutdown_dm()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        await bot.close()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。

    for task in pending:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        task.cancel()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    if bot_task in done:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await send_shutdown_dm()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
    else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            await bot_task  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        except asyncio.CancelledError:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
            pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。


def main():  # 逐行註解：定義函式 main，把一段會重複使用的流程包起來。
    asyncio.run(run_bot()) # 從環境變數拿到機器人的 token，然後啟動機器人
    print("有人打招呼了！") # 在終端機印出「有人打招呼了！」，讓我們知道這件事發生了
#如果這份檔案室「直接執行」，
# 就呼叫 main() 啟動機器人！

if __name__=="__main__":  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
    main() #正式啟用程式

"""
工具筆記：
一、這次我用到的工具

1. rg
   rg 是 ripgrep，用來快速搜尋整個檔案裡的關鍵字。
   我用它找 web_search、fetch_web_pages、followup.send、thinking 等位置。
   用途是先定位真正要改的區塊，不用用眼睛從頭慢慢翻到尾。

2. sed
   sed 可以印出檔案中的指定行數範圍。
   我用它查看某幾段程式碼，例如 /web_search 附近、底部 main 附近。
   用途是確認上下文，避免只看單行就亂改。

3. nl
   nl 會把檔案內容加上行號印出來。
   我用它看每段程式碼的行號，方便確認註解加在哪裡，也方便最後回報位置。

4. apply_patch
   apply_patch 是用來修改檔案的工具。
   我用它手動改 import 註解、/web_search 註解、來源連結註解、共享記憶註解、上線通知註解，以及這段多行工具筆記。
   好處是每次改動都有明確的上下文，比直接整份覆蓋安全。

5. python3 -m py_compile
   這個指令只檢查 Python 語法能不能編譯。
   它不會真的啟動 Discord bot，也不會連線 Discord。
   我用它確認加註解後沒有弄壞括號、縮排、字串或語法。

6. git diff --check
   這個指令檢查 diff 裡有沒有格式問題。
   例如多餘空白、壞掉的縮排、行尾空白等。
   我用它確認改註解時沒有留下容易造成版本管理問題的格式髒污。

7. ast
   ast 是 Python 內建的語法樹解析工具。
   我用它確認 AI.py 仍然能被 Python 正常解析，
   也確認 /web_search 的 decorator 還是掛在真正的 web_search 函式上。

8. tokenize
   tokenize 是 Python 內建的詞法分析工具。
   我用它分辨哪些行是一般程式碼、哪些行是在多行字串裡。
   這很重要，因為不能把 # 註解硬塞進 prompt 或工具筆記的多行字串內容裡，
   不然會改變 bot 實際丟給 Ollama 的 prompt。

9. python
   python 是用來執行目前 bot 相同環境的 Python 指令。
   我用它做過共享記憶的小測試：
   先把一筆 /web_search 結果存進 SHARED_MEMORY_MODEL，
   再用 DEFAULT_CHAT_MODEL 讀取 format_conversation_memory，
   確認普通聊天模型真的讀得到剛剛搜尋過的內容。

二、這份檔案匯入的模組筆記

1. asyncio
   asyncio 是 Python 內建的非同步工具。
   這支 bot 需要同時等 Discord 訊息、等網頁回應、等 Ollama 回答。
   如果不用 asyncio，等待其中一件事時整個 bot 可能會卡住。

2. discord
   discord 是 discord.py 套件。
   它負責跟 Discord 溝通，例如登入 bot、接收訊息、發送訊息、建立 slash 指令、顯示 Modal。

3. os
   os 在這裡主要用來讀環境變數。
   例如 DC_BOT_TOKEN、SUPER_USERS、ALLOWED_USERS、DISCORD_BOT_QUIT_PASSWORD 都是透過 os.getenv 讀出來。

4. dotenv.load_dotenv
   load_dotenv 會讀取 .env 檔案。
   讀完後，.env 裡的設定就可以被 os.getenv 拿到。

5. textwrap
   textwrap 用來切長文字。
   Discord 單則訊息有長度限制，所以 AI 回覆太長時要切成多段送出。

6. json
   json 用來處理 JSON 格式。
   Ollama 的 HTTP API 需要 JSON request，也會回傳 JSON response。

7. base64
   base64 用來把圖片 bytes 轉成文字。
   Ollama vision API 的 images 欄位需要這種格式，才能把 Discord 附件圖片送去分析。

8. uuid
   uuid 用來產生不重複 ID。
   這裡可用來建立不容易撞名的圖片檔名。

9. pathlib.Path
   Path 用來處理檔案和資料夾路徑。
   比直接手寫字串路徑安全，也比較容易跨資料夾操作。

10. urllib.request
   urllib.request 在這份檔案裡被命名成 urlrequest。
   它負責送 HTTP request，例如打開 DuckDuckGo 搜尋頁或實際讀取搜尋結果網頁。

11. urllib.parse
   urllib.parse 在這份檔案裡被命名成 urlparse。
   它負責處理網址，例如把搜尋文字做 URL 編碼、解析 query string、還原 DuckDuckGo 的 uddg 真正網址。

12. urllib.error.URLError / HTTPError
   這兩個是網路請求可能發生的錯誤類型。
   URLError 偏向連線層級問題，HTTPError 偏向伺服器回傳錯誤狀態碼。

13. html.parser.HTMLParser
   HTMLParser 是 Python 內建 HTML 解析器。
   這份檔案用它解析 DuckDuckGo 搜尋結果，也用它把網頁 HTML 轉成可餵給 Ollama 的純文字。

14. time
   time 用來計算時間。
   這份檔案用 time.monotonic 計算使用者發問後，到搜尋、讀網頁、Ollama 回覆完成總共花多久。

15. re
   re 是正規表達式工具。
   這份檔案用它清掉 ANSI 控制碼、移除 thinking process、判斷文字規則和搜尋關鍵字。

16. signal
   signal 用來處理系統訊號。
   例如你按 Ctrl+C 或系統要求程式結束時，bot 可以先做收尾流程，再關閉。

三、目前重要功能筆記

1. 權限只分兩層
   SUPER_USERS 是超級使用者，可以使用所有功能與敏感指令。
   ALLOWED_USERS 是一般允許使用者，可以聊天與使用一般指令。
   SUPER_USERS 會自動被視為 ALLOWED_USERS，所以不用重複寫兩次。
   不在 SUPER_USERS 或 ALLOWED_USERS 裡的人會收到「你沒有權限使用這個 Bot。」。
   agent、state、run、quit、restart、shell、shutdown、reload、eval、exec、debug、admin 這些敏感功能只看 SUPER_USERS。
   （註：stop 功能已開放給所有授權使用者使用）

2. 上線和下線通知流程
   send_startup_dm 會解析 ALLOWED_USERS 加 SUPER_USERS，然後私訊「Bot 已上線。」。
   send_shutdown_dm 會解析同一份權限清單，然後私訊「Bot 即將下線。」。
   startup_dm_sent 和 shutdown_dm_sent 是防重複旗標，用來避免 Discord 重連或多個關閉入口造成重複通知。
   如果某一個使用者找不到或不能私訊，程式會在後台印出收件人與錯誤原因，但不會讓整個 bot 崩潰。

3. 對話記憶分成共享記憶和模型記憶
   SHARED_MEMORY_MODEL 是共享記憶的特殊 key，不是真正的 Ollama 模型名稱。
   /web_search 完成後會把整理後的回答和來源連結存進共享記憶。
   一般聊天會同時讀共享記憶和目前模型自己的記憶。
   這樣使用者先用 gemma4_thinking 跑 /web_search，後面換成 qwen2.5-coder:1.5b_chat 問「統整一下剛剛你查到的資訊」時，仍然能讀到剛剛的搜尋結果。

4. 記憶目前只存在程式記憶體
   conversation_memory 是 Python dict，所以 bot 重啟後記憶會清空。
   如果要讓 web_search 記憶跨重啟保留，之後要再加檔案或資料庫儲存。
   目前的設計是先解決同一次 bot 執行期間的上下文記憶。

5. 記憶長度設定
   CONVERSATION_MEMORY_MAX_CHARS 控制丟給 Ollama 的總記憶文字量，預設 12000。
   CONVERSATION_MEMORY_ENTRY_MAX_CHARS 控制單筆使用者訊息或 AI 回覆最多保存幾個字，預設 6000。
   會把單筆從原本 1200 字提高，是因為 /web_search 的回答通常很長，太短會讓後續統整拿不到重點和來源。

6. /web_search 進度和來源
   /web_search 的進度數字不是假寫死的。
   搜尋完成數量來自 search_web_results 實際回傳的結果數。
   篩選完成數量來自 select_results_for_fetch 挑出的候選連結數。
   網頁讀取完成數量來自 fetch_web_pages 實際讀到文字的網頁數。
   回答最後的來源連結由 format_web_search_source_links 和 append_source_links_to_reply 強制附加，
   所以就算模型自己忘記貼網址，程式也會把讀取成功、讀取失敗或只列入搜尋結果的連結補到 Discord 回覆底下。
"""
