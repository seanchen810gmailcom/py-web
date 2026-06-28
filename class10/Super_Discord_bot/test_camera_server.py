"""Camera 模組的本機驗證、存取控制與 port fallback 測試。"""

import socket
import time
import unittest
import urllib.request

from camera_server import CameraServer


class CameraAuthenticationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = CameraServer(host="127.0.0.1", preferred_port=18080)

    def tearDown(self) -> None:
        self.server.stop()

    def test_code_is_six_digits_and_one_time_only(self) -> None:
        code = self.server._issue_verification_code()
        self.assertRegex(code, r"^\d{6}$")
        self.assertTrue(self.server.status()["has_valid_code"])

        result, token = self.server.verify_code(code, "192.0.2.10")
        self.assertEqual(result, "ok")
        self.assertTrue(token)
        self.assertFalse(self.server.status()["has_valid_code"])
        self.assertTrue(self.server.is_session_valid(token, "192.0.2.10"))
        self.assertFalse(self.server.is_session_valid(token, "192.0.2.11"))

        second_result, second_token = self.server.verify_code(code, "192.0.2.10")
        self.assertEqual(second_result, "invalid")
        self.assertIsNone(second_token)

    def test_expired_code_is_rejected_and_removed_from_status(self) -> None:
        code = self.server._issue_verification_code()
        with self.server._state_lock:
            self.server._verification_expires_at = time.monotonic() - 1

        result, token = self.server.verify_code(code, "192.0.2.20")
        self.assertEqual(result, "invalid")
        self.assertIsNone(token)
        self.assertFalse(self.server.status()["has_valid_code"])

    def test_failed_attempts_are_rate_limited(self) -> None:
        self.server._issue_verification_code()
        for _ in range(self.server.MAX_FAILED_ATTEMPTS):
            result, _ = self.server.verify_code("000000", "192.0.2.30")
            self.assertEqual(result, "invalid")
        result, token = self.server.verify_code("000000", "192.0.2.30")
        self.assertEqual(result, "rate_limited")
        self.assertIsNone(token)

    def test_status_never_contains_code_or_session_token(self) -> None:
        code = self.server._issue_verification_code()
        result, token = self.server.verify_code(code, "192.0.2.40")
        self.assertEqual(result, "ok")
        status_text = repr(self.server.status())
        self.assertNotIn(code, status_text)
        self.assertNotIn(str(token), status_text)


class CameraWebAccessTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ImportError as exc:
            self.skipTest(f"FastAPI test dependency unavailable: {exc}")
        self.TestClient = TestClient
        self.server = CameraServer(host="127.0.0.1", preferred_port=18080)
        self.server._load_dependencies()
        self.app = self.server._build_app()

    def tearDown(self) -> None:
        if hasattr(self, "server"):
            self.server.stop()

    def test_view_and_stream_require_verified_cookie(self) -> None:
        code = self.server._issue_verification_code()
        with self.TestClient(self.app) as client:
            blocked_view = client.get("/view", follow_redirects=False)
            self.assertEqual(blocked_view.status_code, 303)
            blocked_stream = client.get("/stream")
            self.assertEqual(blocked_stream.status_code, 401)

            verified = client.post("/verify", json={"code": code})
            self.assertEqual(verified.status_code, 200)
            allowed_view = client.get("/view")
            self.assertEqual(allowed_view.status_code, 200)
            self.assertIn("/stream", allowed_view.text)

        with self.TestClient(self.app) as second_client:
            reused = second_client.post("/verify", json={"code": code})
            self.assertEqual(reused.status_code, 401)


class CameraPortFallbackTests(unittest.TestCase):
    def test_occupied_preferred_port_uses_next_available_port(self) -> None:
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.bind(("127.0.0.1", 0))
        blocker.listen(1)
        occupied_port = int(blocker.getsockname()[1])
        server = CameraServer(host="127.0.0.1", preferred_port=occupied_port)
        selected_socket = None
        try:
            selected_socket = server._bind_available_socket()
            self.assertNotEqual(server._port, occupied_port)
            self.assertGreater(int(server._port or 0), occupied_port)
        finally:
            if selected_socket is not None:
                selected_socket.close()
            blocker.close()


class CameraLifecycleTests(unittest.TestCase):
    def test_server_starts_once_and_releases_fake_camera_on_stop(self) -> None:
        server = CameraServer(host="127.0.0.1", preferred_port=18180)

        class FakeCapture:
            def __init__(self) -> None:
                self.released = False

            def release(self) -> None:
                self.released = True

        fake_capture = FakeCapture()
        server._open_camera = lambda: fake_capture
        server._read_and_encode_first_frame = lambda capture: b"fake-jpeg"
        server._capture_loop = lambda: server._capture_stop_event.wait()
        try:
            started = server.start()
            self.assertFalse(started.already_running)
            self.assertRegex(str(started.verification_code), r"^\d{6}$")
            self.assertTrue(server.status()["running"])

            duplicate = server.start()
            self.assertTrue(duplicate.already_running)
            self.assertIsNone(duplicate.verification_code)

            with urllib.request.urlopen(started.viewing_url, timeout=3) as response:
                page = response.read().decode("utf-8")
            self.assertIn("6 位數一次性驗證碼", page)
        finally:
            server.stop()

        self.assertTrue(fake_capture.released)
        self.assertFalse(server.status()["running"])
        self.assertFalse(server.status()["has_valid_code"])


if __name__ == "__main__":
    unittest.main()
