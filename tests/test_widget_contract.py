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


if __name__ == "__main__":
    unittest.main()
