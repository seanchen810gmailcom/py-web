#######################模組#######################
# 下面每個 import 都是這支 Discord bot 會用到的工具，右邊註解寫它負責哪一塊。
import asyncio  # 匯入 asyncio：負責非同步等待，例如等 Discord、網頁、Ollama 回應時不讓整個 bot 卡死。
import discord  # 匯入 discord.py：負責連線 Discord、收訊息、發訊息、建立 slash 指令和 Modal。
import os  # 匯入 os：負責讀取環境變數，例如 .env 裡載入的 Discord token、密碼、允許使用者 ID。
from dotenv import load_dotenv  # 匯入 load_dotenv：把 .env 檔案讀進環境變數，讓 os.getenv 可以拿到設定。
import textwrap  # 匯入 textwrap：把太長的 AI 回覆切成多段，避免超過 Discord 單則訊息長度限制。
import json  # 匯入 json：把 Python dict 轉成 JSON，或把 Ollama HTTP API 回傳的 JSON 轉回 Python 資料。
import base64  # 匯入 base64：把圖片 bytes 編碼成 Ollama vision API 可以接收的文字格式。
import uuid  # 匯入 uuid：產生不重複的圖片檔名，避免不同圖片輸出時互相覆蓋。
from pathlib import Path  # 匯入 Path：用比較安全、清楚的方式處理資料夾與檔案路徑。
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

#######################初始化#######################
load_dotenv() # 讀取.env檔案Ｍ讓程式可以拿到DC_BOT_TOKEN這類資料


def split_env_list(value: str) -> list[str]:  # 逐行註解：定義函式 split_env_list，把 .env 裡用逗點分隔的白名單切成清單。
    """把 .env 裡的 a,b,c 轉成 ["a", "b", "c"]，空白和空項目會被自動忽略。"""  # 逐行註解：說明這個函式怎麼處理逗點白名單。
    return [item.strip() for item in (value or "").split(",") if item.strip()]  # 逐行註解：用逗點切開字串，去掉空白，只留下有內容的項目。


def unique_env_items(items: list[str]) -> list[str]:  # 逐行註解：定義函式 unique_env_items，把環境變數清單去掉重複項目。
    """保留原本順序，同時移除重複的 ID，避免同一個人收到兩次上線或下線通知。"""  # 逐行註解：說明這個函式會保留順序並避免重複通知。
    unique_items: list[str] = []  # 逐行註解：建立最後要回傳的不重複清單。
    seen_items: set[str] = set()  # 逐行註解：建立已看過項目的集合，用來快速判斷是否重複。
    for item in items:  # 逐行註解：逐一檢查傳進來的每個 ID 或文字項目。
        if item in seen_items:  # 逐行註解：如果這個項目已經出現過，就不要再加入一次。
            continue  # 逐行註解：跳過這個重複項目，繼續檢查下一個項目。
        seen_items.add(item)  # 逐行註解：把第一次出現的項目記錄起來，之後遇到同樣項目就能跳過。
        unique_items.append(item)  # 逐行註解：把第一次出現的項目加入最後要使用的清單。
    return unique_items  # 逐行註解：回傳已經去重複、但仍保留原本順序的清單。


# 只允許特定人聊天：
# 注意：Discord Bot 端拿不到使用者 email，所以「seanchen810@gmail.com」只能當作
# 你的 Discord 帳號名稱/顯示名稱來比對；最穩定的是改用 user id（ALLOWED_DISCORD_USER_ID）。
# ALLOWED_CHAT_USER / ALLOWED_DISCORD_USER_ID / ALLOWED_DISCORD_USER_IDS 是「誰可以使用 bot」。
# STARTUP_DM_USER_ID / STARTUP_DM_USER_IDS 是「bot 上線、下線時要主動通知誰」，用途不同。
# 如果要讓多個人收到上線、下線私訊，請在 .env 寫 STARTUP_DM_USER_IDS=數字ID1,數字ID2。
ALLOWED_CHAT_USER = os.getenv("ALLOWED_CHAT_USER","seanchen810@gmail.com").strip()  # 逐行註解：設定 ALLOWED_CHAT_USER 這個變數，供後面的流程使用。
ALLOWED_CHAT_USERS = set(split_env_list(ALLOWED_CHAT_USER))  # 逐行註解：把 ALLOWED_CHAT_USER 轉成可支援逗點多人的白名單集合。
ALLOWED_DISCORD_USER_ID = os.getenv("ALLOWED_DISCORD_USER_ID", "").strip()  # 逐行註解：設定 ALLOWED_DISCORD_USER_ID 這個變數，供後面的流程使用。
ALLOWED_DISCORD_USER_ID_LIST = split_env_list(ALLOWED_DISCORD_USER_ID)  # 逐行註解：把 ALLOWED_DISCORD_USER_ID 轉成可支援逗點多人的 ID 清單。
ALLOWED_DISCORD_USER_IDS_EXTRA = split_env_list(os.getenv("ALLOWED_DISCORD_USER_IDS", ""))  # 逐行註解：另外支援複數版 ALLOWED_DISCORD_USER_IDS，方便之後寫得更直覺。
ALLOWED_DISCORD_USER_IDS = set(ALLOWED_DISCORD_USER_ID_LIST + ALLOWED_DISCORD_USER_IDS_EXTRA)  # 逐行註解：合併單數和複數環境變數，變成真正用來判斷的 ID 白名單。
PRIMARY_ALLOWED_DISCORD_USER_ID = (ALLOWED_DISCORD_USER_ID_LIST + ALLOWED_DISCORD_USER_IDS_EXTRA + [""])[0]  # 逐行註解：取第一個白名單 ID，給啟動私訊預設值使用。
STARTUP_DM_USER_ID = os.getenv("STARTUP_DM_USER_ID", PRIMARY_ALLOWED_DISCORD_USER_ID or "1390880884554600559").strip()  # 逐行註解：設定 STARTUP_DM_USER_ID 這個變數，供後面的流程使用。
STARTUP_DM_USER_IDS_RAW = os.getenv("STARTUP_DM_USER_IDS", "").strip()  # 逐行註解：讀取多人上線/下線私訊清單，格式是多個 Discord 數字 ID 用逗點隔開。
STARTUP_DM_USER_IDS_FALLBACK = split_env_list(STARTUP_DM_USER_ID) + ALLOWED_DISCORD_USER_ID_LIST + ALLOWED_DISCORD_USER_IDS_EXTRA  # 逐行註解：如果沒有設定多人清單，就沿用舊的單人 ID 和白名單 ID 當預設收件人。
STARTUP_DM_USER_IDS = unique_env_items(split_env_list(STARTUP_DM_USER_IDS_RAW) or STARTUP_DM_USER_IDS_FALLBACK)  # 逐行註解：決定真正要收到上線/下線私訊的所有 Discord 數字 ID。
DISCORD_BOT_QUIT_PASSWORD = os.getenv("DISCORD_BOT_QUIT_PASSWORD", "").strip()  # 逐行註解：設定 DISCORD_BOT_QUIT_PASSWORD 這個變數，供後面的流程使用。
NO_PERMISSION_MESSAGE = "（你沒有權限使用這個機器人）"  # 逐行註解：統一設定沒有白名單權限時要回覆給使用者的文字。
startup_dm_sent = False  # 逐行註解：設定 startup_dm_sent 這個變數，供後面的流程使用。
shutdown_dm_sent = False  # 逐行註解：設定 shutdown_dm_sent 這個變數，供後面的流程使用。

# 預設文字聊天模型：用 qwen2.5-coder:1.5b 套繁中聊天 Modelfile。
DEFAULT_CHAT_MODEL = "qwen2.5-coder:1.5b_chat"  # 逐行註解：設定 DEFAULT_CHAT_MODEL 這個變數，供後面的流程使用。

# DM 模式下，每個使用者可以選擇目前要用的模型
DM_MODELS = (  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
    DEFAULT_CHAT_MODEL,  # 逐行註解：這行是跨行資料或參數的一個項目。
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
AGENT_MAX_RETRIES = 5  # 逐行註解：Agent 每個任務最多修正/重試 5 次，避免無限 loop。
AGENT_COMMAND_TIMEOUT_SECONDS = 90  # 逐行註解：Agent 執行 shell command 的 timeout，避免長時間指令卡死 Discord bot。
AGENT_MODEL = "gemma4_agent_discord-bot"  # 逐行註解：Agent 模式固定使用這個專用模型，不讀使用者目前在聊天模式選的模型。

# 對話記憶有兩層：
# 1. 共享記憶：同一個使用者的 /web_search 結果會存在這裡，讓不同模型都看得到。
# 2. 模型記憶：同一個使用者在某個模型下的一般聊天會存在這裡，避免不同模型互相污染風格。
# 送進 Ollama 時不限制固定輪次，而是塞到接近 max token 預算為止。
# 這裡用字元數粗估 token；如果想調整總記憶量，可以在 .env 設 CONVERSATION_MEMORY_MAX_CHARS。
# 如果想調整單筆訊息保留多長，可以在 .env 設 CONVERSATION_MEMORY_ENTRY_MAX_CHARS。
SHARED_MEMORY_MODEL = "__shared_user_memory__"  # 逐行註解：建立一個共享記憶用的特殊名稱，讓 web_search 結果可以被所有文字模型看到。
CONVERSATION_MEMORY_MAX_CHARS = int(os.getenv("CONVERSATION_MEMORY_MAX_CHARS", "12000"))  # 逐行註解：設定 CONVERSATION_MEMORY_MAX_CHARS 這個變數，供後面的流程使用。
CONVERSATION_MEMORY_ENTRY_MAX_CHARS = int(os.getenv("CONVERSATION_MEMORY_ENTRY_MAX_CHARS", "6000"))  # 逐行註解：設定單筆對話最多保存幾個字，避免 web_search 長回答被 1200 字切太短。
conversation_memory: dict[tuple[int, str], list[dict[str, str]]] = {}  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。

# 圖片只存到這個資料夾，送出後會刪掉（避免誤刪其他地方的檔案）
IMAGE_DIR = (Path.home() / "discord_bot_generated_images").resolve()  # 逐行註解：設定 IMAGE_DIR 這個變數，供後面的流程使用。
IMAGE_DIR.mkdir(parents=True, exist_ok=True)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

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

bot = discord.Client(intents=intents) # 建立機器人本體，並把 intents 交給它
tree = discord.app_commands.CommandTree(bot) # 建立一個「指令樹」，讓我們可以在裡面登記指令


def is_allowed_discord_user(user) -> bool:  # 逐行註解：定義函式 is_allowed_discord_user，把一段會重複使用的流程包起來。
    """檢查這個 Discord 使用者是不是允許操作 bot 的人。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if ALLOWED_DISCORD_USER_IDS:  # 逐行註解：如果有設定 Discord 使用者 ID 白名單，就優先用 ID 判斷，最穩定。
        return str(user.id) in ALLOWED_DISCORD_USER_IDS  # 逐行註解：檢查這個使用者 ID 是否在逗點白名單裡。

    author_candidates = {  # 逐行註解：開始建立一個跨多行的字典或集合資料。
        (user.name or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
        (getattr(user, "global_name", None) or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
        (getattr(user, "display_name", None) or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
        str(user).strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
    }  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
    return bool(ALLOWED_CHAT_USERS & author_candidates)  # 逐行註解：如果沒有 ID 白名單，就改用名稱白名單和使用者名稱集合做交集比對。


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


async def run_thinking_animation(message: discord.Message, stop_event: asyncio.Event, model_name: str):  # 逐行註解：定義 Thinking 動畫 coroutine，會反覆 edit 同一則訊息。
    """在 AI 正式回答前循環顯示模型名稱 Thinking 動畫。"""  # 逐行註解：正式回答開始前會先 stop，避免兩個 coroutine 同時 edit。
    frame_index = 0  # 逐行註解：記錄目前要顯示第幾格動畫。
    while not stop_event.is_set():  # 逐行註解：只要外部還沒有要求停止，就持續播放動畫。
        frame = THINKING_FRAMES[frame_index % len(THINKING_FRAMES)]  # 逐行註解：用取餘數方式讓動畫清單循環。
        ok = await safe_edit_message(message, thinking_animation_text(model_name, frame))  # 逐行註解：安全更新同一則訊息成目前動畫格。
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
    if first_message is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await safe_edit_message(first_message, chunks[0])  # 逐行註解：把 /web_search 的進度訊息改成正式回答第一段。
        for chunk in chunks[1:]:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
            await interaction.followup.send(chunk, ephemeral=ephemeral)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    for chunk in chunks:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        await interaction.followup.send(chunk, ephemeral=ephemeral)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。


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


def format_conversation_memory(user_id: int, model: str) -> str:  # 逐行註解：定義函式 format_conversation_memory，把一段會重複使用的流程包起來。
    """把共享記憶和目前模型記憶整理進 prompt；不限制輪次，只塞到 max token 預算附近。"""  # 逐行註解：說明這裡會同時讀共享記憶和目前模型自己的記憶。
    shared_history = get_conversation_memory(user_id, SHARED_MEMORY_MODEL)  # 逐行註解：先取出這位使用者的共享記憶，例如之前 web_search 查到的內容。
    model_history = [] if model == SHARED_MEMORY_MODEL else get_conversation_memory(user_id, model)  # 逐行註解：再取目前模型自己的記憶；如果本來就在讀共享記憶，就避免重複讀一次。
    history = shared_history + model_history  # 逐行註解：把共享記憶放前面、模型自己的記憶放後面，讓所有模型都能接續 web_search 的上下文。
    if not history:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return "無"  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    lines: list[str] = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    used_chars = 0  # 逐行註解：設定 used_chars 這個變數，供後面的流程使用。
    for item in reversed(history):  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        role = "使用者" if item.get("role") == "user" else "AI"  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        content = (item.get("content") or "").strip()  # 逐行註解：設定 content 這個變數，供後面的流程使用。
        if content:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            line = f"{role}：{content}"  # 逐行註解：設定 line 這個變數，供後面的流程使用。
            used_chars += len(line)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            if used_chars > CONVERSATION_MEMORY_MAX_CHARS:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                break  # 逐行註解：提前跳出目前這個迴圈。
            lines.append(line)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    lines.reverse()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    return "\n".join(lines) if lines else "無"  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


def build_prompt_with_memory(user_id: int, model: str, user_text: str) -> str:  # 逐行註解：定義函式 build_prompt_with_memory，把一段會重複使用的流程包起來。
    """把 max token 預算內的對話記憶一起交給 Ollama，讓每個模型都能接續上下文。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    user_text = (user_text or "").strip()  # 逐行註解：設定 user_text 這個變數，供後面的流程使用。
    memory_context = format_conversation_memory(user_id, model)  # 逐行註解：設定 memory_context 這個變數，供後面的流程使用。
    if memory_context == "無":  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return user_text  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    return f"""
以下是你和這位使用者的對話記憶，已自動保留到接近 max token 預算為止。
請用它理解上下文、記住使用者剛剛要你做什麼，但不要逐字重複記憶內容。

對話記憶：
{memory_context}

使用者現在的新訊息：
{user_text}
""".strip()


def remember_conversation(user_id: int, model: str, user_text: str, assistant_text: str) -> None:  # 逐行註解：定義函式 remember_conversation，把一段會重複使用的流程包起來。
    """保存使用者訊息與 AI 回覆；一般聊天按模型分開記，web_search 可存進共享記憶。"""  # 逐行註解：說明記憶可以分模型保存，也可以保存到共享記憶給所有模型使用。
    user_text = (user_text or "").strip()  # 逐行註解：設定 user_text 這個變數，供後面的流程使用。
    assistant_text = (assistant_text or "").strip()  # 逐行註解：設定 assistant_text 這個變數，供後面的流程使用。
    if not user_text and not assistant_text:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    key = (user_id, model)  # 逐行註解：設定 key 這個變數，供後面的流程使用。
    history = conversation_memory.setdefault(key, [])  # 逐行註解：設定 history 這個變數，供後面的流程使用。
    if user_text:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        history.append({"role": "user", "content": user_text[:CONVERSATION_MEMORY_ENTRY_MAX_CHARS]})  # 逐行註解：保存使用者訊息，但最多保留設定好的單筆字數，避免記憶爆太大。
    if assistant_text:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        history.append({"role": "assistant", "content": assistant_text[:CONVERSATION_MEMORY_ENTRY_MAX_CHARS]})  # 逐行註解：保存 AI 回覆，web_search 長回答也能保留更多內容。


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
        # DuckDuckGo 的結果標題會放在 class="result__a" 的 <a> 裡。
        if tag == "a" and "result__a" in classes:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            self._in_title = True  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            self._title_parts = []  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
            self._current_href = attr.get("href") or ""  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        # 搜尋摘要會放在 result__snippet，之後會接到最後一筆結果上。
        elif "result__snippet" in classes:  # 逐行註解：前面的 if 不成立時，改檢查這個額外條件。
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
            headers={"User-Agent": "Mozilla/5.0"},  # 逐行註解：設定 headers 這個變數，供後面的流程使用。
            method="GET",  # 逐行註解：設定 method 這個變數，供後面的流程使用。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        with urlrequest.urlopen(req, timeout=15) as resp:  # 逐行註解：開啟需要自動收尾的資源，例如網路回應或檔案。
            html = resp.read().decode("utf-8", errors="replace")  # 逐行註解：設定 html 這個變數，供後面的流程使用。
        parser = DuckDuckGoResultParser()  # 逐行註解：設定 parser 這個變數，供後面的流程使用。
        parser.feed(html)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
        return parser.results[:limit]  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    # urllib 是同步阻塞工具，放到 thread 裡跑，才不會卡住 Discord bot。
    return await asyncio.to_thread(_search)  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


async def fetch_web_pages(  # 逐行註解：定義非同步函式 fetch_web_pages，可以搭配 await 處理 Discord 或網路等待。
    results: list[dict[str, str]],  # 逐行註解：這行是跨行資料或參數的一個項目。
    *,  # 逐行註解：這行是跨行資料或參數的一個項目。
    limit: int = 5,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    min_attempts: int = 3,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    min_successful: int = 1,  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
) -> list[dict[str, str]]:  # 逐行註解：這行開啟一個程式區塊，下面縮排內容會一起執行。
    """實際打開挑過的搜尋結果網址；如果前幾個讀不到，繼續試到至少一個成功。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    selected = results[:limit]  # 逐行註解：設定 selected 這個變數，供後面的流程使用。

    def _fetch_one(item: dict[str, str]) -> dict[str, str]:  # 逐行註解：定義函式 _fetch_one，把一段會重複使用的流程包起來。
        url = item["url"]  # 逐行註解：設定 url 這個變數，供後面的流程使用。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
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
    # await：等這件事完成後再繼續往下
    # return：直接結束函式
    # tree.sync()：把slash 指令送去Discord登記
    await tree.sync() # 把我們在程式裡登記的指令，同步到 Discord 上，讓她知道我們有哪些指令可以用


@bot.event  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def on_disconnect():  # 逐行註解：定義非同步函式 on_disconnect，可以搭配 await 處理 Discord 或網路等待。
    pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。


async def send_startup_dm():  # 逐行註解：定義非同步函式 send_startup_dm，可以搭配 await 處理 Discord 或網路等待。
    # 這裡不是權限判斷，而是主動通知清單；清單來自 STARTUP_DM_USER_IDS。
    global startup_dm_sent  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    if startup_dm_sent:  # 逐行註解：如果這次啟動已經送過上線通知，就不要重複送給大家。
        return  # 逐行註解：直接結束函式，避免 Discord 重連時同一批人一直收到上線通知。
    for user_id in STARTUP_DM_USER_IDS:  # 逐行註解：逐一拿出要收到上線通知的每個 Discord 數字使用者 ID。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            user = await bot.fetch_user(int(user_id))  # 逐行註解：用 Discord 數字 ID 取得使用者物件，這樣才能主動發私訊。
            await user.send("我上線嘍，可以開始為您服務了！")  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
            print(f"上線私訊失敗（{user_id}）：{type(e).__name__}: {e}")  # 逐行註解：把哪個使用者 ID 發送失敗印出來，方便檢查 .env 有沒有填錯。
    startup_dm_sent = True  # 逐行註解：整批上線通知跑完後標記已送過，避免重複發送。


async def send_shutdown_dm():  # 逐行註解：定義非同步函式 send_shutdown_dm，可以搭配 await 處理 Discord 或網路等待。
    # 關閉通知跟上線通知用同一份 STARTUP_DM_USER_IDS 清單，確保大家都知道 bot 下線。
    global shutdown_dm_sent  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    if shutdown_dm_sent:  # 逐行註解：如果這次關閉流程已經送過下線通知，就不要重複送給大家。
        return  # 逐行註解：直接結束函式，避免多個關閉入口造成重複下線私訊。
    for user_id in STARTUP_DM_USER_IDS:  # 逐行註解：逐一拿出要收到下線通知的每個 Discord 數字使用者 ID。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            user = await bot.fetch_user(int(user_id))  # 逐行註解：用 Discord 數字 ID 取得使用者物件，這樣才能主動發私訊。
            await user.send("我先下線了，掰掰！")  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
            print(f"下線私訊失敗（{user_id}）：{type(e).__name__}: {e}")  # 逐行註解：把哪個使用者 ID 發送失敗印出來，方便檢查 .env 有沒有填錯。
    shutdown_dm_sent = True  # 逐行註解：整批下線通知跑完後標記已送過，避免重複發送。


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

    # 檢查是否在 Agent 模式；Agent 模式會把下一則訊息當成任務，不走一般聊天。
    if message.author.id in agent_sessions and not message.author.bot:  # 逐行註解：判斷使用者是否已登入 Agent 模式。
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

    # 只回覆白名單；不在白名單時，DM 或提到 bot 的伺服器訊息會明確回覆沒有權限。
    if not is_allowed_discord_user(message.author):  # 逐行註解：檢查這個訊息作者是否不在白名單裡。
        if should_reply_no_permission_to_message(message):  # 逐行註解：判斷這種沒有權限的訊息是否應該回覆，避免伺服器一般聊天洗版。
            await message.channel.send(NO_PERMISSION_MESSAGE)  # 逐行註解：告訴非白名單使用者沒有權限，而不是直接不理。
        return  # 逐行註解：沒有權限時結束處理，不繼續呼叫 Ollama。

    user_text = (message.content or "").strip()  # 逐行註解：設定 user_text 這個變數，供後面的流程使用。

    # 伺服器頻道：禁止「你說話就回答」；只能用 /ask 觸發
    # 私訊(DM)：保留原本體驗，直接問直接答
    if message.guild is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    # 如果是 Discord 指令（例如 /hello），就不要當成一般聊天內容來回覆
    if user_text.startswith("/"):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    if user_text.lower() == "hello": # 如果這則訊息的內容是 hello
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
    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
        if _is_dm(message):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            selected_model = dm_user_model.get(message.author.id, DEFAULT_CHAT_MODEL)  # 逐行註解：設定 selected_model 這個變數，供後面的流程使用。
        else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
            selected_model = DEFAULT_CHAT_MODEL  # 逐行註解：設定 selected_model 這個變數，供後面的流程使用。

        if _is_dm(message) and selected_model == "x/flux2-klein:latest":  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
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

        # 文字模型也支援「圖片 + 文字」：使用者傳圖片時，讓 gemma4 系列模型分析
        image_attachment: discord.Attachment | None = None  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        for att in (message.attachments or []):  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
            # 只抓第一張圖片
            if (att.content_type or "").startswith("image/") or (att.filename or "").lower().endswith((".png", ".jpg", ".jpeg", ".webp")):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                image_attachment = att  # 逐行註解：設定 image_attachment 這個變數，供後面的流程使用。
                break  # 逐行註解：提前跳出目前這個迴圈。

        response_message = await message.channel.send(thinking_animation_text(selected_model, THINKING_FRAMES[0]))  # 逐行註解：先送出同一則之後要被 edit 的 Thinking 訊息。
        thinking_stop_event = asyncio.Event()  # 逐行註解：建立停止 Thinking 動畫的事件，正式回答前會先觸發它。
        thinking_task = asyncio.create_task(run_thinking_animation(response_message, thinking_stop_event, selected_model))  # 逐行註解：啟動 Thinking 動畫，動畫只 edit response_message 這一則。
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
            if image_attachment is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                # 下載圖片 bytes（不落地）後丟給 vision
                img_bytes = await image_attachment.read()  # 逐行註解：設定 img_bytes 這個變數，供後面的流程使用。
                prompt_for_ollama = build_prompt_with_memory(author_id, selected_model, user_text)  # 逐行註解：設定 prompt_for_ollama 這個變數，供後面的流程使用。
                ollama_reply, thinking_process = await ask_ollama_vision(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
                    selected_model,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    prompt_for_ollama,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    img_bytes,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    timeout_s=timeout_s,  # 逐行註解：設定 timeout_s 這個變數，供後面的流程使用。
                    include_thinking=True,  # 逐行註解：設定 include_thinking 這個變數，供後面的流程使用。
                )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
                ollama_reply = ollama_reply.strip()  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。
                attachment_info = f"{image_attachment.filename} ({len(img_bytes)} bytes)"  # 逐行註解：設定 attachment_info 這個變數，供後面的流程使用。
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
            remember_conversation(author_id, selected_model, user_text, ollama_reply)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            thinking_sec = time.monotonic() - started  # 逐行註解：設定 thinking_sec 這個變數，供後面的流程使用。
            lines = [  # 逐行註解：開始建立一個跨多行的列表資料。
                sep,  # 逐行註解：這行是跨行資料或參數的一個項目。
                f"使用者名稱：{author_name}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                f"使用者帳號：{author_account}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                f"使用者ID：{author_id}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                f"使用者詢問：{user_text}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                "工具：無",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                f"使用者選的模型：{selected_model}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            ]  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            if attachment_info:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                lines.append(f"圖片：{attachment_info}")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            if thinking_process:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                lines.append(f"完整 thinking process：\n{thinking_process}")  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
            lines.extend(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
                [  # 逐行註解：開始建立一個跨多行的列表資料。
                    f"AI回覆：{ollama_reply}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
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

        await show_temporary_thinking_process(response_message, thinking_process)  # 逐行註解：如果有 thinking process，就先用 code box 顯示 3 秒，下一步正式回答會覆蓋。
        await stream_lines_to_message(response_message, ollama_reply)  # 逐行註解：正式回答開始後，一行一行 edit 原本的 Thinking 訊息。
    except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
        await message.channel.send(f"（發生錯誤：{type(e).__name__}: {str(e)[:300]}）")  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
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
    if not is_allowed_discord_user(interaction.user):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await interaction.response.send_message("（你沒有權限使用這個指令）", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    await interaction.response.send_modal(QuitPasswordModal())  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。


@tree.command(name="hello",description="Say hello to the bot")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def hello(interaction: discord.Interaction):  # 逐行註解：定義非同步函式 hello，可以搭配 await 處理 Discord 或網路等待。
    """輸入/hello，機器人會回傳hey!"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    # interaction 就是這次使用指令時送來的資料包
    # 裡面包含是誰按的，在哪裡暗的，指令相關資訊
    if not is_allowed_discord_user(interaction.user):  # 逐行註解：slash 指令也統一檢查白名單，不在名單就不能用。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：告訴非白名單使用者沒有權限。
        return  # 逐行註解：沒有權限時直接結束，不執行 hello 指令。
    await interaction.response.send_message("Hey!") # 回覆這個指令，內容是 Hello, World!
    #!只會傳給使用者

@tree.command(name="dm", description="Send me a DM (for testing DM chat)")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def dm(interaction: discord.Interaction, text: str):  # 逐行註解：定義非同步函式 dm，可以搭配 await 處理 Discord 或網路等待。
    """輸入 /dm <文字>，機器人會私訊你同樣的文字（用來測試 DM 功能）"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if not is_allowed_discord_user(interaction.user):  # 逐行註解：測試 DM 指令也要先檢查白名單。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限時回覆提醒。
        return  # 逐行註解：沒有權限時停止，不發私訊。
    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
        await interaction.user.send(text)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        await interaction.response.send_message("已私訊你了", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
    except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
        await interaction.response.send_message(f"私訊失敗：{type(e).__name__}", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。


@tree.command(name="model", description="(DM only) Select the model for DM chat")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
@discord.app_commands.choices(  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
    model=[  # 逐行註解：開始建立一個跨多行的列表資料。
        discord.app_commands.Choice(name="qwen2.5-coder:1.5b_chat (default text)", value="qwen2.5-coder:1.5b_chat"),  # 逐行註解：這行是跨行資料或參數的一個項目。
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
    if not is_allowed_discord_user(interaction.user):  # 逐行註解：切換模型也要檢查白名單，避免非授權者改模型。
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

    # 只回覆白名單；這裡和一般 DM 訊息使用同一個 is_allowed_discord_user，避免權限判斷不一致。
    if not is_allowed_discord_user(interaction.user):  # 逐行註解：檢查 slash 指令使用者是否不在白名單裡。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限時明確回覆，而不是直接不理。
        return  # 逐行註解：沒有權限時結束，不繼續呼叫 Ollama。

    q = (question or "").strip()  # 逐行註解：設定 q 這個變數，供後面的流程使用。
    if not q:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await interaction.response.send_message("請輸入問題", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    await interaction.response.defer(ephemeral=True, thinking=True)  # 逐行註解：先 defer，避免 Ollama 等太久讓 Discord 指令逾時。
    response_message = await interaction.followup.send(  # 逐行註解：建立同一則之後要反覆 edit 的 slash followup 訊息。
        thinking_animation_text(DEFAULT_CHAT_MODEL, THINKING_FRAMES[0]),  # 逐行註解：一開始先顯示目前模型名稱和第一格 Thinking 動畫。
        ephemeral=True,  # 逐行註解：/ask 原本是私人回覆，這裡保持 ephemeral。
        wait=True,  # 逐行註解：需要拿到 Message 物件，後面才能 edit 同一則。
    )  # 逐行註解：結束 followup.send 呼叫。
    thinking_stop_event = asyncio.Event()  # 逐行註解：建立停止 Thinking 動畫的事件。
    thinking_task = asyncio.create_task(run_thinking_animation(response_message, thinking_stop_event, DEFAULT_CHAT_MODEL))  # 逐行註解：啟動 /ask 專用 Thinking 動畫 task。

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
        remember_conversation(interaction.user.id, DEFAULT_CHAT_MODEL, q, ollama_reply)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
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
                    f"AI回覆：{ollama_reply}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"思考時間：{thinking_sec:.2f}秒",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    sep,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    "",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                ]  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
    except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
        thinking_stop_event.set()  # 逐行註解：發生錯誤時也要先停止 Thinking 動畫，避免它繼續 edit。
        try:  # 逐行註解：等待動畫 task 收尾。
            await thinking_task  # 逐行註解：確保動畫已經停止。
        except Exception as stop_error:  # 逐行註解：如果動畫停止失敗，把錯誤印到後台。
            print(f"/ask Thinking 動畫停止失敗：{type(stop_error).__name__}: {stop_error}")  # 逐行註解：輸出動畫停止錯誤。
        await safe_edit_message(response_message, f"（發生錯誤：{type(e).__name__}: {str(e)[:300]}）")  # 逐行註解：把同一則 Thinking 訊息改成錯誤訊息。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    thinking_stop_event.set()  # 逐行註解：Ollama 回覆完成後，先停止 Thinking 動畫。
    try:  # 逐行註解：等待動畫 task 完全結束，避免逐行顯示同時 edit。
        await thinking_task  # 逐行註解：確保只有接下來的 stream_lines_to_message 在 edit response_message。
    except Exception as e:  # 逐行註解：動畫停止失敗時不要靜默，印出錯誤。
        print(f"/ask Thinking 動畫停止失敗：{type(e).__name__}: {e}")  # 逐行註解：把停止錯誤印到後台。

    if not ollama_reply:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        ollama_reply = "（我沒有產生任何回覆）"  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。

    await show_temporary_thinking_process(response_message, thinking_process)  # 逐行註解：如果有 thinking process，就先用 code box 顯示 3 秒，下一步正式回答會覆蓋。
    await stream_lines_to_message(  # 逐行註解：把 /ask 正式回答一行一行顯示在同一則訊息上。
        response_message,  # 逐行註解：第一則要 edit 的訊息就是原本的 Thinking 訊息。
        ollama_reply,  # 逐行註解：要逐行顯示的 AI 正式回答。
        send_extra=lambda content: interaction.followup.send(content, ephemeral=True, wait=True),  # 逐行註解：如果超過單則長度，就用 ephemeral followup 發下一則。
    )  # 逐行註解：結束逐行顯示呼叫。


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


def parse_top_physmem(line: str) -> dict:  # 逐行註解：解析 top 的 PhysMem 行，作為 /debugstate 比對用。
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
    """使用 psutil available 口徑計算 RAM，並保留 top PhysMem raw 給 /debugstate。"""  # 逐行註解：避免 mem.used 和 mem.percent 在 macOS 上看起來互相矛盾。
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
        text="Use /debugstate for raw sensor data."
    )  # 逐行註解：底部說明。

    return embed  # 逐行註解：回傳 Embed。

def build_debug_state_embed(stats: dict) -> discord.Embed:  # 逐行註解：建立 /debugstate 的資料來源檢查面板。
    cpu = stats["cpu"]  # 逐行註解：取出 CPU 資料。
    ram = stats["ram"]  # 逐行註解：取出 RAM 資料。
    gpu = stats["gpu"]  # 逐行註解：取出 GPU 資料。
    temp = stats["temperature"]  # 逐行註解：取出溫度資料。
    fans = stats["fans"]  # 逐行註解：取出風扇資料。
    raw = stats.get("raw") or {}  # 逐行註解：取出原始資料來源。
    lines = [  # 逐行註解：建立 debug 內容。
        "DEBUG STATE",  # 逐行註解：標題。
        "",  # 逐行註解：空行。
        f"top CPU raw: {cpu.get('top_raw') or 'N/A'}",  # 逐行註解：顯示 top CPU 原始行。
        f"top parsed: {cpu.get('top_parsed') or {}}",  # 逐行註解：顯示 top 解析值。
        f"psutil CPU total(avg cores): {format_percent(cpu.get('psutil_total'))}",  # 逐行註解：顯示 psutil per-core 平均。
        f"per-core CPU: {cpu.get('psutil_cores') or cpu.get('cores') or []}",  # 逐行註解：顯示每核心資料。
        "",  # 逐行註解：空行。
        f"RAM source: {ram.get('source')}",  # 逐行註解：顯示 RAM 來源。
        f"RAM final: {format_bytes_gb(ram.get('used'))} / {format_bytes_gb(ram.get('total'))} ({format_percent(ram.get('percent'))})",  # 逐行註解：顯示 RAM 最終值。
        f"top PhysMem raw: {ram.get('top_raw') or 'N/A'}",  # 逐行註解：顯示 top PhysMem 原始行。
        f"top PhysMem parsed: {ram.get('top_parsed') or {}}",  # 逐行註解：顯示 top PhysMem 解析值。
        "",  # 逐行註解：空行。
        f"GPU source: {gpu.get('source')}",  # 逐行註解：顯示 GPU 來源。
        f"GPU final estimate: {format_percent(gpu.get('total'))}",  # 逐行註解：顯示 GPU estimate 最終值。
        f"GPU attempts: {gpu.get('attempts')}",  # 逐行註解：顯示 GPU 嘗試來源。
        "powermetrics GPU raw:",  # 逐行註解：標示 raw 輸出。
        short_debug_text(raw.get("powermetrics_gpu_power") or gpu.get("powermetrics_raw") or raw.get("powermetrics_gpu_all") or "N/A", 900),  # 逐行註解：顯示 powermetrics GPU raw 或 sudo 失敗訊息。
        "",  # 逐行註解：空行。
        f"Temperature source: {temp.get('source')}",  # 逐行註解：顯示溫度來源。
        f"Temperature final CPU/GPU: {format_temperature(temp.get('cpu_max'))} / {format_temperature(temp.get('gpu_max'))}",  # 逐行註解：顯示 CPU/GPU 溫度。
        f"Fan source: {fans.get('source')}",  # 逐行註解：顯示風扇來源。
        f"Fan final: {fans.get('fans') or 'N/A'}",  # 逐行註解：顯示風扇最終資料。
        "powermetrics SMC raw:",  # 逐行註解：標示 SMC raw。
        short_debug_text(raw.get("powermetrics_smc") or temp.get("powermetrics_raw") or fans.get("powermetrics_raw") or "N/A", 900),  # 逐行註解：顯示 powermetrics smc raw 或 sudo 失敗訊息。
        "",  # 逐行註解：空行。
        f"Final values: CPU={format_percent(cpu.get('total'))}, RAM={format_percent(ram.get('percent'))}, GPU estimate={format_percent(gpu.get('total'))}, TEMP={format_temperature(max_available_temperature(temp))}, FAN={first_fan_rpm_text(fans)}",  # 逐行註解：顯示主畫面最終值。
    ]  # 逐行註解：結束 debug lines。
    body = make_code_block("\n".join(lines)[:3900], "txt")  # 逐行註解：避免 Embed description 超過限制。
    return discord.Embed(title="Debug State", description=body, color=0x8B949E)  # 逐行註解：回傳 debug embed。


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
        "raw": {  # 逐行註解：保存 /debugstate 要看的原始資料。
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
        if not is_allowed_discord_user(interaction.user):  # 逐行註解：再次檢查白名單，避免 Modal 被非預期方式送出。
            await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限就只回覆執行者。
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


class DebugStatePasswordModal(discord.ui.Modal, title="查看 State Debug"):  # 逐行註解：定義 /debugstate 專用密碼視窗，避免系統 raw data 對所有人公開。
    password = discord.ui.TextInput(  # 逐行註解：建立密碼輸入欄位。
        label="請輸入 debug state 密碼",  # 逐行註解：設定 Modal 欄位標題。
        placeholder="請輸入 Mac 密碼",  # 逐行註解：提示使用同一套敏感指令密碼。
        required=True,  # 逐行註解：密碼欄位必填。
        max_length=200,  # 逐行註解：限制密碼長度。
    )  # 逐行註解：結束 TextInput 設定。

    async def on_submit(self, interaction: discord.Interaction):  # 逐行註解：定義使用者送出 Modal 後要執行的流程。
        if not is_allowed_discord_user(interaction.user):  # 逐行註解：再次檢查白名單。
            await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限就拒絕。
            return  # 逐行註解：停止流程。
        if not DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：如果 .env 沒設定敏感指令密碼，就拒絕查詢。
            await interaction.response.send_message("尚未設定 DISCORD_BOT_QUIT_PASSWORD，無法使用 /debugstate。", ephemeral=True)  # 逐行註解：提醒設定密碼。
            return  # 逐行註解：停止流程。
        if self.password.value.strip() != DISCORD_BOT_QUIT_PASSWORD:  # 逐行註解：比對 Modal 密碼。
            await interaction.response.send_message("密碼錯誤，無法查看 debug state。", ephemeral=True)  # 逐行註解：密碼錯誤時只回覆執行者。
            return  # 逐行註解：停止流程。
        author_name = (getattr(interaction.user, "global_name", None) or getattr(interaction.user, "display_name", None) or interaction.user.name or "").strip()  # 逐行註解：取得使用者顯示名稱。
        author_account = str(interaction.user).strip()  # 逐行註解：取得 Discord 帳號字串。
        print(  # 逐行註解：後台記錄誰使用了 debugstate，但不印密碼。
            "\n".join(  # 逐行註解：組合多行後台紀錄。
                [  # 逐行註解：開始 debugstate 後台紀錄。
                    "——————————————————",  # 逐行註解：分隔線。
                    f"使用者名稱：{author_name}",  # 逐行註解：顯示使用者名稱。
                    f"使用者帳號：{author_account}",  # 逐行註解：顯示使用者帳號。
                    f"使用者ID：{interaction.user.id}",  # 逐行註解：顯示 Discord ID。
                    "使用者詢問：/debugstate",  # 逐行註解：顯示指令。
                    "工具：debugstate",  # 逐行註解：顯示工具名稱。
                    "狀態：密碼驗證通過，輸出 state raw/debug 資料",  # 逐行註解：顯示狀態。
                    "——————————————————",  # 逐行註解：分隔線。
                    "",  # 逐行註解：空行。
                ]  # 逐行註解：結束後台紀錄。
            )  # 逐行註解：結束 join。
        )  # 逐行註解：結束 print。
        await interaction.response.defer(ephemeral=True)  # 逐行註解：先 defer，避免資料收集超過 Discord 時限。
        stats = await asyncio.to_thread(collect_computer_stats)  # 逐行註解：到 thread 裡執行 top/powermetrics/mactop 等可能阻塞的查詢。
        await interaction.followup.send(embed=build_debug_state_embed(stats), ephemeral=True)  # 逐行註解：把 debug embed 只送給執行者。


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
        if not is_allowed_discord_user(interaction.user):  # 逐行註解：再次檢查白名單。
            await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限就只回覆執行者。
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
        if not is_allowed_discord_user(interaction.user):  # 逐行註解：再次檢查白名單。
            await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有權限就只回覆執行者。
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
    if not is_allowed_discord_user(interaction.user):  # 逐行註解：先用既有白名單機制檢查使用者。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有白名單權限就回覆沒有權限。
        return  # 逐行註解：停止指令。
    await interaction.response.send_message("是否顯示 Apple 標誌？", view=StateAppleChoiceView(interaction.user.id), ephemeral=True)  # 逐行註解：先讓使用者選是或否，選完才跳密碼視窗。


@tree.command(name="debugstate", description="查看 /state 的原始資料來源")  # 逐行註解：新增 /debugstate slash command，用來檢查 /state 數值來源。
async def debugstate(interaction: discord.Interaction):  # 逐行註解：定義 /debugstate 指令。
    """輸入 /debugstate，先輸入密碼，再顯示 top、powermetrics、psutil、mactop 的 raw/parsed 資料。"""  # 逐行註解：說明 debugstate 用途。
    if not is_allowed_discord_user(interaction.user):  # 逐行註解：先用既有白名單機制檢查使用者。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有白名單權限就回覆沒有權限。
        return  # 逐行註解：停止指令。
    await interaction.response.send_modal(DebugStatePasswordModal())  # 逐行註解：用 Modal 輸入密碼，避免密碼出現在聊天記錄。


@tree.command(name="web_search", description="Search the web and answer with Ollama")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
@discord.app_commands.choices(  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
    model=[  # 逐行註解：開始建立一個跨多行的列表資料。
        discord.app_commands.Choice(name="qwen2.5-coder:1.5b_chat (default text)", value="qwen2.5-coder:1.5b_chat"),  # 逐行註解：這行是跨行資料或參數的一個項目。
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

    if not is_allowed_discord_user(interaction.user):  # 逐行註解：/web_search 也走同一個白名單函式，支援逗點多位使用者。
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

    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
        started = time.monotonic()  # 逐行註解：設定 started 這個變數，供後面的流程使用。
        # 建立一則可以反覆 edit 的進度訊息，後面每個階段都更新同一則。
        progress_message = await interaction.followup.send(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
            "/web_search 進度\n1. 正在搜尋網頁…",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
            ephemeral=private_reply,  # 逐行註解：設定 ephemeral 這個變數，供後面的流程使用。
            wait=True,  # 逐行註解：設定 wait 這個變數，供後面的流程使用。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。

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
        page_reads = await fetch_web_pages(fetch_candidates, limit=5, min_attempts=3, min_successful=1)  # 逐行註解：設定 page_reads 這個變數，供後面的流程使用。
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
        # 來源連結由程式端強制附加，不只依賴模型自己列來源，避免 Discord 回答沒有網址。
        source_links = format_web_search_source_links(page_reads, fetch_candidates)  # 逐行註解：設定 source_links 這個變數，供後面的流程使用。
        ollama_reply = append_source_links_to_reply(ollama_reply, source_links)  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。
        # 這裡故意存進共享記憶，不存進單一模型記憶，這樣使用者換模型後仍能問「剛剛查到什麼」。
        web_search_memory_reply = f"這是上一筆 /web_search 查到並回答過的內容，後續使用者說「剛剛查到的」或「統整一下」時要接續這筆資料。\n\n{ollama_reply}"  # 逐行註解：把 web_search 回答包成更明確的記憶文字，讓後續聊天模型知道這是剛剛查到的資料。
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
                    f"AI回覆：{ollama_reply}",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    f"思考時間：{thinking_sec:.2f}秒",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                    sep,  # 逐行註解：這行是跨行資料或參數的一個項目。
                    "",  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
                ]  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
            )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
    except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
        error_message = f"（發生錯誤：{type(e).__name__}: {str(e)[:300]}）"  # 逐行註解：設定 error_message 這個變數，供後面的流程使用。
        if progress_message is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            await update_web_search_progress(progress_message, error_message)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
            await interaction.followup.send(error_message, ephemeral=private_reply)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    if not ollama_reply:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        ollama_reply = "（我沒有產生任何回覆）"  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。

    chunks = textwrap.wrap(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
        ollama_reply,  # 逐行註解：這行是跨行資料或參數的一個項目。
        width=1800,  # 逐行註解：設定 width 這個變數，供後面的流程使用。
        break_long_words=False,  # 逐行註解：提前跳出目前這個迴圈。
        replace_whitespace=False,  # 逐行註解：設定 replace_whitespace 這個變數，供後面的流程使用。
    ) or [ollama_reply[:1800]]  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

    await send_followup_chunks_with_temporary_thinking(  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        interaction,  # 逐行註解：這行是跨行資料或參數的一個項目。
        chunks[:3],  # 逐行註解：這行是跨行資料或參數的一個項目。
        ephemeral=private_reply,  # 逐行註解：設定 ephemeral 這個變數，供後面的流程使用。
        thinking_text=thinking_process,  # 逐行註解：設定 thinking_text 這個變數，供後面的流程使用。
        first_message=progress_message,  # 逐行註解：設定 first_message 這個變數，供後面的流程使用。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。


@tree.command(name="run", description="進入終端模式執行指令")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def run_terminal(interaction: discord.Interaction):  # 逐行註解：定義非同步函式 run_terminal，可以搭配 await 處理 Discord 或網路等待。
    """輸入 /run，先跳出密碼視窗；密碼正確後進入終端模式，可輸入指令執行。"""  # 逐行註解：說明這個指令的用途。
    if not is_allowed_discord_user(interaction.user):  # 逐行註解：先用既有白名單機制檢查使用者。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有白名單權限就回覆沒有權限。
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
    if not is_allowed_discord_user(interaction.user):  # 逐行註解：先用既有白名單機制檢查使用者。
        await interaction.response.send_message(NO_PERMISSION_MESSAGE, ephemeral=True)  # 逐行註解：沒有白名單權限就回覆沒有權限。
        return  # 逐行註解：停止指令。
    if interaction.user.id in agent_sessions:  # 逐行註解：如果使用者已經在 Agent mode，就把這次 /agent 當成退出。
        del agent_sessions[interaction.user.id]  # 逐行註解：移除 Agent session。
        await interaction.response.send_message("已退出 agent mode", ephemeral=True)  # 逐行註解：提示已退出。
        return  # 逐行註解：停止指令。
    await interaction.response.send_modal(AgentPasswordModal())  # 逐行註解：進入 Agent mode 前先跳出密碼視窗，流程和 /run 一樣。


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
   例如 DC_BOT_TOKEN、ALLOWED_DISCORD_USER_ID、DISCORD_BOT_QUIT_PASSWORD 都是透過 os.getenv 讀出來。

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

1. 白名單和通知名單是兩件事
   ALLOWED_CHAT_USER、ALLOWED_DISCORD_USER_ID、ALLOWED_DISCORD_USER_IDS 是用來判斷誰可以使用 bot。
   STARTUP_DM_USER_ID、STARTUP_DM_USER_IDS 是用來決定 bot 上線或下線時要主動私訊誰。
   如果只把 Ray_Shen 寫進 ALLOWED_CHAT_USER，Ray 可以使用 bot，但不代表他會收到上線、下線私訊。
   要讓多人收到上線、下線通知，.env 要寫 STARTUP_DM_USER_IDS=數字ID1,數字ID2。
   這裡必須填 Discord 數字使用者 ID，不能填顯示名稱或帳號名稱。

2. 上線和下線通知流程
   send_startup_dm 會讀 STARTUP_DM_USER_IDS，逐一 fetch_user，然後私訊「我上線嘍，可以開始為您服務了！」。
   send_shutdown_dm 會讀同一份 STARTUP_DM_USER_IDS，逐一 fetch_user，然後私訊「我先下線了，掰掰！」。
   startup_dm_sent 和 shutdown_dm_sent 是防重複旗標，用來避免 Discord 重連或多個關閉入口造成重複通知。
   如果某一個 ID 填錯或不能私訊，程式會在後台印出那個 ID 的錯誤，但不會讓整個 bot 崩潰。

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
