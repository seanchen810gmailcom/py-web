"""Mac 鏡頭的本機 FastAPI + MJPEG 串流伺服器。"""

from __future__ import annotations

import hmac
import os
import secrets
import socket
import threading
import time
from dataclasses import dataclass
from typing import Any, Iterator

try:
    from starlette.requests import Request as StarletteRequest
except ImportError:
    StarletteRequest = Any


class CameraServerError(RuntimeError):
    """Camera 模組可以安全顯示給 Discord 管理員的錯誤。"""


class CameraDependencyError(CameraServerError):
    """相機串流需要的 Python 套件尚未安裝。"""


@dataclass(frozen=True)
class CameraStartResult:
    """成功啟動後僅回傳給 slash command 的資訊。"""

    already_running: bool
    viewing_url: str
    verification_code: str | None
    expires_in_seconds: int
    port: int


class CameraServer:
    """管理鏡頭、串流網頁、一次性驗證碼與資源釋放。"""

    CODE_TTL_SECONDS = 300
    MAX_PORT_ATTEMPTS = 20
    MAX_FAILED_ATTEMPTS = 5
    FAILED_ATTEMPT_WINDOW_SECONDS = 60
    SESSION_COOKIE_NAME = "camera_session"

    def __init__(
        self,
        host: str = "0.0.0.0",
        preferred_port: int = 8080,
        camera_index: int = 0,
        target_fps: int = 60,
        frame_width: int = 1280,
        frame_height: int = 720,
        jpeg_quality: int = 80,
    ) -> None:
        self.host = host
        self.preferred_port = preferred_port
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.jpeg_quality = jpeg_quality

        self._lifecycle_lock = threading.RLock()
        self._state_lock = threading.RLock()
        self._frame_condition = threading.Condition(self._state_lock)
        self._capture_stop_event = threading.Event()

        self._cv2: Any = None
        self._fastapi_types: dict[str, Any] = {}
        self._capture: Any = None
        self._capture_thread: threading.Thread | None = None
        self._uvicorn_server: Any = None
        self._server_thread: threading.Thread | None = None
        self._server_socket: socket.socket | None = None
        self._app: Any = None
        self._port: int | None = None
        self._latest_jpeg: bytes | None = None
        self._frame_sequence = 0
        self._camera_error = ""

        self._verification_code: str | None = None
        self._verification_expires_at = 0.0
        self._viewer_session_token: str | None = None
        self._viewer_session_ip: str | None = None
        self._failed_attempts: dict[str, list[float]] = {}

    @classmethod
    def from_environment(cls) -> "CameraServer":
        """使用 .env 的選填設定建立伺服器，無效數字會回到安全預設值。"""

        return cls(
            host=(os.getenv("CAMERA_HOST", "0.0.0.0").strip() or "0.0.0.0"),
            preferred_port=cls._env_int("CAMERA_PORT", 8080, 1, 65535),
            camera_index=cls._env_int("CAMERA_INDEX", 0, 0, 20),
            target_fps=cls._env_int("CAMERA_TARGET_FPS", 60, 1, 60),
        )

    @staticmethod
    def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
        try:
            value = int(os.getenv(name, str(default)).strip())
        except (TypeError, ValueError):
            return default
        return min(max(value, minimum), maximum)

    def start(self) -> CameraStartResult:
        """啟動鏡頭與網頁伺服器；已啟動時不會建立第二份資源。"""

        with self._lifecycle_lock:
            current_status = self.status()
            if current_status["running"]:
                return CameraStartResult(
                    already_running=True,
                    viewing_url=self.viewing_url(),
                    verification_code=None,
                    expires_in_seconds=0,
                    port=int(current_status["port"]),
                )

            self._stop_components()
            self._load_dependencies()
            capture = self._open_camera()
            server_socket = self._bind_available_socket()

            try:
                first_jpeg = self._read_and_encode_first_frame(capture)
                app = self._build_app()
                uvicorn = self._fastapi_types["uvicorn"]
                config = uvicorn.Config(
                    app,
                    host=self.host,
                    port=self._port,
                    log_level="warning",
                    access_log=False,
                    lifespan="off",
                )
                uvicorn_server = uvicorn.Server(config)

                with self._state_lock:
                    self._capture = capture
                    self._server_socket = server_socket
                    self._app = app
                    self._uvicorn_server = uvicorn_server
                    self._latest_jpeg = first_jpeg
                    self._frame_sequence += 1
                    self._camera_error = ""
                    self._capture_stop_event.clear()

                self._capture_thread = threading.Thread(
                    target=self._capture_loop,
                    name="camera-capture",
                    daemon=True,
                )
                self._server_thread = threading.Thread(
                    target=self._run_web_server,
                    name="camera-web-server",
                    daemon=True,
                )
                self._capture_thread.start()
                self._server_thread.start()

                if not self._wait_until_server_started(timeout=5.0):
                    raise CameraServerError("網頁伺服器無法啟動，請檢查本機網路與 port 設定。")

                code = self._issue_verification_code()
                return CameraStartResult(
                    already_running=False,
                    viewing_url=self.viewing_url(),
                    verification_code=code,
                    expires_in_seconds=self.CODE_TTL_SECONDS,
                    port=int(self._port or self.preferred_port),
                )
            except Exception:
                if self._capture is None:
                    capture.release()
                if self._server_socket is None:
                    server_socket.close()
                self._stop_components()
                raise

    def stop(self) -> bool:
        """停止伺服器、串流與鏡頭，並清除所有驗證狀態。"""

        with self._lifecycle_lock:
            was_active = self.status()["running"] or self._capture is not None
            self._stop_components()
            return bool(was_active)

    def status(self) -> dict[str, Any]:
        """回傳不含密碼或驗證碼內容的執行狀態。"""

        with self._state_lock:
            self._expire_verification_code_locked()
            capture_thread_alive = bool(self._capture_thread and self._capture_thread.is_alive())
            server_thread_alive = bool(self._server_thread and self._server_thread.is_alive())
            server_started = bool(self._uvicorn_server and getattr(self._uvicorn_server, "started", False))
            camera_active = self._capture is not None and capture_thread_alive
            server_active = server_thread_alive and server_started
            return {
                "running": camera_active and server_active,
                "camera_active": camera_active,
                "server_active": server_active,
                "has_valid_code": self._verification_code is not None,
                "viewer_authenticated": self._viewer_session_token is not None,
                "port": self._port,
                "camera_error": self._camera_error,
            }

    def viewing_url(self) -> str:
        """產生手機在同一個區域網路內可開啟的網址。"""

        host = self._discover_lan_ip() if self.host in {"0.0.0.0", "::"} else self.host
        return f"http://{host}:{self._port or self.preferred_port}"

    def verify_code(self, code: str, client_ip: str) -> tuple[str, str | None]:
        """驗證一次性碼，成功後立即銷毀並核發單一觀看 session。"""

        normalized_ip = client_ip or "unknown"
        now = time.monotonic()
        with self._state_lock:
            self._expire_verification_code_locked(now)
            attempts = [
                attempt
                for attempt in self._failed_attempts.get(normalized_ip, [])
                if now - attempt < self.FAILED_ATTEMPT_WINDOW_SECONDS
            ]
            self._failed_attempts[normalized_ip] = attempts
            if len(attempts) >= self.MAX_FAILED_ATTEMPTS:
                return "rate_limited", None
            if not self._verification_code:
                return "invalid", None
            if not hmac.compare_digest(str(code), self._verification_code):
                attempts.append(now)
                return "invalid", None

            token = secrets.token_urlsafe(32)
            self._verification_code = None
            self._verification_expires_at = 0.0
            self._viewer_session_token = token
            self._viewer_session_ip = normalized_ip
            self._failed_attempts.clear()
            return "ok", token

    def is_session_valid(self, token: str | None, client_ip: str) -> bool:
        """同時比對不可預測的 cookie 與驗證時的來源 IP。"""

        with self._state_lock:
            if not token or not self._viewer_session_token:
                return False
            return hmac.compare_digest(token, self._viewer_session_token) and hmac.compare_digest(
                client_ip or "unknown",
                self._viewer_session_ip or "",
            )

    def iter_mjpeg_frames(self) -> Iterator[bytes]:
        """每個觀看者只取最新畫面，網路慢時自然丟幀而不會累積佇列。"""

        last_sequence = -1
        while True:
            with self._frame_condition:
                self._frame_condition.wait_for(
                    lambda: self._frame_sequence != last_sequence or not self.status()["running"],
                    timeout=2.0,
                )
                if not self.status()["running"]:
                    return
                frame = self._latest_jpeg
                last_sequence = self._frame_sequence
            if frame:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"

    def _load_dependencies(self) -> None:
        missing: list[str] = []
        try:
            import cv2
        except ImportError:
            cv2 = None
            missing.append("opencv-python")
        try:
            import uvicorn
            from fastapi import FastAPI, Request
            from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
        except ImportError:
            uvicorn = FastAPI = Request = HTMLResponse = JSONResponse = RedirectResponse = StreamingResponse = None
            missing.extend(["fastapi", "uvicorn"])
        if missing:
            package_names = ", ".join(dict.fromkeys(missing))
            raise CameraDependencyError(
                f"Camera 模組缺少套件：{package_names}。請先執行 pip install -r requirements.txt。"
            )
        self._cv2 = cv2
        self._fastapi_types = {
            "uvicorn": uvicorn,
            "FastAPI": FastAPI,
            "Request": Request,
            "HTMLResponse": HTMLResponse,
            "JSONResponse": JSONResponse,
            "RedirectResponse": RedirectResponse,
            "StreamingResponse": StreamingResponse,
        }

    def _open_camera(self) -> Any:
        cv2 = self._cv2
        backends: list[int | None] = []
        avfoundation = getattr(cv2, "CAP_AVFOUNDATION", None)
        if avfoundation is not None:
            backends.append(avfoundation)
        backends.append(None)

        capture = None
        for backend in backends:
            candidate = cv2.VideoCapture(self.camera_index, backend) if backend is not None else cv2.VideoCapture(self.camera_index)
            if candidate.isOpened():
                capture = candidate
                break
            candidate.release()
        if capture is None:
            raise CameraServerError(
                "無法開啟 Mac 鏡頭。請到「系統設定 > 隱私與安全性 > 相機」允許 Terminal/Python，"
                "並確認 FaceTime、Zoom 或 Photo Booth 沒有正在使用鏡頭。"
            )

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        capture.set(cv2.CAP_PROP_FPS, self.target_fps)
        if hasattr(cv2, "CAP_PROP_BUFFERSIZE"):
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return capture

    def _read_and_encode_first_frame(self, capture: Any) -> bytes:
        ok, frame = capture.read()
        if not ok or frame is None:
            raise CameraServerError(
                "鏡頭已被偵測到，但無法讀取畫面。請檢查 macOS 相機權限，並關閉可能佔用鏡頭的 FaceTime、Zoom 或 Photo Booth。"
            )
        ok, encoded = self._cv2.imencode(
            ".jpg",
            frame,
            [int(self._cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality],
        )
        if not ok:
            raise CameraServerError("鏡頭畫面無法編碼為 MJPEG。")
        return encoded.tobytes()

    def _capture_loop(self) -> None:
        consecutive_failures = 0
        while not self._capture_stop_event.is_set():
            with self._state_lock:
                capture = self._capture
            if capture is None:
                return
            ok, frame = capture.read()
            if not ok or frame is None:
                consecutive_failures += 1
                if consecutive_failures >= 30:
                    with self._state_lock:
                        self._camera_error = "鏡頭畫面已中斷，可能被其他 App 佔用或權限被取消。"
                    return
                self._capture_stop_event.wait(min(0.05 * consecutive_failures, 0.5))
                continue

            consecutive_failures = 0
            ok, encoded = self._cv2.imencode(
                ".jpg",
                frame,
                [int(self._cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality],
            )
            if not ok:
                self._capture_stop_event.wait(0.05)
                continue
            with self._frame_condition:
                self._latest_jpeg = encoded.tobytes()
                self._frame_sequence += 1
                self._frame_condition.notify_all()

    def _bind_available_socket(self) -> socket.socket:
        last_error: OSError | None = None
        for port in range(self.preferred_port, min(self.preferred_port + self.MAX_PORT_ATTEMPTS, 65536)):
            candidate = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            candidate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                candidate.bind((self.host, port))
                candidate.listen(128)
                candidate.setblocking(False)
                self._port = port
                return candidate
            except OSError as exc:
                last_error = exc
                candidate.close()
        raise CameraServerError(
            f"無法使用 port {self.preferred_port} 到 {self.preferred_port + self.MAX_PORT_ATTEMPTS - 1}，"
            "請關閉佔用中的程式或在 .env 調整 CAMERA_PORT。"
        ) from last_error

    def _run_web_server(self) -> None:
        server = self._uvicorn_server
        server_socket = self._server_socket
        if server is None or server_socket is None:
            return
        try:
            server.run(sockets=[server_socket])
        finally:
            with self._frame_condition:
                self._frame_condition.notify_all()

    def _wait_until_server_started(self, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            server = self._uvicorn_server
            thread = self._server_thread
            if server is not None and getattr(server, "started", False):
                return True
            if thread is None or not thread.is_alive():
                return False
            time.sleep(0.05)
        return False

    def _issue_verification_code(self) -> str:
        code = f"{secrets.randbelow(1_000_000):06d}"
        with self._state_lock:
            self._verification_code = code
            self._verification_expires_at = time.monotonic() + self.CODE_TTL_SECONDS
            self._viewer_session_token = None
            self._viewer_session_ip = None
            self._failed_attempts.clear()
        return code

    def _expire_verification_code_locked(self, now: float | None = None) -> None:
        current_time = time.monotonic() if now is None else now
        if self._verification_code and current_time >= self._verification_expires_at:
            self._verification_code = None
            self._verification_expires_at = 0.0

    def _stop_components(self) -> None:
        with self._state_lock:
            capture = self._capture
            capture_thread = self._capture_thread
            uvicorn_server = self._uvicorn_server
            server_thread = self._server_thread
            server_socket = self._server_socket
            self._capture_stop_event.set()
            if uvicorn_server is not None:
                uvicorn_server.should_exit = True
            self._verification_code = None
            self._verification_expires_at = 0.0
            self._viewer_session_token = None
            self._viewer_session_ip = None
            self._failed_attempts.clear()
            self._frame_condition.notify_all()

        if capture_thread and capture_thread is not threading.current_thread():
            capture_thread.join(timeout=2.0)
        if capture is not None:
            capture.release()
        if capture_thread and capture_thread.is_alive():
            capture_thread.join(timeout=1.0)
        if server_thread and server_thread is not threading.current_thread():
            server_thread.join(timeout=5.0)
        if server_socket is not None:
            try:
                server_socket.close()
            except OSError:
                pass

        with self._state_lock:
            self._capture = None
            self._capture_thread = None
            self._uvicorn_server = None
            self._server_thread = None
            self._server_socket = None
            self._app = None
            self._port = None
            self._latest_jpeg = None
            self._camera_error = ""
            self._capture_stop_event.clear()

    @staticmethod
    def _discover_lan_ip() -> str:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("8.8.8.8", 80))
            return str(probe.getsockname()[0])
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return "127.0.0.1"
        finally:
            probe.close()

    def _build_app(self) -> Any:
        FastAPI = self._fastapi_types["FastAPI"]
        HTMLResponse = self._fastapi_types["HTMLResponse"]
        JSONResponse = self._fastapi_types["JSONResponse"]
        RedirectResponse = self._fastapi_types["RedirectResponse"]
        StreamingResponse = self._fastapi_types["StreamingResponse"]

        app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
        no_store_headers = {"Cache-Control": "no-store, max-age=0", "Pragma": "no-cache"}

        def client_ip(request: Any) -> str:
            return str(request.client.host) if request.client else "unknown"

        def request_is_authenticated(request: Any) -> bool:
            token = request.cookies.get(self.SESSION_COOKIE_NAME)
            return self.is_session_valid(token, client_ip(request))

        @app.get("/", response_class=HTMLResponse)
        async def login_page(request: StarletteRequest) -> Any:
            if request_is_authenticated(request):
                return RedirectResponse("/view", status_code=303, headers=no_store_headers)
            return HTMLResponse(self._login_html(), headers=no_store_headers)

        @app.post("/verify")
        async def verify(request: StarletteRequest) -> Any:
            try:
                payload = await request.json()
            except Exception:
                return JSONResponse({"ok": False, "message": "請輸入 6 位數驗證碼。"}, status_code=400, headers=no_store_headers)
            code = str(payload.get("code", "")).strip() if isinstance(payload, dict) else ""
            if len(code) != 6 or not code.isdigit():
                return JSONResponse({"ok": False, "message": "請輸入 6 位數驗證碼。"}, status_code=400, headers=no_store_headers)
            result, token = self.verify_code(code, client_ip(request))
            if result == "rate_limited":
                return JSONResponse(
                    {"ok": False, "message": "嘗試次數過多，請稍後再試。"},
                    status_code=429,
                    headers=no_store_headers,
                )
            if result != "ok" or token is None:
                return JSONResponse(
                    {"ok": False, "message": "驗證碼錯誤、已過期或已使用。"},
                    status_code=401,
                    headers=no_store_headers,
                )
            response = JSONResponse({"ok": True, "redirect": "/view"}, headers=no_store_headers)
            response.set_cookie(
                self.SESSION_COOKIE_NAME,
                token,
                httponly=True,
                samesite="strict",
                secure=False,
                path="/",
            )
            return response

        @app.get("/view", response_class=HTMLResponse)
        async def viewer_page(request: StarletteRequest) -> Any:
            if not request_is_authenticated(request):
                return RedirectResponse("/", status_code=303, headers=no_store_headers)
            return HTMLResponse(self._viewer_html(), headers=no_store_headers)

        @app.get("/stream")
        async def stream(request: StarletteRequest) -> Any:
            if not request_is_authenticated(request):
                return JSONResponse({"detail": "Unauthorized"}, status_code=401, headers=no_store_headers)
            return StreamingResponse(
                self.iter_mjpeg_frames(),
                media_type="multipart/x-mixed-replace; boundary=frame",
                headers=no_store_headers,
            )

        return app

    @staticmethod
    def _login_html() -> str:
        return """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="robots" content="noindex,nofollow">
  <title>Mac Camera 驗證</title>
  <style>
    :root { color-scheme: dark; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #101114; color: #f5f5f7; }
    main { width: min(88vw, 360px); padding: 28px; border: 1px solid #34363d; border-radius: 18px; background: #1b1d22; }
    h1 { margin: 0 0 8px; font-size: 1.45rem; }
    p { color: #b9bdc7; line-height: 1.5; }
    input, button { box-sizing: border-box; width: 100%; min-height: 50px; border-radius: 12px; font-size: 1.1rem; }
    input { border: 1px solid #484b55; padding: 0 14px; color: #fff; background: #101114; letter-spacing: .35em; text-align: center; }
    button { margin-top: 12px; border: 0; color: #fff; background: #2563eb; font-weight: 700; }
    #message { min-height: 1.5em; color: #ff8a8a; }
  </style>
</head>
<body>
  <main>
    <h1>Mac Camera</h1>
    <p>請輸入 Discord 提供的 6 位數一次性驗證碼。</p>
    <form id="verify-form">
      <input id="code" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" required aria-label="6 位數驗證碼">
      <button type="submit">開始觀看</button>
    </form>
    <p id="message" role="alert"></p>
  </main>
  <script>
    const form = document.getElementById('verify-form');
    const codeInput = document.getElementById('code');
    const message = document.getElementById('message');
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      message.textContent = '';
      try {
        const response = await fetch('/verify', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({code: codeInput.value})
        });
        const data = await response.json();
        if (!response.ok) {
          message.textContent = data.message || '驗證失敗。';
          codeInput.value = '';
          codeInput.focus();
          return;
        }
        window.location.replace(data.redirect || '/view');
      } catch (_) {
        message.textContent = '無法連線到鏡頭伺服器。';
      }
    });
  </script>
</body>
</html>"""

    @staticmethod
    def _viewer_html() -> str:
        return """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="robots" content="noindex,nofollow">
  <title>Mac Camera</title>
  <style>
    :root { color-scheme: dark; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; min-height: 100vh; background: #050506; color: #fff; display: grid; grid-template-rows: auto 1fr; }
    header { padding: 12px 16px; background: #15161a; font-weight: 650; }
    main { display: grid; place-items: center; overflow: hidden; }
    img { display: block; width: 100%; height: 100%; max-height: calc(100vh - 48px); object-fit: contain; background: #000; }
  </style>
</head>
<body>
  <header>Mac Camera 即時畫面</header>
  <main><img src="/stream" alt="Mac 鏡頭即時串流"></main>
</body>
</html>"""
