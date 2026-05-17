#######################模組#######################
# asyncio 是 Python 內建的非同步工具。
# 可以把它想成「任務小管家」： 如果某件事需要等網路回應，他可以先去安排別的事，不會讓整個城市傻傻卡住
import asyncio
import discord # pip install -U discord.py；這個套件負責和Discord 溝通
import os # 用來讀取環境變數
from dotenv import load_dotenv # pip install python-dotenv；這個套件負責讀取 .env 檔案
import textwrap # 用來把太長的 AI 回覆切成多段，避免超過 Discord 單則訊息上限
import json # 用來和 Ollama HTTP API 交換 JSON 資料
import base64 # 圖片模型 / 圖片分析會用 base64 傳圖片資料
import uuid # 產生不重複的圖片檔名，避免不同圖片互相覆蓋
from pathlib import Path # 比字串路徑更安全地處理檔案位置
from urllib import request as urlrequest # Python 內建的網路請求工具，不需要額外安裝 requests
from urllib import parse as urlparse # 用來處理網址編碼與 DuckDuckGo 轉址參數
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser # 用來解析 DuckDuckGo 搜尋結果 HTML
import time # 用來計算 AI 思考/搜尋花了幾秒
import re # 用正規表達式清掉 Ollama 的 thinking process

#######################初始化#######################
load_dotenv() # 讀取.env檔案Ｍ讓程式可以拿到DC_BOT_TOKEN這類資料

# 只允許特定人聊天：
# 注意：Discord Bot 端拿不到使用者 email，所以「seanchen810@gmail.com」只能當作
# 你的 Discord 帳號名稱/顯示名稱來比對；最穩定的是改用 user id（ALLOWED_DISCORD_USER_ID）。
ALLOWED_CHAT_USER = os.getenv("ALLOWED_CHAT_USER","seanchen810@gmail.com").strip()
ALLOWED_DISCORD_USER_ID = os.getenv("ALLOWED_DISCORD_USER_ID", "").strip()
STARTUP_DM_USER_ID = os.getenv("STARTUP_DM_USER_ID", ALLOWED_DISCORD_USER_ID or "1390880884554600559").strip()
startup_dm_sent = False

# 預設文字聊天模型：用 qwen2.5-coder:1.5b 套 gemma4 的繁中聊天 Modelfile。
DEFAULT_CHAT_MODEL = "qwen2.5-coder:1.5b_chat"

# DM 模式下，每個使用者可以選擇目前要用的模型
DM_MODELS = (DEFAULT_CHAT_MODEL, "gemma4", "ollama_sad", "ollama_angry", "ollama_happy", "x/flux2-klein:latest")
dm_user_model: dict[int, str] = {}

# 每個使用者、每個模型各自保存對話記憶。
# 送進 Ollama 時不限制固定輪次，而是塞到接近 max token 預算為止。
# 這裡用字元數粗估 token；如果想調整，可以在 .env 設 CONVERSATION_MEMORY_MAX_CHARS。
CONVERSATION_MEMORY_MAX_CHARS = int(os.getenv("CONVERSATION_MEMORY_MAX_CHARS", "12000"))
conversation_memory: dict[tuple[int, str], list[dict[str, str]]] = {}

# 圖片只存到這個資料夾，送出後會刪掉（避免誤刪其他地方的檔案）
IMAGE_DIR = (Path.home() / "discord_bot_generated_images").resolve()
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# event loop 可以想成「非同步任務的轉盤」：
# 哪個工作先做、哪個工作要等一下，會由這個轉盤幫忙安排。
# Python 3.10+ 在主程式裡不一定會先自動準備好這個轉盤，
# 所以我們自己先建立一個給Discord使用。
asyncio.set_event_loop(asyncio.new_event_loop())
# 建立一個新的 event loop，給Discord使用
# Intent 可以想成「先跟Discord勾選：我想收到哪些類型的通知」
# 如果沒有先打開某個 Intent，Discord就不會把那種資酪送給機器人。
intents = discord.Intents.default()
intents.message_content = True # 允許機器人看到訊息真正的文字內容，這樣她才知道有人是不是輸入了Hello

bot = discord.Client(intents=intents) # 建立機器人本體，並把 intents 交給它
tree = discord.app_commands.CommandTree(bot) # 建立一個「指令樹」，讓我們可以在裡面登記指令

# Ollama 有時會把終端機控制碼或 thinking process 一起吐出來。
# 這三個 regex 是「輸出清理器」：使用者端與後台都會先經過它們過濾。
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
THINK_TAG_RE = re.compile(r"(?is)<think>.*?</think>")
THINKING_PROCESS_RE = re.compile(
    r"(?is)^\s*(?:thinking\.\.\.\s*)?(?:thinking process|thought process)\s*:.*?(?:\.\.\.done thinking\.|done thinking\.)\s*"
)
THINKING_INTRO_RE = re.compile(
    r"(?is)^\s*thinking\.\.\..*?(?:\.\.\.done thinking\.|done thinking\.)\s*"
)

def strip_thinking_process(text: str) -> str:
    """
    避免把 Ollama 的 thinking process（長長英文/推理過程）顯示在使用者/後台。
    常見格式是 <think>...</think>，這裡直接移除。
    """
    _, final_reply = split_thinking_process(text)
    return final_reply


def split_thinking_process(text: str) -> tuple[str, str]:
    """
    把 Ollama 回覆拆成「thinking process」和「正式回答」。
    使用者端會先暫時顯示 thinking，再自動編輯成正式回答。
    """
    t = (text or "").strip()
    if not t:
        return "", ""
    t = ANSI_ESCAPE_RE.sub("", t)
    thinking_parts: list[str] = []

    for pattern in (THINK_TAG_RE, THINKING_PROCESS_RE, THINKING_INTRO_RE):
        while True:
            match = pattern.search(t)
            if match is None:
                break
            thinking_parts.append(match.group(0).strip())
            t = (t[:match.start()] + t[match.end():]).strip()

    return "\n\n".join(thinking_parts).strip(), t.strip()


def format_temporary_thinking_message(thinking_text: str, final_preview: str) -> str:
    """把 thinking process 包成 Discord 訊息，5 秒後會被編輯掉。"""
    thinking_text = (thinking_text or "").strip().replace("```", "'''")
    final_preview = (final_preview or "").strip()
    if len(thinking_text) > 900:
        thinking_text = thinking_text[:900].rstrip() + "\n（thinking process 太長，暫時只顯示前面）"

    prefix = f"thinking process：\n```text\n{thinking_text}\n```\n"
    remaining = 1900 - len(prefix)
    if remaining <= 0:
        return prefix[:1900]
    if len(final_preview) > remaining:
        final_preview = final_preview[:remaining].rstrip() + "…"
    return prefix + final_preview


async def send_chunks_with_temporary_thinking(channel: discord.abc.Messageable, chunks: list[str], thinking_text: str = ""):
    """一般頻道/DM：先顯示 thinking 5 秒，再編輯成正式回答。"""
    if not chunks:
        return
    if thinking_text.strip():
        msg = await channel.send(format_temporary_thinking_message(thinking_text, chunks[0]))
        await asyncio.sleep(5)
        await msg.edit(content=chunks[0])
        for chunk in chunks[1:]:
            await channel.send(chunk)
        return

    for chunk in chunks:
        await channel.send(chunk)


async def send_followup_chunks_with_temporary_thinking(
    interaction: discord.Interaction,
    chunks: list[str],
    *,
    ephemeral: bool,
    thinking_text: str = "",
):
    """Slash 指令 followup：先顯示 thinking 5 秒，再編輯成正式回答。"""
    if not chunks:
        return
    if thinking_text.strip():
        msg = await interaction.followup.send(
            format_temporary_thinking_message(thinking_text, chunks[0]),
            ephemeral=ephemeral,
            wait=True,
        )
        await asyncio.sleep(5)
        await msg.edit(content=chunks[0])
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk, ephemeral=ephemeral)
        return

    for chunk in chunks:
        await interaction.followup.send(chunk, ephemeral=ephemeral)


SIMPLIFIED_TO_TRADITIONAL = str.maketrans({
    "么": "麼",
    "吗": "嗎",
    "为": "為",
    "这": "這",
    "个": "個",
    "后": "後",
    "里": "裡",
    "会": "會",
    "帮": "幫",
    "说": "說",
    "让": "讓",
    "请": "請",
    "问": "問",
    "题": "題",
    "应": "應",
    "对": "對",
    "时": "時",
    "间": "間",
    "现": "現",
    "发": "發",
    "过": "過",
    "还": "還",
    "没": "沒",
    "给": "給",
    "开": "開",
    "关": "關",
    "实": "實",
    "种": "種",
    "动": "動",
    "国": "國",
    "语": "語",
    "汉": "漢",
    "体": "體",
    "简": "簡",
    "繁": "繁",
    "软": "軟",
    "频": "頻",
    "讯": "訊",
    "资": "資",
    "与": "與",
    "内": "內",
    "写": "寫",
    "读": "讀",
    "条": "條",
    "将": "將",
    "来": "來",
    "优": "優",
    "习": "習",
    "义": "義",
    "云": "雲",
    "尽": "盡",
    "准": "準",
    "确": "確",
    "为": "為",
})


def force_common_traditional_chinese(text: str) -> str:
    """qwen 小模型偶爾會漏簡體字；這裡把常見簡體字轉回繁體。"""
    return (text or "").translate(SIMPLIFIED_TO_TRADITIONAL)


def get_conversation_memory(user_id: int, model: str) -> list[dict[str, str]]:
    """取出某個使用者在某個模型底下的最近對話記憶。"""
    return conversation_memory.get((user_id, model), [])


def format_conversation_memory(user_id: int, model: str) -> str:
    """把對話記憶整理進 prompt；不限制輪次，只塞到 max token 預算附近。"""
    history = get_conversation_memory(user_id, model)
    if not history:
        return "無"

    lines: list[str] = []
    used_chars = 0
    for item in reversed(history):
        role = "使用者" if item.get("role") == "user" else "AI"
        content = (item.get("content") or "").strip()
        if content:
            line = f"{role}：{content}"
            used_chars += len(line)
            if used_chars > CONVERSATION_MEMORY_MAX_CHARS:
                break
            lines.append(line)
    lines.reverse()
    return "\n".join(lines) if lines else "無"


def build_prompt_with_memory(user_id: int, model: str, user_text: str) -> str:
    """把 max token 預算內的對話記憶一起交給 Ollama，讓每個模型都能接續上下文。"""
    user_text = (user_text or "").strip()
    memory_context = format_conversation_memory(user_id, model)
    if memory_context == "無":
        return user_text

    return f"""
以下是你和這位使用者的對話記憶，已自動保留到接近 max token 預算為止。
請用它理解上下文、記住使用者剛剛要你做什麼，但不要逐字重複記憶內容。

對話記憶：
{memory_context}

使用者現在的新訊息：
{user_text}
""".strip()


def remember_conversation(user_id: int, model: str, user_text: str, assistant_text: str) -> None:
    """保存使用者訊息與 AI 回覆；每個模型分開記，不用固定輪次裁切。"""
    user_text = (user_text or "").strip()
    assistant_text = (assistant_text or "").strip()
    if not user_text and not assistant_text:
        return

    key = (user_id, model)
    history = conversation_memory.setdefault(key, [])
    if user_text:
        history.append({"role": "user", "content": user_text[:1200]})
    if assistant_text:
        history.append({"role": "assistant", "content": assistant_text[:1200]})


class DuckDuckGoResultParser(HTMLParser):
    """
    專門解析 DuckDuckGo HTML 搜尋結果的 parser。
    這裡不用 BeautifulSoup，是為了讓專案不需要額外安裝套件。
    """
    def __init__(self):
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._in_title = False
        self._in_snippet = False
        self._title_parts: list[str] = []
        self._snippet_parts: list[str] = []
        self._current_href = ""

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        # DuckDuckGo 的結果標題會放在 class="result__a" 的 <a> 裡。
        if tag == "a" and "result__a" in classes:
            self._in_title = True
            self._title_parts = []
            self._current_href = attr.get("href") or ""
        # 搜尋摘要會放在 result__snippet，之後會接到最後一筆結果上。
        elif "result__snippet" in classes:
            self._in_snippet = True
            self._snippet_parts = []

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        elif self._in_snippet:
            self._snippet_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._in_title:
            title = " ".join("".join(self._title_parts).split())
            url = normalize_duckduckgo_url(self._current_href)
            if title and url:
                self.results.append({"title": title, "url": url, "snippet": ""})
            self._in_title = False
        elif self._in_snippet:
            snippet = " ".join("".join(self._snippet_parts).split())
            if snippet and self.results:
                self.results[-1]["snippet"] = snippet
            self._in_snippet = False


class WebPageTextParser(HTMLParser):
    """把一般網頁 HTML 轉成純文字，給 Ollama 當成真正讀到的頁面內容。"""
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth:
            return
        cleaned = " ".join((data or "").split())
        if cleaned:
            self.parts.append(cleaned)

    def text(self, *, max_chars: int = 1800) -> str:
        return " ".join(self.parts)[:max_chars].strip()


def normalize_duckduckgo_url(raw_url: str) -> str:
    """
    DuckDuckGo 結果常常不是直接網址，而是 /l/?uddg=真正網址。
    這個函式把它還原成後台容易讀的原始網址。
    """
    raw_url = (raw_url or "").strip()
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url
    parsed = urlparse.urlparse(raw_url)
    qs = urlparse.parse_qs(parsed.query)
    if "uddg" in qs and qs["uddg"]:
        return qs["uddg"][0]
    return raw_url


def format_search_results_for_log(results: list[dict[str, str]]) -> str:
    """把搜尋結果整理成後台看的格式：標題、網址、摘要。"""
    if not results:
        return "無"
    return "\n".join(
        f"[{i}] 標題：{r['title']}\n網址：{r['url']}\n摘要：{r.get('snippet') or '（沒有摘要）'}"
        for i, r in enumerate(results, start=1)
    )


def format_search_urls_for_log(results: list[dict[str, str]]) -> str:
    """只列出 Ollama 參考到的網址，方便在後台快速檢查來源。"""
    if not results:
        return "無"
    return "\n".join(f"[{i}] {r['url']}" for i, r in enumerate(results, start=1))


def format_page_reads_for_log(pages: list[dict[str, str]]) -> str:
    if not pages:
        return "無"
    return "\n\n".join(
        f"[{i}] 網址：{p['url']}\n狀態：{p['status']}\n內容：{p.get('text') or '（沒有讀到可用文字）'}"
        for i, p in enumerate(pages, start=1)
    )


async def search_web_results(question: str, *, limit: int = 5) -> list[dict[str, str]]:
    """
    /web_search 會呼叫這裡：
    1. 把使用者問題送到 DuckDuckGo HTML 搜尋。
    2. 解析出前幾筆搜尋結果。
    3. 回傳給 Ollama 當作回答依據。
    """
    question = (question or "").strip()
    if not question:
        return []

    def _search() -> list[dict[str, str]]:
        url = "https://html.duckduckgo.com/html/?q=" + urlparse.quote(question)
        req = urlrequest.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            method="GET",
        )
        with urlrequest.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        parser = DuckDuckGoResultParser()
        parser.feed(html)
        return parser.results[:limit]

    # urllib 是同步阻塞工具，放到 thread 裡跑，才不會卡住 Discord bot。
    return await asyncio.to_thread(_search)


async def fetch_web_pages(results: list[dict[str, str]], *, limit: int = 3) -> list[dict[str, str]]:
    """實際打開搜尋結果網址，讀取網頁文字；讀不到時保留錯誤原因。"""
    selected = results[:limit]

    def _fetch_one(item: dict[str, str]) -> dict[str, str]:
        url = item["url"]
        try:
            req = urlrequest.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                method="GET",
            )
            with urlrequest.urlopen(req, timeout=12) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read(350_000)
            if "html" not in content_type.lower() and "text" not in content_type.lower():
                return {"url": url, "status": f"略過：不是文字網頁 ({content_type})", "text": ""}
            parser = WebPageTextParser()
            parser.feed(raw.decode("utf-8", errors="replace"))
            text = parser.text()
            if not text:
                return {"url": url, "status": "已打開，但沒有讀到可用文字", "text": ""}
            return {"url": url, "status": "已讀取", "text": text}
        except Exception as e:
            return {"url": url, "status": f"讀取失敗：{type(e).__name__}: {str(e)[:160]}", "text": ""}

    tasks = [asyncio.to_thread(_fetch_one, item) for item in selected]
    return await asyncio.gather(*tasks)


async def ask_ollama_text(
    model: str,
    prompt: str,
    *,
    timeout_s: int | None = None,
    include_thinking: bool = False,
) -> str | tuple[str, str]:
    """
    用本機 Ollama 文字模型回覆（CLI: `ollama run <model> ...`）。
    會自動移除 thinking process。
    """
    prompt = (prompt or "").strip()
    if not prompt:
        return ("", "") if include_thinking else ""

    # 用 subprocess 跑 `ollama run`，不用另外安裝 Ollama Python 套件。
    proc = await asyncio.create_subprocess_exec(
        "ollama",
        "run",
        model,
        prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        if timeout_s is None:
            stdout, stderr = await proc.communicate()
        else:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except TimeoutError:
        proc.kill()
        reply = "（Ollama 回覆逾時，稍後再試）"
        return (reply, "") if include_thinking else reply

    if proc.returncode != 0:
        err = (stderr or b"").decode("utf-8", errors="replace").strip()
        reply = f"（Ollama 執行失敗：{err[:400]}）"
        return (reply, "") if include_thinking else reply

    reply = (stdout or b"").decode("utf-8", errors="replace").strip()
    thinking_process, reply = split_thinking_process(reply)
    if model == DEFAULT_CHAT_MODEL:
        reply = force_common_traditional_chinese(reply)
    if include_thinking:
        return reply, thinking_process
    return reply


async def ask_ollama_vision(
    model: str,
    prompt: str,
    image_bytes: bytes,
    *,
    timeout_s: int | None = None,
    include_thinking: bool = False,
) -> str | tuple[str, str]:
    """
    用 Ollama HTTP API 走 vision（文字 + 圖片）推論。
    會自動移除 thinking process。
    """
    prompt = (prompt or "").strip() or "請分析這張圖片。"
    if not image_bytes:
        raise ValueError("empty image bytes")

    # Ollama vision API 要把圖片轉成 base64 字串後放進 images。
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "images": [base64.b64encode(image_bytes).decode("utf-8")],
    }
    req = urlrequest.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _do_request() -> dict:
        with urlrequest.urlopen(req, timeout=(timeout_s or 0) or None) as resp:
            raw = resp.read()
        return json.loads(raw.decode("utf-8", errors="replace"))

    try:
        data = await asyncio.to_thread(_do_request)
    except Exception as e:
        raise RuntimeError(f"ollama vision error: {type(e).__name__}: {e}") from e

    if not isinstance(data, dict):
        raise RuntimeError("invalid response from ollama")
    reply = (data.get("response") or "").strip()
    thinking_process, reply = split_thinking_process(reply)
    if include_thinking:
        return reply, thinking_process
    return reply


async def ask_ollama_image(prompt: str, progress_cb=None) -> Path:
    """
    用 Ollama 的 HTTP API 呼叫影像模型，回傳一張圖片路徑。
    圖片只會寫在 IMAGE_DIR，送出後會刪掉，避免堆在電腦上。
    """
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("empty prompt")

    # 圖片模型用 stream=True，才能一邊生成一邊更新 Discord 進度。
    payload = {
        "model": "x/flux2-klein:latest",
        "prompt": prompt,
        "stream": True,
    }
    req = urlrequest.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _do_stream_request() -> dict:
        last: dict | None = None
        collected_images: list[str] = []
        try:
            with urlrequest.urlopen(req, timeout=300) as resp:
                for raw_line in resp:
                    if not raw_line:
                        continue
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    # Ollama 串流每一行都是一個 JSON 片段；最後會包含圖片資料。
                    if isinstance(obj, dict):
                        last = obj
                        img_one = obj.get("image")
                        if isinstance(img_one, str) and img_one:
                            collected_images.append(img_one)
                        imgs = obj.get("images") or []
                        if isinstance(imgs, list):
                            for it in imgs:
                                if isinstance(it, str) and it:
                                    collected_images.append(it)
                    if progress_cb is not None and isinstance(obj, dict):
                        status = (obj.get("response") or "").strip()
                        status = strip_thinking_process(status)
                        if not status and obj.get("done") is True:
                            status = "done"
                        if status:
                            progress_cb(status)
                    if isinstance(obj, dict) and obj.get("done") is True:
                        break
        except (URLError, HTTPError) as e:
            raise RuntimeError(f"ollama http error: {e}") from e
        if not isinstance(last, dict):
            raise RuntimeError("no response from ollama")
        if collected_images:
            last = dict(last)
            last["images"] = collected_images
        return last

    data = await asyncio.to_thread(_do_stream_request)
    images: list[str] = []
    img_one = data.get("image")
    if isinstance(img_one, str) and img_one:
        images.append(img_one)
    imgs = data.get("images") or []
    if isinstance(imgs, list):
        images.extend([x for x in imgs if isinstance(x, str) and x])

    if not images:
        raise RuntimeError("no images returned from ollama")

    img_b64 = images[0]
    img_bytes = base64.b64decode(img_b64)

    out_path = (IMAGE_DIR / f"{uuid.uuid4().hex}.png").resolve()
    if IMAGE_DIR not in out_path.parents:
        raise RuntimeError("unsafe image path")
    out_path.write_bytes(img_bytes)
    return out_path
#######################事件#######################
"""
@bot.event 這種寫法叫做裝飾器，
可以把它寫成幫下面的函式貼上一張「事件處理員」標籤。
def 是一般函式，通常會照順序一路做完。
async def 是可以搭配 await 的函式；
遇到需要等一下的工作時，
他可以先暫停，等事情完後再回來繼續做。
"""
@bot.event
async def on_ready():
    global startup_dm_sent
    print(f"{bot.user}is ready and online\n＝＝＝＝＝＝＝＝＝＝＝後台：＝＝＝＝＝＝＝＝＝＝＝")
    if STARTUP_DM_USER_ID and not startup_dm_sent:
        try:
            user = await bot.fetch_user(int(STARTUP_DM_USER_ID))
            await user.send("我上線嘍，可以開始為您服務了！")
            startup_dm_sent = True
        except Exception as e:
            print(f"上線私訊失敗：{type(e).__name__}: {e}")
    # await：等這件事完成後再繼續往下
    # return：直接結束函式
    # tree.sync()：把slash 指令送去Discord登記
    await tree.sync() # 把我們在程式裡登記的指令，同步到 Discord 上，讓她知道我們有哪些指令可以用
@bot.event
async def on_message(message):
    # messafe 就是一則剛剛出現在頻道的訊息
    if message.author == bot.user: # 如果這則訊息的作者是機器人自己，就不理他（避免無限循環）
        return

    # 只回覆特定人（Discord 無法用 email 驗證，只能比對 name/display_name 或 user id）
    if ALLOWED_DISCORD_USER_ID:
        if str(message.author.id) != ALLOWED_DISCORD_USER_ID:
            return
    else:
        author_candidates = {
            (message.author.name or "").strip(),
            (getattr(message.author, "global_name", None) or "").strip(),
            (getattr(message.author, "display_name", None) or "").strip(),
            str(message.author).strip(),  # name#discriminator（舊版）或 name（新版）
        }
        if ALLOWED_CHAT_USER not in author_candidates:
            return

    user_text = (message.content or "").strip()

    # 伺服器頻道：禁止「你說話就回答」；只能用 /ask 觸發
    # 私訊(DM)：保留原本體驗，直接問直接答
    if message.guild is not None:
        return

    # 如果是 Discord 指令（例如 /hello），就不要當成一般聊天內容來回覆
    if user_text.startswith("/"):
        return

    if user_text.lower() == "hello": # 如果這則訊息的內容是 hello
        await message.channel.send("Hey!") # 就回 Hey!
        print("有人打招呼了！") # 在終端機印出「有人打招呼了！」，讓我們知道這件事發生了
        return

    def _author_label(m: discord.Message) -> str:
        a = m.author
        name = (getattr(a, "global_name", None) or getattr(a, "display_name", None) or a.name or "").strip()
        handle = str(a).strip()
        return f"{name} ({handle}) id={a.id}"

    def _is_dm(message: discord.Message) -> bool:
        return message.guild is None

    async def _start_thinking_effect(channel: discord.abc.Messageable):
        """
        文字模型等待時顯示「思考中...」動態效果。
        回覆完成後 stop() 會把這則等待訊息刪掉，避免頻道留下多餘訊息。
        """
        thinking_msg: discord.Message | None = await channel.send("思考中…")
        stop_event = asyncio.Event()

        async def _animator():
            frames = ("思考中", "思考中.", "思考中..", "思考中...")
            i = 0
            while not stop_event.is_set():
                try:
                    if thinking_msg is not None:
                        await thinking_msg.edit(content=frames[i % len(frames)])
                except Exception:
                    pass
                i += 1
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=0.8)
                except TimeoutError:
                    continue

        task = asyncio.create_task(_animator())

        async def stop():
            stop_event.set()
            try:
                await task
            except Exception:
                pass
            if thinking_msg is not None:
                try:
                    await thinking_msg.delete()
                except Exception:
                    pass

        return stop

    # 不是 hello 的話，就依照目前模型回覆（文字顯示思考中，圖片保留生成進度）
    try:
        if _is_dm(message):
            selected_model = dm_user_model.get(message.author.id, DEFAULT_CHAT_MODEL)
        else:
            selected_model = DEFAULT_CHAT_MODEL

        if _is_dm(message) and selected_model == "x/flux2-klein:latest":
            img_path: Path | None = None
            progress_msg: discord.Message | None = None
            progress_text = ""
            progress_queue: asyncio.Queue[str] | None = None
            progress_task: asyncio.Task | None = None
            percent_task: asyncio.Task | None = None
            try:
                started = time.monotonic()
                # 顯示生成進度（像終端機那樣一路更新）
                progress_msg = await message.channel.send("0%\n開始生成圖片…")

                loop = asyncio.get_running_loop()
                progress_queue = asyncio.Queue()
                start_ts = time.monotonic()
                done_flag = False

                def _progress_cb(s: str):
                    if not s:
                        return
                    # 這個 callback 會在 thread 內被呼叫，用 call_soon_threadsafe 回到 event loop
                    loop.call_soon_threadsafe(progress_queue.put_nowait, s)

                async def _progress_updater():
                    nonlocal progress_text
                    assert progress_queue is not None
                    while True:
                        s = await progress_queue.get()
                        if s == "__DONE__":
                            break
                        progress_text = (progress_text + "\n" + s).strip()
                        progress_text = "\n".join(progress_text.splitlines()[-15:])

                async def _percent_updater():
                    nonlocal progress_text, done_flag
                    last_percent = -1
                    while not done_flag:
                        elapsed = time.monotonic() - start_ts
                        if elapsed < 5:
                            percent = 0
                        elif elapsed < 15:
                            percent = 25
                        elif elapsed < 30:
                            percent = 50
                        elif elapsed < 60:
                            percent = 75
                        else:
                            percent = 75

                        if percent != last_percent and progress_msg is not None:
                            last_percent = percent
                            shown = progress_text.strip() or "生成中…"
                            if len(shown) > 1800:
                                shown = shown[-1800:]
                            try:
                                await progress_msg.edit(content=f"{last_percent}%\n```{shown}```")
                            except Exception:
                                pass
                        await asyncio.sleep(2)

                progress_task = asyncio.create_task(_progress_updater())
                percent_task = asyncio.create_task(_percent_updater())

                img_path = await ask_ollama_image(user_text, progress_cb=_progress_cb)
                if progress_queue is not None:
                    progress_queue.put_nowait("__DONE__")
                if progress_task is not None:
                    await progress_task
                done_flag = True
                if percent_task is not None:
                    await percent_task
                if progress_msg is not None:
                    try:
                        await progress_msg.edit(content="100%\n完成，正在傳送圖片…")
                    except Exception:
                        pass
                await message.channel.send(file=discord.File(str(img_path)))
                remember_conversation(message.author.id, selected_model, user_text, "已生成圖片")
                author_name = (getattr(message.author, "global_name", None) or getattr(message.author, "display_name", None) or message.author.name or "").strip()
                author_account = str(message.author).strip()
                print(
                    "\n".join(
                        [
                            "——————————————————",
                            f"使用者名稱：{author_name}",
                            f"使用者帳號：{author_account}",
                            f"使用者ID：{message.author.id}",
                            f"使用者詢問：{user_text}",
                            "工具：無",
                            f"使用者選的模型：{selected_model}",
                            "AI回覆：已生成圖片",
                            f"思考時間：{time.monotonic() - started:.2f}秒",
                            "——————————————————",
                            "",
                        ]
                    )
                )
            finally:
                done_flag = True
                if progress_queue is not None:
                    try:
                        progress_queue.put_nowait("__DONE__")
                    except Exception:
                        pass
                if progress_task is not None and not progress_task.done():
                    progress_task.cancel()
                if percent_task is not None and not percent_task.done():
                    percent_task.cancel()
                if progress_msg is not None:
                    try:
                        await progress_msg.delete()
                    except Exception:
                        pass
                if img_path is not None:
                    try:
                        img_path = img_path.resolve()
                        if IMAGE_DIR in img_path.parents and img_path.is_file():
                            img_path.unlink(missing_ok=True)
                    except Exception:
                        pass
            return

        # 文字模型也支援「圖片 + 文字」：使用者傳圖片時，讓 gemma4 分析
        image_attachment: discord.Attachment | None = None
        for att in (message.attachments or []):
            # 只抓第一張圖片
            if (att.content_type or "").startswith("image/") or (att.filename or "").lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                image_attachment = att
                break

        stop_thinking = await _start_thinking_effect(message.channel)
        try:
            # 預設不設逾時：就一直等到 Ollama 回覆（避免回「逾時」）
            timeout_raw = (os.getenv("OLLAMA_TEXT_TIMEOUT_S", "0") or "").strip().lower()
            # OLLAMA_TEXT_TIMEOUT_S=0 / none / off => 永不逾時（就一直等）
            if timeout_raw in {"0", "none", "off", "false", "no", ""}:
                timeout_s = None
            else:
                timeout_s = int(timeout_raw)
            started = time.monotonic()
            sep = "——————————————————"
            author_name = (getattr(message.author, "global_name", None) or getattr(message.author, "display_name", None) or message.author.name or "").strip()
            author_account = str(message.author).strip()
            author_id = message.author.id
            thinking_process = ""
            if image_attachment is not None:
                # 下載圖片 bytes（不落地）後丟給 vision
                img_bytes = await image_attachment.read()
                prompt_for_ollama = build_prompt_with_memory(author_id, selected_model, user_text)
                ollama_reply, thinking_process = await ask_ollama_vision(
                    selected_model,
                    prompt_for_ollama,
                    img_bytes,
                    timeout_s=timeout_s,
                    include_thinking=True,
                )
                ollama_reply = ollama_reply.strip()
                attachment_info = f"{image_attachment.filename} ({len(img_bytes)} bytes)"
            else:
                prompt_for_ollama = build_prompt_with_memory(author_id, selected_model, user_text)
                ollama_reply, thinking_process = await ask_ollama_text(
                    selected_model,
                    prompt_for_ollama,
                    timeout_s=timeout_s,
                    include_thinking=True,
                )
                ollama_reply = ollama_reply.strip()
                attachment_info = ""
            remember_conversation(author_id, selected_model, user_text, ollama_reply)
            thinking_sec = time.monotonic() - started
            lines = [
                sep,
                f"使用者名稱：{author_name}",
                f"使用者帳號：{author_account}",
                f"使用者ID：{author_id}",
                f"使用者詢問：{user_text}",
                "工具：無",
                f"使用者選的模型：{selected_model}",
            ]
            if attachment_info:
                lines.append(f"圖片：{attachment_info}")
            if thinking_process:
                lines.append(f"完整 thinking process：\n{thinking_process}")
            lines.extend(
                [
                    f"AI回覆：{ollama_reply}",
                    f"思考時間：{thinking_sec:.2f}秒",
                    sep,
                    "",
                ]
            )
            print("\n".join(lines))
        finally:
            await stop_thinking()

        # Discord 單則訊息上限約 2000 字；保守切段
        if not ollama_reply:
            ollama_reply = "（我沒有產生任何回覆）"

        chunks = textwrap.wrap(
            ollama_reply,
            width=1800,
            break_long_words=False,
            replace_whitespace=False,
        ) or [ollama_reply[:1800]]

        await send_chunks_with_temporary_thinking(message.channel, chunks[:3], thinking_process)
    except Exception as e:
        await message.channel.send(f"（發生錯誤：{type(e).__name__}: {str(e)[:300]}）")
    #!會傳到頻道裡的每個人
#######################指令#######################
@tree.command(name="hello",description="Say hello to the bot")
async def hello(interaction: discord.Interaction):
    """輸入/hello，機器人會回傳hey!"""
    # interaction 就是這次使用指令時送來的資料包
    # 裡面包含是誰按的，在哪裡暗的，指令相關資訊
    await interaction.response.send_message("Hey!") # 回覆這個指令，內容是 Hello, World!
    #!只會傳給使用者

@tree.command(name="dm", description="Send me a DM (for testing DM chat)")
async def dm(interaction: discord.Interaction, text: str):
    """輸入 /dm <文字>，機器人會私訊你同樣的文字（用來測試 DM 功能）"""
    try:
        await interaction.user.send(text)
        await interaction.response.send_message("已私訊你了", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"私訊失敗：{type(e).__name__}", ephemeral=True)


@tree.command(name="model", description="(DM only) Select the model for DM chat")
@discord.app_commands.choices(
    model=[
        discord.app_commands.Choice(name="qwen2.5-coder:1.5b_chat (default text)", value="qwen2.5-coder:1.5b_chat"),
        discord.app_commands.Choice(name="gemma4 (text)", value="gemma4"),
        discord.app_commands.Choice(name="ollama_happy (text)", value="ollama_happy"),
        discord.app_commands.Choice(name="ollama_angry (text)", value="ollama_angry"),
        discord.app_commands.Choice(name="ollama_sad (text)", value="ollama_sad"),
        discord.app_commands.Choice(name="x/flux2-klein:latest (image)", value="x/flux2-klein:latest"),
    ]
)
async def model(interaction: discord.Interaction, model: discord.app_commands.Choice[str]):
    """在 DM 模式選擇模型：gemma4（文字）或 x/flux2-klein:latest（生成圖片）"""
    # 只允許 DM 裡使用（避免伺服器頻道亂掉）
    if interaction.guild is not None:
        await interaction.response.send_message("請在私訊(DM)裡使用 /model", ephemeral=True)
        return

    chosen = (model.value or "").strip()
    if chosen not in DM_MODELS:
        await interaction.response.send_message("模型不支援", ephemeral=True)
        return

    dm_user_model[interaction.user.id] = chosen
    await interaction.response.send_message(f"DM 模式模型已切換為：{chosen}", ephemeral=True)


@tree.command(name="ask", description="Ask the bot (server only); DM can just type directly")
async def ask(interaction: discord.Interaction, question: str):
    """
    伺服器頻道只允許用 /ask 觸發（避免你說話就回答）。
    回覆使用 ephemeral，避免公開洗版。
    """
    if interaction.guild is None:
        await interaction.response.send_message("你在 DM 直接打字就會回答，不用 /ask", ephemeral=True)
        return

    # 只回覆特定人（同 on_message）
    if ALLOWED_DISCORD_USER_ID:
        if str(interaction.user.id) != ALLOWED_DISCORD_USER_ID:
            await interaction.response.send_message("（你沒有權限使用這個機器人）", ephemeral=True)
            return
    else:
        u = interaction.user
        author_candidates = {
            (u.name or "").strip(),
            (getattr(u, "global_name", None) or "").strip(),
            (getattr(u, "display_name", None) or "").strip(),
            str(u).strip(),
        }
        if ALLOWED_CHAT_USER not in author_candidates:
            await interaction.response.send_message("（你沒有權限使用這個機器人）", ephemeral=True)
            return

    q = (question or "").strip()
    if not q:
        await interaction.response.send_message("請輸入問題", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    try:
        timeout_raw = (os.getenv("OLLAMA_TEXT_TIMEOUT_S", "0") or "").strip().lower()
        if timeout_raw in {"0", "none", "off", "false", "no", ""}:
            timeout_s = None
        else:
            timeout_s = int(timeout_raw)

        started = time.monotonic()
        prompt_for_ollama = build_prompt_with_memory(interaction.user.id, DEFAULT_CHAT_MODEL, q)
        ollama_reply, thinking_process = await ask_ollama_text(
            DEFAULT_CHAT_MODEL,
            prompt_for_ollama,
            timeout_s=timeout_s,
            include_thinking=True,
        )
        ollama_reply = ollama_reply.strip()
        remember_conversation(interaction.user.id, DEFAULT_CHAT_MODEL, q, ollama_reply)
        thinking_sec = time.monotonic() - started
        sep = "——————————————————"
        author_name = (getattr(interaction.user, "global_name", None) or getattr(interaction.user, "display_name", None) or interaction.user.name or "").strip()
        author_account = str(interaction.user).strip()
        print(
            "\n".join(
                [
                    sep,
                    f"使用者名稱：{author_name}",
                    f"使用者帳號：{author_account}",
                    f"使用者ID：{interaction.user.id}",
                    f"使用者詢問：{q}",
                    "工具：無",
                    f"使用者選的模型：{DEFAULT_CHAT_MODEL}",
                    *([f"完整 thinking process：\n{thinking_process}"] if thinking_process else []),
                    f"AI回覆：{ollama_reply}",
                    f"思考時間：{thinking_sec:.2f}秒",
                    sep,
                    "",
                ]
            )
        )
    except Exception as e:
        await interaction.followup.send(f"（發生錯誤：{type(e).__name__}: {str(e)[:300]}）", ephemeral=True)
        return

    if not ollama_reply:
        ollama_reply = "（我沒有產生任何回覆）"

    chunks = textwrap.wrap(
        ollama_reply,
        width=1800,
        break_long_words=False,
        replace_whitespace=False,
    ) or [ollama_reply[:1800]]

    await send_followup_chunks_with_temporary_thinking(
        interaction,
        chunks[:3],
        ephemeral=True,
        thinking_text=thinking_process,
    )


@tree.command(name="web_search", description="Search the web and answer with Ollama")
@discord.app_commands.choices(
    model=[
        discord.app_commands.Choice(name="qwen2.5-coder:1.5b_chat (default text)", value="qwen2.5-coder:1.5b_chat"),
        discord.app_commands.Choice(name="gemma4 (text)", value="gemma4"),
        discord.app_commands.Choice(name="ollama_happy (text)", value="ollama_happy"),
        discord.app_commands.Choice(name="ollama_angry (text)", value="ollama_angry"),
        discord.app_commands.Choice(name="ollama_sad (text)", value="ollama_sad"),
    ]
)
async def web_search(interaction: discord.Interaction, question: str, model: discord.app_commands.Choice[str]):
    """輸入 /web_search <問題>，先搜尋網頁，再讓 Ollama 根據搜尋結果回答。"""
    private_reply = interaction.guild is not None

    if ALLOWED_DISCORD_USER_ID:
        if str(interaction.user.id) != ALLOWED_DISCORD_USER_ID:
            await interaction.response.send_message("（你沒有權限使用這個機器人）", ephemeral=private_reply)
            return
    else:
        u = interaction.user
        author_candidates = {
            (u.name or "").strip(),
            (getattr(u, "global_name", None) or "").strip(),
            (getattr(u, "display_name", None) or "").strip(),
            str(u).strip(),
        }
        if ALLOWED_CHAT_USER not in author_candidates:
            await interaction.response.send_message("（你沒有權限使用這個機器人）", ephemeral=private_reply)
            return

    q = (question or "").strip()
    if not q:
        await interaction.response.send_message("請輸入要搜尋的問題", ephemeral=private_reply)
        return

    selected_model = (model.value or "").strip()
    if selected_model not in DM_MODELS or selected_model == "x/flux2-klein:latest":
        await interaction.response.send_message("web_search 只能選文字模型，不能選生成圖片模型。", ephemeral=private_reply)
        return

    await interaction.response.defer(ephemeral=private_reply, thinking=True)

    try:
        started = time.monotonic()
        results = await search_web_results(q)
        if not results:
            await interaction.followup.send("找不到可用的網頁搜尋結果。", ephemeral=private_reply)
            return

        search_context = format_search_results_for_log(results)
        search_urls = format_search_urls_for_log(results)
        page_reads = await fetch_web_pages(results)
        page_read_context = format_page_reads_for_log(page_reads)
        memory_context = format_conversation_memory(interaction.user.id, selected_model)
        prompt = f"""
你要根據「實際讀到的網頁內容」回答使用者問題。
規則：
1. 使用繁體中文回答。
2. 優先使用「實際讀到的網頁內容」，不要只介紹網址。
3. 如果實際讀到的內容不足，再參考搜尋摘要；如果仍不足，就直接說資料不足。
4. 不要輸出 thinking process、推理過程、草稿、自我對話。
5. 回答最後加上「來源」清單，列出有用到的編號與網址。
6. 如果使用者問天氣、價格、新聞這類即時問題，要直接整理目前讀到的資訊，不要只叫使用者自己去點網址。

使用者問題：
{q}

對話記憶：
{memory_context}

搜尋摘要：
{search_context}

實際讀到的網頁內容：
{page_read_context}
""".strip()

        timeout_raw = (os.getenv("OLLAMA_TEXT_TIMEOUT_S", "0") or "").strip().lower()
        if timeout_raw in {"0", "none", "off", "false", "no", ""}:
            timeout_s = None
        else:
            timeout_s = int(timeout_raw)
        ollama_reply, thinking_process = await ask_ollama_text(
            selected_model,
            prompt,
            timeout_s=timeout_s,
            include_thinking=True,
        )
        ollama_reply = ollama_reply.strip()
        remember_conversation(interaction.user.id, selected_model, f"/web_search {q}", ollama_reply)
        thinking_sec = time.monotonic() - started

        sep = "——————————————————"
        author_name = (getattr(interaction.user, "global_name", None) or getattr(interaction.user, "display_name", None) or interaction.user.name or "").strip()
        author_account = str(interaction.user).strip()
        print(
            "\n".join(
                [
                    sep,
                    f"使用者名稱：{author_name}",
                    f"使用者帳號：{author_account}",
                    f"使用者ID：{interaction.user.id}",
                    f"使用者詢問：/web_search {q}",
                    "工具：web_search",
                    f"使用者選的模型：{selected_model}",
                    f"使用者填的問題：{q}",
                    f"Ollama查詢：{q}",
                    f"Ollama看的網址：\n{search_urls}",
                    f"搜尋結果數：{len(results)}",
                    f"Ollama查到的東西：\n{search_context}",
                    f"Ollama實際讀到的網頁內容：\n{page_read_context}",
                    *([f"完整 thinking process：\n{thinking_process}"] if thinking_process else []),
                    f"AI回覆：{ollama_reply}",
                    f"思考時間：{thinking_sec:.2f}秒",
                    sep,
                    "",
                ]
            )
        )
    except Exception as e:
        await interaction.followup.send(f"（發生錯誤：{type(e).__name__}: {str(e)[:300]}）", ephemeral=private_reply)
        return

    if not ollama_reply:
        ollama_reply = "（我沒有產生任何回覆）"

    chunks = textwrap.wrap(
        ollama_reply,
        width=1800,
        break_long_words=False,
        replace_whitespace=False,
    ) or [ollama_reply[:1800]]

    await send_followup_chunks_with_temporary_thinking(
        interaction,
        chunks[:3],
        ephemeral=private_reply,
        thinking_text=thinking_process,
    )

#######################啟動#######################
def main():
    bot.run(os.getenv("DC_BOT_TOKEN")) # 從環境變數拿到機器人的 token，然後啟動機器人
    print("有人打招呼了！") # 在終端機印出「有人打招呼了！」，讓我們知道這件事發生了
#如果這份檔案室「直接執行」，
# 就呼叫 main() 啟動機器人！

if __name__=="__main__":
    main() #正式啟用程式
