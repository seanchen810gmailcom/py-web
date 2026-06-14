#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 逐行註解：測試 Google Workspace Auto Mode、動作解析與 dispatcher routing，不直接呼叫 Google API。

import unittest  # 逐行註解：使用 Python 內建 unittest。

import AI  # 逐行註解：載入 Discord bot 主程式，但不執行 main()。


class GoogleWorkspaceIntentTests(unittest.TestCase):  # 逐行註解：Workspace 意圖解析測試。
    def setUp(self):  # 逐行註解：每個測試共用 Auto profile。
        self.profile = {"last_tool": "google_auto"}  # 逐行註解：模擬使用者選 Auto Mode。

    def test_auto_mode_routes_required_examples(self):  # 逐行註解：驗證使用者要求的 Auto Mode 範例。
        self.assertEqual(AI.google_workspace_detect_tool_from_text(self.profile, "寄信給 Sean 主旨是測試 內容是 Hi"), "google_gmail")  # 逐行註解：寄信要走 Gmail。
        self.assertEqual(AI.google_workspace_detect_tool_from_text(self.profile, "建立簡報 called Test"), "google_slide")  # 逐行註解：建立簡報要走 Slides。
        self.assertEqual(AI.google_workspace_detect_tool_from_text(self.profile, "建立試算表 called Test"), "google_sheet")  # 逐行註解：建立試算表要走 Sheets。
        self.assertEqual(AI.google_workspace_detect_tool_from_text(self.profile, "建立會議 標題是 Test 今天 14:30"), "google_calendar")  # 逐行註解：建立會議要走 Calendar。
        self.assertEqual(AI.google_workspace_detect_tool_from_text(self.profile, "建立聯絡人 姓名是 Sean email 是 sean@example.com"), "google_contacts")  # 逐行註解：建立聯絡人要走 Contacts。

    def test_action_detection_covers_full_workspace_actions(self):  # 逐行註解：驗證新增的 action 都會被辨識。
        actions = AI.google_workspace_detect_actions("寄信給 Sean 主旨是測試 內容是 Hi")  # 逐行註解：解析寄信動作。
        self.assertIn("send", actions)  # 逐行註解：寄信必須是 send。
        self.assertIn("draft", AI.google_workspace_detect_actions("建立 Gmail 草稿 收件者是 a@example.com 內容是 Hi"))  # 逐行註解：草稿必須是 draft。
        slide_actions = AI.google_workspace_detect_actions("新增投影片 內容是 Slide 1")  # 逐行註解：解析新增投影片。
        self.assertIn("create_slide", slide_actions)  # 逐行註解：新增投影片必須是 create_slide。
        self.assertIn("archive", AI.google_workspace_detect_actions("封存 Gmail Message ID:abc"))  # 逐行註解：封存必須被辨識。
        self.assertIn("label", AI.google_workspace_detect_actions("標籤 Gmail Message ID:abc 標籤是Test"))  # 逐行註解：標籤必須被辨識。
        self.assertIn("upload", AI.google_workspace_detect_actions("上傳 路徑是 /tmp/a.txt"))  # 逐行註解：上傳必須被辨識。
        self.assertIn("download", AI.google_workspace_detect_actions("下載 檔案ID:abc"))  # 逐行註解：下載必須被辨識。

    def test_title_and_account_email_handling(self):  # 逐行註解：驗證標題抽取與 Email 隔離例外。
        self.assertEqual(AI.google_workspace_extract_title("create a presentation called Test"), "Test")  # 逐行註解：英文 called 要抽到標題。
        self.assertEqual(AI.google_workspace_extract_title("建立試算表 叫做 Test_Sheet"), "Test_Sheet")  # 逐行註解：中文叫做要抽到標題。
        self.assertTrue(AI.google_workspace_requires_google_api(["send"]))  # 逐行註解：send 必須要求 Google API。
        self.assertFalse(AI.google_workspace_email_should_match_account("google_gmail", "寄信給 a@example.com 內容是 Hi"))  # 逐行註解：Gmail 收件者不能被誤判成帳號切換。
        self.assertFalse(AI.google_workspace_email_should_match_account("google_contacts", "建立聯絡人 email 是 a@example.com"))  # 逐行註解：Contacts email 不能被誤判成帳號切換。


class GoogleWorkspaceDispatcherTests(unittest.TestCase):  # 逐行註解：Workspace dispatcher routing 測試。
    def patch_function(self, name, replacement):  # 逐行註解：簡單 monkeypatch 函式並自動還原。
        original = getattr(AI, name)  # 逐行註解：保存原函式。
        setattr(AI, name, replacement)  # 逐行註解：替換成測試假函式。
        self.addCleanup(lambda: setattr(AI, name, original))  # 逐行註解：測試結束後還原。

    def test_files_dispatch_routes_docs_sheets_drive_forms_slides(self):  # 逐行註解：驗證檔案 dispatcher 接到正確函式。
        self.patch_function("google_workspace_create_document", lambda *args: "DOC_CREATE")  # 逐行註解：替換 Docs create。
        self.patch_function("google_workspace_update_sheet_cells", lambda *args: "SHEET_UPDATE")  # 逐行註解：替換 Sheets update。
        self.patch_function("google_workspace_create_drive_folder", lambda *args: "DRIVE_FOLDER")  # 逐行註解：替換 Drive folder。
        self.patch_function("google_workspace_create_form", lambda *args: "FORM_CREATE")  # 逐行註解：替換 Forms create。
        self.patch_function("google_workspace_create_slide", lambda *args: "SLIDE_CREATE")  # 逐行註解：替換 Slides create slide。
        self.assertEqual(AI.google_workspace_dispatch_files(1, "a@example.com", "google_doc", ["create"], "建立文件 標題是 Test"), ["DOC_CREATE"])  # 逐行註解：Docs create routing。
        self.assertEqual(AI.google_workspace_dispatch_files(1, "a@example.com", "google_sheet", ["edit"], "A1 = Name"), ["SHEET_UPDATE"])  # 逐行註解：Sheets update routing。
        self.assertEqual(AI.google_workspace_dispatch_files(1, "a@example.com", "google_drive", ["create"], "建立資料夾 標題是 Folder"), ["DRIVE_FOLDER"])  # 逐行註解：Drive folder routing。
        self.assertEqual(AI.google_workspace_dispatch_files(1, "a@example.com", "google_form", ["create"], "建立表單 標題是 Form"), ["FORM_CREATE"])  # 逐行註解：Forms create routing。
        self.assertEqual(AI.google_workspace_dispatch_files(1, "a@example.com", "google_slide", ["create_slide"], "新增投影片 內容是 Slide 1"), ["SLIDE_CREATE"])  # 逐行註解：Slides create slide routing。

    def test_gmail_calendar_contacts_dispatch_routes_new_actions(self):  # 逐行註解：驗證 Gmail、Calendar、Contacts dispatcher。
        self.patch_function("google_workspace_send_gmail_email", lambda *args: "GMAIL_SEND")  # 逐行註解：替換 Gmail send。
        self.patch_function("google_workspace_archive_gmail_message", lambda *args: "GMAIL_ARCHIVE")  # 逐行註解：替換 Gmail archive。
        self.patch_function("google_workspace_update_calendar_event", lambda *args: "CAL_UPDATE")  # 逐行註解：替換 Calendar update。
        self.patch_function("google_workspace_create_contact", lambda *args: "CONTACT_CREATE")  # 逐行註解：替換 Contacts create。
        self.assertEqual(AI.google_workspace_dispatch_gmail(1, "a@example.com", ["send"], "寄信給 b@example.com 內容是 Hi"), ["GMAIL_SEND"])  # 逐行註解：Gmail send routing。
        self.assertEqual(AI.google_workspace_dispatch_gmail(1, "a@example.com", ["archive"], "封存 Message ID:abc"), ["GMAIL_ARCHIVE"])  # 逐行註解：Gmail archive routing。
        self.assertEqual(AI.google_workspace_dispatch_calendar(1, "a@example.com", ["edit"], "行程ID:abc 新標題是會議"), ["CAL_UPDATE"])  # 逐行註解：Calendar update routing。
        self.assertEqual(AI.google_workspace_dispatch_contacts(1, "a@example.com", ["create"], "建立聯絡人 姓名是 Sean email 是 sean@example.com"), ["CONTACT_CREATE"])  # 逐行註解：Contacts create routing。


if __name__ == "__main__":  # 逐行註解：直接執行本檔時跑 unittest。
    unittest.main()  # 逐行註解：啟動測試。
