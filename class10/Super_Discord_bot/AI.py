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

#######################初始化#######################
load_dotenv() # 讀取.env檔案Ｍ讓程式可以拿到DC_BOT_TOKEN這類資料

# 只允許特定人聊天：
# 注意：Discord Bot 端拿不到使用者 email，所以「seanchen810@gmail.com」只能當作
# 你的 Discord 帳號名稱/顯示名稱來比對；最穩定的是改用 user id（ALLOWED_DISCORD_USER_ID）。
ALLOWED_CHAT_USER = os.getenv("ALLOWED_CHAT_USER","seanchen810@gmail.com").strip()  # 逐行註解：設定 ALLOWED_CHAT_USER 這個變數，供後面的流程使用。
ALLOWED_DISCORD_USER_ID = os.getenv("ALLOWED_DISCORD_USER_ID", "").strip()  # 逐行註解：設定 ALLOWED_DISCORD_USER_ID 這個變數，供後面的流程使用。
STARTUP_DM_USER_ID = os.getenv("STARTUP_DM_USER_ID", ALLOWED_DISCORD_USER_ID or "1390880884554600559").strip()  # 逐行註解：設定 STARTUP_DM_USER_ID 這個變數，供後面的流程使用。
DISCORD_BOT_QUIT_PASSWORD = os.getenv("DISCORD_BOT_QUIT_PASSWORD", "").strip()  # 逐行註解：設定 DISCORD_BOT_QUIT_PASSWORD 這個變數，供後面的流程使用。
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
NO_THINKING_MODELS = {"gemma4_Instant", "gemma4_happy", "gemma4_angry", "gemma4_sad"}  # 逐行註解：設定 NO_THINKING_MODELS 這個變數，供後面的流程使用。
dm_user_model: dict[int, str] = {}  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。

# 每個使用者、每個模型各自保存對話記憶。
# 送進 Ollama 時不限制固定輪次，而是塞到接近 max token 預算為止。
# 這裡用字元數粗估 token；如果想調整，可以在 .env 設 CONVERSATION_MEMORY_MAX_CHARS。
CONVERSATION_MEMORY_MAX_CHARS = int(os.getenv("CONVERSATION_MEMORY_MAX_CHARS", "12000"))  # 逐行註解：設定 CONVERSATION_MEMORY_MAX_CHARS 這個變數，供後面的流程使用。
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
    if ALLOWED_DISCORD_USER_ID:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return str(user.id) == ALLOWED_DISCORD_USER_ID  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    author_candidates = {  # 逐行註解：開始建立一個跨多行的字典或集合資料。
        (user.name or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
        (getattr(user, "global_name", None) or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
        (getattr(user, "display_name", None) or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
        str(user).strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
    }  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
    return ALLOWED_CHAT_USER in author_candidates  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


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


def format_temporary_thinking_message(thinking_text: str, final_preview: str) -> str:  # 逐行註解：定義函式 format_temporary_thinking_message，把一段會重複使用的流程包起來。
    """把 thinking process 包成 Discord 訊息，5 秒後會被編輯掉。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    thinking_text = (thinking_text or "").strip().replace("```", "'''")  # 逐行註解：設定 thinking_text 這個變數，供後面的流程使用。
    final_preview = (final_preview or "").strip()  # 逐行註解：設定 final_preview 這個變數，供後面的流程使用。
    if len(thinking_text) > 900:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        thinking_text = thinking_text[:900].rstrip() + "\n（thinking process 太長，暫時只顯示前面）"  # 逐行註解：設定 thinking_text 這個變數，供後面的流程使用。

    prefix = f"thinking process：\n```text\n{thinking_text}\n```\n"  # 逐行註解：設定 prefix 這個變數，供後面的流程使用。
    remaining = 1900 - len(prefix)  # 逐行註解：設定 remaining 這個變數，供後面的流程使用。
    if remaining <= 0:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return prefix[:1900]  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    if len(final_preview) > remaining:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        final_preview = final_preview[:remaining].rstrip() + "…"  # 逐行註解：設定 final_preview 這個變數，供後面的流程使用。
    return prefix + final_preview  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。


async def send_chunks_with_temporary_thinking(channel: discord.abc.Messageable, chunks: list[str], thinking_text: str = ""):  # 逐行註解：定義非同步函式 send_chunks_with_temporary_thinking，可以搭配 await 處理 Discord 或網路等待。
    """一般頻道/DM：先顯示 thinking 5 秒，再編輯成正式回答。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if not chunks:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    if thinking_text.strip():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        msg = await channel.send(format_temporary_thinking_message(thinking_text, chunks[0]))  # 逐行註解：設定 msg 這個變數，供後面的流程使用。
        await asyncio.sleep(5)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        await msg.edit(content=chunks[0])  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        for chunk in chunks[1:]:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
            await channel.send(chunk)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    for chunk in chunks:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
        await channel.send(chunk)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。


async def send_followup_chunks_with_temporary_thinking(  # 逐行註解：定義非同步函式 send_followup_chunks_with_temporary_thinking，可以搭配 await 處理 Discord 或網路等待。
    interaction: discord.Interaction,  # 逐行註解：這行是跨行資料或參數的一個項目。
    chunks: list[str],  # 逐行註解：這行是跨行資料或參數的一個項目。
    *,  # 逐行註解：這行是跨行資料或參數的一個項目。
    ephemeral: bool,  # 逐行註解：這行是跨行資料或參數的一個項目。
    thinking_text: str = "",  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
    first_message=None,  # 逐行註解：設定 first_message 這個變數，供後面的流程使用。
):  # 逐行註解：這行開啟一個程式區塊，下面縮排內容會一起執行。
    """Slash 指令 followup：先顯示 thinking 5 秒，再編輯成正式回答。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if not chunks:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    if thinking_text.strip():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        # first_message 是 /web_search 的進度訊息；有傳進來時，就把同一則訊息改成暫時 thinking。
        if first_message is None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            msg = await interaction.followup.send(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
                format_temporary_thinking_message(thinking_text, chunks[0]),  # 逐行註解：這行是跨行資料或參數的一個項目。
                ephemeral=ephemeral,  # 逐行註解：設定 ephemeral 這個變數，供後面的流程使用。
                wait=True,  # 逐行註解：設定 wait 這個變數，供後面的流程使用。
            )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
            msg = first_message  # 逐行註解：設定 msg 這個變數，供後面的流程使用。
            await msg.edit(content=format_temporary_thinking_message(thinking_text, chunks[0]))  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        await asyncio.sleep(5)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        await msg.edit(content=chunks[0])  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        for chunk in chunks[1:]:  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
            await interaction.followup.send(chunk, ephemeral=ephemeral)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    # 沒有 thinking process 時，直接把進度訊息改成正式回答第一段，避免多洗一則訊息。
    if first_message is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await first_message.edit(content=chunks[0])  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
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
    """把對話記憶整理進 prompt；不限制輪次，只塞到 max token 預算附近。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    history = get_conversation_memory(user_id, model)  # 逐行註解：設定 history 這個變數，供後面的流程使用。
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
    """保存使用者訊息與 AI 回覆；每個模型分開記，不用固定輪次裁切。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    user_text = (user_text or "").strip()  # 逐行註解：設定 user_text 這個變數，供後面的流程使用。
    assistant_text = (assistant_text or "").strip()  # 逐行註解：設定 assistant_text 這個變數，供後面的流程使用。
    if not user_text and not assistant_text:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    key = (user_id, model)  # 逐行註解：設定 key 這個變數，供後面的流程使用。
    history = conversation_memory.setdefault(key, [])  # 逐行註解：設定 history 這個變數，供後面的流程使用。
    if user_text:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        history.append({"role": "user", "content": user_text[:1200]})  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    if assistant_text:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        history.append({"role": "assistant", "content": assistant_text[:1200]})  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。


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
    global startup_dm_sent  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    if STARTUP_DM_USER_ID and not startup_dm_sent:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            user = await bot.fetch_user(int(STARTUP_DM_USER_ID))  # 逐行註解：設定 user 這個變數，供後面的流程使用。
            await user.send("我上線嘍，可以開始為您服務了！")  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            startup_dm_sent = True  # 逐行註解：設定 startup_dm_sent 這個變數，供後面的流程使用。
        except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
            print(f"上線私訊失敗：{type(e).__name__}: {e}")  # 逐行註解：把資訊印到終端機後台，方便觀察 bot 執行狀態。


async def send_shutdown_dm():  # 逐行註解：定義非同步函式 send_shutdown_dm，可以搭配 await 處理 Discord 或網路等待。
    global shutdown_dm_sent  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
    if STARTUP_DM_USER_ID and not shutdown_dm_sent:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
            user = await bot.fetch_user(int(STARTUP_DM_USER_ID))  # 逐行註解：設定 user 這個變數，供後面的流程使用。
            await user.send("我先下線了，掰掰！")  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            shutdown_dm_sent = True  # 逐行註解：設定 shutdown_dm_sent 這個變數，供後面的流程使用。
        except Exception as e:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
            print(f"下線私訊失敗：{type(e).__name__}: {e}")  # 逐行註解：把資訊印到終端機後台，方便觀察 bot 執行狀態。


@bot.event  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def on_message(message):  # 逐行註解：定義非同步函式 on_message，可以搭配 await 處理 Discord 或網路等待。
    # messafe 就是一則剛剛出現在頻道的訊息
    if message.author == bot.user: # 如果這則訊息的作者是機器人自己，就不理他（避免無限循環）
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    # 只回覆特定人（Discord 無法用 email 驗證，只能比對 name/display_name 或 user id）
    if ALLOWED_DISCORD_USER_ID:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        if str(message.author.id) != ALLOWED_DISCORD_USER_ID:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
        author_candidates = {  # 逐行註解：開始建立一個跨多行的字典或集合資料。
            (message.author.name or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
            (getattr(message.author, "global_name", None) or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
            (getattr(message.author, "display_name", None) or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
            str(message.author).strip(),  # name#discriminator（舊版）或 name（新版）
        }  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        if ALLOWED_CHAT_USER not in author_candidates:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

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
                        await thinking_msg.edit(content=frames[i % len(frames)])  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                except Exception:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                    pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。
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
            except Exception:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。
            if thinking_msg is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                    await thinking_msg.delete()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                except Exception:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                    pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。

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
                            try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                                await progress_msg.edit(content=f"{last_percent}%\n```{shown}```")  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                            except Exception:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                                pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。
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
                    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                        await progress_msg.edit(content="100%\n完成，正在傳送圖片…")  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                    except Exception:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                        pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。
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
                    except Exception:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                        pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。
                if progress_task is not None and not progress_task.done():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    progress_task.cancel()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                if percent_task is not None and not percent_task.done():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    percent_task.cancel()  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                if progress_msg is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                        await progress_msg.delete()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
                    except Exception:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                        pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。
                if img_path is not None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
                        img_path = img_path.resolve()  # 逐行註解：設定 img_path 這個變數，供後面的流程使用。
                        if IMAGE_DIR in img_path.parents and img_path.is_file():  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                            img_path.unlink(missing_ok=True)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
                    except Exception:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
                        pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

        # 文字模型也支援「圖片 + 文字」：使用者傳圖片時，讓 gemma4 系列模型分析
        image_attachment: discord.Attachment | None = None  # 逐行註解：把右邊算出的值存到左邊的變數或欄位。
        for att in (message.attachments or []):  # 逐行註解：用迴圈逐一處理清單、字典或其他可迭代資料。
            # 只抓第一張圖片
            if (att.content_type or "").startswith("image/") or (att.filename or "").lower().endswith((".png", ".jpg", ".jpeg", ".webp")):  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
                image_attachment = att  # 逐行註解：設定 image_attachment 這個變數，供後面的流程使用。
                break  # 逐行註解：提前跳出目前這個迴圈。

        stop_thinking = await _start_thinking_effect(message.channel)  # 逐行註解：設定 stop_thinking 這個變數，供後面的流程使用。
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
            await stop_thinking()  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。

        # Discord 單則訊息上限約 2000 字；保守切段
        if not ollama_reply:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            ollama_reply = "（我沒有產生任何回覆）"  # 逐行註解：設定 ollama_reply 這個變數，供後面的流程使用。

        chunks = textwrap.wrap(  # 逐行註解：開始一個跨多行的函式呼叫，下面幾行會放參數。
            ollama_reply,  # 逐行註解：這行是跨行資料或參數的一個項目。
            width=1800,  # 逐行註解：設定 width 這個變數，供後面的流程使用。
            break_long_words=False,  # 逐行註解：提前跳出目前這個迴圈。
            replace_whitespace=False,  # 逐行註解：設定 replace_whitespace 這個變數，供後面的流程使用。
        ) or [ollama_reply[:1800]]  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。

        await send_chunks_with_temporary_thinking(message.channel, chunks[:3], thinking_process)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
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
        placeholder="請輸入 .env 裡的 DISCORD_BOT_QUIT_PASSWORD",  # 逐行註解：設定 placeholder 這個變數，供後面的流程使用。
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
    await interaction.response.send_message("Hey!") # 回覆這個指令，內容是 Hello, World!
    #!只會傳給使用者

@tree.command(name="dm", description="Send me a DM (for testing DM chat)")  # 逐行註解：這行是裝飾器，用來替下一個函式或類別加上 Discord/介面設定。
async def dm(interaction: discord.Interaction, text: str):  # 逐行註解：定義非同步函式 dm，可以搭配 await 處理 Discord 或網路等待。
    """輸入 /dm <文字>，機器人會私訊你同樣的文字（用來測試 DM 功能）"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
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

    # 只回覆特定人（同 on_message）
    if ALLOWED_DISCORD_USER_ID:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        if str(interaction.user.id) != ALLOWED_DISCORD_USER_ID:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            await interaction.response.send_message("（你沒有權限使用這個機器人）", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
        u = interaction.user  # 逐行註解：設定 u 這個變數，供後面的流程使用。
        author_candidates = {  # 逐行註解：開始建立一個跨多行的字典或集合資料。
            (u.name or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
            (getattr(u, "global_name", None) or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
            (getattr(u, "display_name", None) or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
            str(u).strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
        }  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        if ALLOWED_CHAT_USER not in author_candidates:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            await interaction.response.send_message("（你沒有權限使用這個機器人）", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    q = (question or "").strip()  # 逐行註解：設定 q 這個變數，供後面的流程使用。
    if not q:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        await interaction.response.send_message("請輸入問題", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

    await interaction.response.defer(ephemeral=True, thinking=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。

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
        await interaction.followup.send(f"（發生錯誤：{type(e).__name__}: {str(e)[:300]}）", ephemeral=True)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
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
        ephemeral=True,  # 逐行註解：設定 ephemeral 這個變數，供後面的流程使用。
        thinking_text=thinking_process,  # 逐行註解：設定 thinking_text 這個變數，供後面的流程使用。
    )  # 逐行註解：結束上一個跨行函式呼叫或資料結構。


async def update_web_search_progress(progress_message, content: str):  # 逐行註解：定義非同步函式 update_web_search_progress，可以搭配 await 處理 Discord 或網路等待。
    """更新 /web_search 的同一則進度訊息；失敗時不要中斷搜尋流程。"""  # 逐行註解：這行是文字內容，通常用來組 prompt、訊息或後台紀錄。
    if progress_message is None:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    try:  # 逐行註解：開始嘗試執行可能會失敗的程式碼，方便後面捕捉錯誤。
        await progress_message.edit(content=content[:1900])  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
    except Exception:  # 逐行註解：捕捉 try 區塊發生的錯誤，避免 bot 直接崩潰。
        pass  # 逐行註解：這裡暫時不做事，只是保留語法需要的位置。


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

    if ALLOWED_DISCORD_USER_ID:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
        if str(interaction.user.id) != ALLOWED_DISCORD_USER_ID:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            await interaction.response.send_message("（你沒有權限使用這個機器人）", ephemeral=private_reply)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。
    else:  # 逐行註解：前面條件都不成立時，執行這個備用分支。
        u = interaction.user  # 逐行註解：設定 u 這個變數，供後面的流程使用。
        author_candidates = {  # 逐行註解：開始建立一個跨多行的字典或集合資料。
            (u.name or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
            (getattr(u, "global_name", None) or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
            (getattr(u, "display_name", None) or "").strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
            str(u).strip(),  # 逐行註解：這行是跨行資料或參數的一個項目。
        }  # 逐行註解：結束上一個跨行函式呼叫或資料結構。
        if ALLOWED_CHAT_USER not in author_candidates:  # 逐行註解：判斷這個條件是否成立，成立才執行下面縮排的程式。
            await interaction.response.send_message("（你沒有權限使用這個機器人）", ephemeral=private_reply)  # 逐行註解：等待非同步工作完成，期間不阻塞整個 Discord bot。
            return  # 逐行註解：把結果傳回呼叫這個函式的地方，並結束目前函式。

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
        remember_conversation(interaction.user.id, selected_model, f"/web_search {q}", ollama_reply)  # 逐行註解：執行這一行，推進 Discord bot、Ollama 或網頁搜尋流程。
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
這段是給你讀程式時看的筆記，不會被 Python 當成會執行的程式邏輯。
因為它放在檔案最底下，而且沒有被變數接住，所以只是一段多行文字註解。

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
   我用它手動改 import 註解、/web_search 註解、來源連結註解，以及這段多行工具筆記。
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
"""
