"""قرارداد ظاهری دو تم: شب بنفش (تیره) و روز طلایی/زرد (روشن).

این تست‌ها فقط فایل‌های استاتیک را می‌خوانند، پس بدون هیچ وابستگی و بدون دیتابیس اجرا می‌شوند.
"""
import colorsys
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
CSS = (FRONTEND / "assets" / "css" / "style.css").read_text(encoding="utf-8")
PAGES = ("index.html", "dashboard.html", "admin.html", "widget-preview.html")

REQUIRED_TOKENS = {
    "--bg", "--bg-elevated", "--bg-elevated-2", "--bg-input", "--bg-glass", "--overlay",
    "--border", "--border-soft", "--text", "--text-muted", "--text-faint",
    "--accent", "--accent-hover", "--accent-text", "--accent-soft", "--accent-line", "--on-accent",
    "--gold", "--gold-soft", "--grad-brand", "--grad-text",
    "--success", "--success-soft", "--danger", "--danger-soft", "--code-text", "--knob", "--sidebar-bg", "--topbar-bg",
    "--shadow-card", "--shadow-pop", "--shadow-btn", "--glow-a", "--glow-b", "--glow-c",
}


def block(selector):
    match = re.search(re.escape(selector) + r"\s*\{(.*?)\n\}", CSS, re.S)
    assert match, f"{selector} block not found"
    return match.group(1)


def tokens(selector):
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", block(selector)))


def rgb(value):
    value = value.strip()
    assert re.fullmatch(r"#[0-9a-fA-F]{6}", value), value
    return tuple(int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))


def luminance(value):
    def channel(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb(value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def hue_deg(value):
    return colorsys.rgb_to_hls(*rgb(value))[0] * 360


class ThemeTokenTests(unittest.TestCase):
    def setUp(self):
        self.dark = tokens(":root")
        self.light = tokens(':root[data-theme="light"]')

    def test_both_themes_define_every_required_token(self):
        self.assertFalse(REQUIRED_TOKENS - set(self.dark), REQUIRED_TOKENS - set(self.dark))
        self.assertFalse(REQUIRED_TOKENS - set(self.light), REQUIRED_TOKENS - set(self.light))

    def test_nord_amber_and_rose_define_full_distinct_palettes(self):
        palettes = {
            name: tokens(f':root[data-theme="{name}"]')
            for name in ("nord", "amber", "rose")
        }
        for name, palette in palettes.items():
            self.assertFalse(REQUIRED_TOKENS - set(palette), (name, REQUIRED_TOKENS - set(palette)))
            self.assertGreaterEqual(contrast(palette["--text"], palette["--bg"]), 7, name)
            self.assertGreaterEqual(contrast(palette["--text"], palette["--bg-elevated"]), 7, name)
            self.assertGreaterEqual(contrast(palette["--accent-text"], palette["--bg-elevated"]), 4.5, name)
        self.assertTrue(180 <= hue_deg(palettes["nord"]["--accent"]) <= 215, "Nord باید آبی یخی باشد")
        self.assertTrue(25 <= hue_deg(palettes["amber"]["--accent"]) <= 55, "Amber باید کهربایی باشد")
        self.assertTrue(315 <= hue_deg(palettes["rose"]["--accent"]) <= 350, "Rose باید صورتی/رز باشد")

    def test_theme_selection_has_one_shared_authority_and_all_three_presets(self):
        theme_js = (FRONTEND / "assets" / "js" / "theme.js").read_text(encoding="utf-8")
        settings_js = (FRONTEND / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
        dashboard = (FRONTEND / "dashboard.html").read_text(encoding="utf-8")
        for name in ("nord", "amber", "rose"):
            self.assertIn(f'data-theme="{name}"', CSS)
            self.assertIn(f'data-theme-preset="{name}"', dashboard)
            self.assertIn(f'"{name}"', theme_js)
        self.assertIn("window.QZTheme.set(theme", settings_js)
        self.assertIn('setAttribute("aria-pressed"', settings_js)

    def test_dark_theme_matches_gentelella_dna(self):
        self.assertLess(luminance(self.dark["--bg"]), 0.03)
        self.assertTrue(155 <= hue_deg(self.dark["--accent"]) <= 175)
        self.assertEqual(self.dark["--accent"].lower(), "#1abb9c")
        self.assertIn("#169f85", self.dark["--grad-brand"].lower())
        self.assertEqual(self.dark["--sidebar-bg"].lower(), "#1a2332")
        self.assertIn("color-scheme: dark", block(":root"))

    def test_light_theme_matches_gentelella_dna(self):
        self.assertGreater(luminance(self.light["--bg"]), 0.9)
        self.assertGreater(luminance(self.light["--bg-elevated"]), 0.95)
        for name in ("--accent", "--accent-hover"):
            self.assertTrue(155 <= hue_deg(self.light[name]) <= 175, (name, hue_deg(self.light[name])))
        self.assertEqual(self.light["--accent"].lower(), "#1abb9c")
        self.assertIn("#169f85", self.light["--grad-brand"].lower())
        self.assertEqual(self.light["--sidebar-bg"].lower(), "#1a2332")
        self.assertIn("color-scheme: light", block(':root[data-theme="light"]'))

    def test_text_is_readable_in_both_themes(self):
        for name, theme in (("dark", self.dark), ("light", self.light)):
            for surface in ("--bg", "--bg-elevated", "--bg-elevated-2"):
                self.assertGreaterEqual(contrast(theme["--text"], theme[surface]), 7, (name, surface))
            self.assertGreaterEqual(contrast(theme["--text-muted"], theme["--bg-elevated"]), 4.5, name)
            self.assertGreaterEqual(contrast(theme["--text-faint"], theme["--bg-elevated"]), 3.2, name)
            self.assertGreaterEqual(contrast(theme["--accent-text"], theme["--bg-elevated"]), 4.5, name)
            self.assertGreaterEqual(contrast(theme["--danger"], theme["--bg-elevated"]), 3.2, name)
            self.assertGreaterEqual(contrast(theme["--success"], theme["--bg-elevated"]), 3.5, name)

    def test_text_on_primary_buttons_is_readable_in_both_themes(self):
        for name, theme in (("dark", self.dark), ("light", self.light)):
            stops = re.findall(r"#[0-9a-fA-F]{6}", theme["--grad-brand"])
            for stop in stops:
                self.assertGreaterEqual(contrast(theme["--on-accent"], stop), 4.5, (name, stop))


class StylesheetHygieneTests(unittest.TestCase):
    def test_components_use_tokens_not_hardcoded_brand_colours(self):
        body = CSS.split("/* =========================================================================\n   Prismo 2.5", 1)[1]
        # توکن‌های تم را قبل از بررسی کامپوننت‌ها حذف کن؛ رنگ hex در این بلوک‌ها مجاز است.
        body = body.split("/* =========================================================================\n   تنظیمات مرکزی 2.7", 1)[0]
        body = re.sub(r':root(?:\[data-theme="[^"]+"\])?\s*\{.*?\n\}', '', body, flags=re.S)
        leftovers = set(re.findall(r"#[0-9a-fA-F]{3,8}\b", body))
        self.assertFalse(leftovers, f"رنگ ثابت خارج از توکن‌ها: {sorted(leftovers)}")

    def test_old_flat_override_block_is_gone(self):
        self.assertNotIn("v2.3 — مینیمال", CSS)
        outside = [line for line in CSS.splitlines() if "!important" in line and "animation-duration" not in line]
        self.assertEqual(outside, [], "فقط قانون prefers-reduced-motion مجاز به !important است")

    def test_every_token_used_is_defined(self):
        defined = set(tokens(":root"))
        used = set(re.findall(r"var\((--[\w-]+)", CSS))
        self.assertFalse(used - defined, f"توکن تعریف‌نشده: {sorted(used - defined)}")

    def test_fonts_fall_back_to_persian_capable_stack(self):
        mono = tokens(":root")["--font-mono"]
        self.assertLess(mono.index("Vazirmatn"), mono.index("monospace"))


class PageWiringTests(unittest.TestCase):
    def read(self, name):
        return (FRONTEND / name).read_text(encoding="utf-8")

    def test_all_pages_share_one_asset_version(self):
        versions = set()
        for page in PAGES:
            versions.update(re.findall(r"\?v=(\d+\.\d+\.\d+)", self.read(page)))
        self.assertEqual(versions, {"2.7.7"})

    def test_heavy_scripts_are_loaded_on_demand_not_with_the_page(self):
        dashboard = self.read("dashboard.html")
        self.assertRegex(dashboard, r'<script src="/assets/js/shell.js\?v=[\d.]+" defer></script>')
        for script in ("extract.js", "pets.js"):
            self.assertNotIn(f"/assets/js/{script}", dashboard, f"{script} باید با Lazy.script بارگذاری شود نه با صفحه")
        js = (FRONTEND / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
        self.assertIn('Lazy.script("/assets/js/extract.js', js)
        self.assertIn('Lazy.script("/assets/js/pets.js', js)

    def test_fonts_do_not_block_rendering(self):
        for page in ("index.html", "dashboard.html", "admin.html"):
            html = self.read(page)
            self.assertIn('rel="preconnect" href="https://fonts.googleapis.com"', html, page)
            self.assertIn("onload=\"this.media='all'\"", html, page)
        self.assertNotIn("@import", CSS)

    def test_brand_icons_follow_theme_text_colour(self):
        for page in ("index.html", "dashboard.html", "admin.html"):
            self.assertNotIn('stroke="#fff"', self.read(page), page)

    def test_every_page_has_a_theme_toggle_source(self):
        for page in ("index.html", "dashboard.html", "admin.html"):
            self.assertIn("/assets/js/theme.js", self.read(page), page)
        self.assertNotIn('id="themeToggle"', self.read("dashboard.html"))
        js = (FRONTEND / "assets" / "js" / "theme.js").read_text(encoding="utf-8")
        self.assertIn('"qz-theme-change"', js)

    def test_widget_preview_follows_site_theme(self):
        self.assertIn('params.get("theme")', self.read("widget-preview.html"))
        dashboard = (FRONTEND / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
        self.assertIn("theme=${encodeURIComponent(theme)}", dashboard)
        self.assertIn('addEventListener("qz-theme-change"', dashboard)
        self.assertIn("color-scheme: light", CSS.split(".widget-preview-frame", 1)[1].split("}", 1)[0])

    def test_dashboard_badge_matches_release(self):
        self.assertIn("PRISMO 2.7.7", self.read("dashboard.html"))


class PetSpriteContractTests(unittest.TestCase):
    """بلوک اسپرایت‌ها در widget.js و pets.js باید یکسان باشد، وگرنه پیش‌نمایش با ویجت واقعی فرق می‌کند."""

    @staticmethod
    def block(path):
        text = (FRONTEND / path).read_text(encoding="utf-8")
        match = re.search(r"/\*PETS-BEGIN\*/(.*?)/\*PETS-END\*/", text, re.S)
        assert match, path
        return match.group(1)

    def test_widget_and_dashboard_share_identical_sprites(self):
        self.assertEqual(self.block("widget.js").strip(), self.block("assets/js/pets.js").strip())

    def test_every_sprite_frame_is_a_16_column_grid(self):
        import json
        raw = self.block("widget.js").split("=", 1)[1].strip().rstrip(";")
        sprites = json.loads(raw)
        self.assertEqual(set(sprites), {"dog", "cat", "raccoon"})
        for name, spec in sprites.items():
            self.assertEqual(len(spec["body"]), 9, name)
            self.assertEqual(set(spec["legs"]), {"a", "b", "i"}, name)
            for rows in [spec["body"]] + list(spec["legs"].values()):
                for row in rows:
                    self.assertEqual(len(row), 16, (name, row))
                    self.assertRegex(row, r"^[.KBDLPW]+$")


class WidgetThemeTests(unittest.TestCase):
    def setUp(self):
        self.js = (FRONTEND / "widget.js").read_text(encoding="utf-8")

    def test_widget_has_matching_dark_and_light_palettes(self):
        self.assertIn("DARK_VARS", self.js)
        self.assertIn("LIGHT_VARS", self.js)
        self.assertIn("THEME_VARS", self.js)
        for theme in ("ocean", "forest", "sunset", "lavender", "mono"):
            self.assertIn(f"{theme}: ", self.js)
        self.assertIn("--qz-panel:#1a2332", self.js)
        self.assertIn("--qz-bubble:#f9fafb", self.js)

    def test_widget_text_colour_adapts_to_chosen_accent(self):
        self.assertIn("function readableOn", self.js)
        self.assertIn("--qz-on-accent", self.js)
        self.assertNotIn("#6a49f2", self.js, "گرادیان هدر نباید بنفشِ ثابت داشته باشد")
        self.assertNotIn('stroke="#fff"', self.js)

    def test_widget_default_accent_matches_gentelella_teal(self):
        self.assertNotIn("#7C5CFF", self.js)
        self.assertIn("#1ABB9C", self.js)


if __name__ == "__main__":
    unittest.main()
