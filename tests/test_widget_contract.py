import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WidgetContractTests(unittest.TestCase):
    def test_widget_uses_shadow_dom_and_config_endpoint(self):
        source = (ROOT / "frontend/widget.js").read_text(encoding="utf-8")
        self.assertIn("attachShadow", source)
        self.assertIn("/public/widget/", source)
        self.assertIn("data-theme", source)

    def test_preview_page_embeds_widget_script(self):
        source = (ROOT / "frontend/widget-preview.html").read_text(encoding="utf-8")
        self.assertIn("/widget.js", source)
        self.assertIn("data-widget-id", source)

    def test_widget_does_not_expose_stop_or_old_retry_messages(self):
        source = (ROOT / "frontend/widget.js").read_text(encoding="utf-8")
        self.assertNotIn("درخواست متوقف شد.", source)
        self.assertNotIn("فعلاً نتونستم پاسخ را آماده کنم.", source)
        self.assertIn('cache: "no-store"', source)

    def test_widget_endpoints_are_private_and_not_archived(self):
        source = (ROOT / "app/main.py").read_text(encoding="utf-8")
        streaming = (ROOT / "app/services/streaming.py").read_text(encoding="utf-8")
        self.assertIn('"/public/widget/"', source)
        self.assertIn('"X-Robots-Tag"', source)
        self.assertIn('no-store, no-cache, no-transform, private', source)
        self.assertIn('noindex, noarchive, nosnippet', streaming)


if __name__ == "__main__":
    unittest.main()
