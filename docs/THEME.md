# Prismo Theme & Frontend Structure

[فارسی](#راهنمای-فارسی) · [English](#english-guide)

<a id="راهنمای-فارسی"></a>

## راهنمای فارسی

این سند معماری رابط کاربری Prismo را توضیح می‌دهد: رنگ‌ها کجا تعریف شده‌اند، تم و زبان چگونه تغییر می‌کنند، کدام فایل‌ها مسئول هر رفتار هستند و چطور می‌توان بدون پراکندگی استایل‌ها، رابط را توسعه داد.

## 1. فایل‌های اصلی رابط

| مسیر | مسئولیت |
|---|---|
| `frontend/index.html` | صفحه‌ی ورود/ثبت‌نام و بارگذاری تنظیم اولیه‌ی تم |
| `frontend/auth-callback.html` | تکمیل callback ورود Google/Supabase |
| `frontend/dashboard.html` | فضای اصلی کاربر، بخش‌ها و تنظیمات سایت |
| `frontend/admin.html` | پنل ادمین؛ در نسخه‌ی فعلی تم آن فقط dark است |
| `frontend/widget-preview.html` | پیش‌نمایش ویجت در داشبورد |
| `frontend/widget.js` | ویجت قابل جاسازی در سایت‌های دیگر؛ استایل آن مستقل از تم داشبورد است |
| `frontend/assets/css/style.css` | استایل عمومی، توکن‌های طراحی، کامپوننت‌ها، layout و responsive rules |
| `frontend/assets/js/theme.js` | اعمال تم، اعتبارسنجی نام تم، نگهداری انتخاب تم و انتشار رویداد تغییر تم |
| `frontend/assets/js/settings.js` | تنظیمات کاربر، ترجمه‌ی رابط، تغییر زبان و جهت RTL/LTR و کنترل‌های تم |
| `frontend/assets/js/shell.js` | رفتار پوسته‌ی داشبورد، سایدبار، breadcrumb و هشدار مدیریتی |
| `frontend/assets/js/dashboard.js` | رفتار بخش‌های داشبورد و فراخوانی APIها |
| `frontend/assets/js/admin.js` | رفتار پنل ادمین |
| `frontend/assets/js/api.js` | توابع مشترک درخواست API و مدیریت خطاها |

## 2. تم چطور اعمال می‌شود؟

تم فعال در ویژگی `data-theme` روی عنصر ریشه‌ی HTML قرار می‌گیرد. برای مثال:

```html
<html data-theme="ocean">
```

در `style.css` توکن‌های پایه داخل `:root` تعریف شده‌اند. تم روشن در `:root[data-theme="light"]` و تم‌های رنگی در selectorهای مشابه برای هر تم override می‌شوند. کامپوننت‌ها باید از توکن‌هایی مانند `var(--bg)`, `var(--text)`, `var(--accent)` و `var(--border)` استفاده کنند؛ نه اینکه رنگ برند را در هر selector دوباره hard-code کنند.

کد `theme.js` فهرست تم‌های مجاز را کنترل می‌کند، مقدار ذخیره‌شده‌ی `qz_theme` را می‌خواند و روی `document.documentElement.dataset.theme` اعمال می‌کند. بعد از تغییر تم، رویداد `qz-theme-change` منتشر می‌شود تا کنترل انتخاب تم بتواند حالت active را به‌روز کند. رابط تنظیمات برای تغییر تم از API مشترک `window.QZTheme.set(...)` استفاده می‌کند تا دو بخش جداگانه مقدار متناقض ننویسند.

### نام تم‌های موجود

| مقدار فنی | نام نمایشی | جهت بصری |
|---|---|---|
| `dark` | تیره کلاسیک | زمینه‌ی slate تیره با accent سبزآبی |
| `light` | روشن کلاسیک | زمینه‌ی روشن و متن تیره با accent سبزآبی |
| `ocean` | اقیانوس | سرمه‌ای عمیق و آبی فیروزه‌ای |
| `forest` | جنگل | سبز تیره و سبز روشن |
| `sunset` | غروب | زمینه‌ی زرشکی/بنفش تیره و accent مرجانی |
| `lavender` | لاوندر | زمینه‌ی بنفش تیره و accent بنفش روشن |
| `mono` | مینیمال | پالت سیاه، سفید و خاکستری |
| `nord` | نورد | slate سرد با accent آبی یخی |
| `amber` | کهربا | قهوه‌ای تیره و accent کهربایی |
| `rose` | رز | زمینه‌ی زرشکی تیره و accent صورتی |

مقدار پیش‌فرض تم `dark` است. انتخاب کاربر در مرورگر با کلید `qz_theme` ذخیره می‌شود. این ترجیح محلی مرورگر است؛ آن را با تنظیمات حساب در دیتابیس اشتباه نگیرید.

## 3. Design tokens مهم

توکن‌ها در بالای `frontend/assets/css/style.css` و بلوک‌های تم تعریف می‌شوند:

| توکن | کاربرد |
|---|---|
| `--bg` | پس‌زمینه‌ی اصلی صفحه |
| `--bg-elevated`, `--bg-elevated-2` | سطح کارت‌ها، پنل‌ها و عناصر ثانویه |
| `--bg-input` | پس‌زمینه‌ی ورودی‌های فرم |
| `--bg-glass`, `--overlay` | سطوح شفاف و لایه‌های پوشاننده |
| `--text`, `--text-muted`, `--text-faint` | متن اصلی، ثانویه و کم‌رنگ |
| `--border`, `--border-soft` | مرزها و جداکننده‌ها |
| `--accent`, `--accent-2`, `--accent-hover`, `--accent-soft`, `--accent-line` | رنگ تعاملی اصلی و حالت‌های آن |
| `--accent-text`, `--on-accent` | متن روی accent یا کنترل‌های accent |
| `--success`, `--danger`, `--gold` و نسخه‌های `*-soft` | وضعیت موفقیت، خطا و تأکید |
| `--sidebar-bg`, `--sidebar-text*`, `--topbar-bg` | رنگ‌های سایدبار و نوار بالا |
| `--grad-brand`, `--grad-text` | گرادیان برند و متن‌های تزئینی |
| `--shadow-card`, `--shadow-pop`, `--shadow-btn` | سایه‌ی کارت، منو و دکمه |
| `--glow-a`, `--glow-b`, `--glow-c` | نورهای تزئینی پس‌زمینه |
| `--font-body`, `--font-mono` | فونت متن رابط و متن monospace |
| `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl` | شعاع گوشه‌ها |

### قانون مهم توسعه

وقتی رنگی برای کل رابط تغییر می‌کند، ابتدا token تم را تغییر بده. از اضافه کردن override سراسری تازه یا `!important` برای جبران ناسازگاری تم خودداری کن. اگر یک کامپوننت جدید اضافه می‌شود، برای آن از توکن‌های معنایی استفاده کن تا در همه‌ی تم‌ها هماهنگ بماند.

## 4. زبان و جهت رابط

تنظیم زبان در `frontend/assets/js/settings.js` مدیریت می‌شود:

- `qz_language` مقدار انتخاب‌شده (`fa` یا `en`) را در مرورگر نگه می‌دارد.
- `document.documentElement.lang` روی `fa` یا `en` قرار می‌گیرد.
- برای فارسی، `dir="rtl"` و برای انگلیسی `dir="ltr"` تنظیم می‌شود.
- کلاس `qz-ltr` روی body فعال می‌شود تا اصلاحات لازم برای layout انگلیسی اعمال شوند.
- یک واژه‌نامه‌ی داخلی عبارت‌های رابط را ترجمه می‌کند و `MutationObserver` متن‌های جدیدی را که بعداً وارد DOM می‌شوند نیز بررسی می‌کند.
- فیلدها، کدها، پیام‌های کاربر و محتوای مشخص‌شده به‌عنوان محتوای کاربر از ترجمه‌ی خودکار کنار گذاشته می‌شوند تا متن اصلی آن‌ها آسیب نبیند.

این یک لایه‌ی سبک بومی‌سازی داخلی است، نه یک سیستم i18n خارجی کامل. عبارت‌هایی که در واژه‌نامه یا الگوی ترجمه پوشش داده نشده‌اند ممکن است ترجمه نشوند؛ بنابراین برای افزودن متن جدید، ترجمه‌ی فارسی و انگلیسی آن را همراه با رابط اضافه و آزمایش کنید.

## 5. رفتارهای ویژه

- **پنل ادمین:** بدنه‌ی `admin.html` دارای `data-admin-dark-only` است؛ بنابراین `theme.js` تم `dark` را اعمال می‌کند و این صفحه مانند داشبورد کاربر همه‌ی ده تم را انتخاب نمی‌کند.
- **مرکز تنظیمات:** `data-theme-settings-center` مانع ساخته‌شدن دکمه‌ی شناور قدیمی تم می‌شود. تغییر تم از بخش تنظیمات انجام می‌شود.
- **Reduced motion:** CSS به `prefers-reduced-motion: reduce` احترام می‌گذارد. تنظیمات رابط نیز گزینه‌ی کاهش حرکت را ارائه می‌کند.
- **کنتراست:** گزینه‌ی کنتراست بالا، کلاس `qz-high-contrast` را برای بهبود مرزها و متن‌های ثانویه به کار می‌برد.
- **فونت‌ها:** Vazirmatn و JetBrains Mono از Google Fonts به شکل غیرمسدودکننده بارگذاری می‌شوند و در صورت در دسترس نبودن، fallbackهایی مثل Tahoma و Consolas تعریف شده‌اند.
- **ویجت جاسازی‌شده:** تم داشبورد با تم ویجت یکی نیست. ویجت تنظیم مستقل خود را دارد و کد embed می‌تواند از تم خودکار، روشن یا تیره استفاده کند؛ رنگ اصلی ویجت نیز از تنظیمات ویجت می‌آید.

## 6. افزودن تم جدید

برای اضافه کردن تم جدید، همه‌ی نقاط زیر را هماهنگ کن؛ تغییر CSS به‌تنهایی کافی نیست:

1. مقدار جدید را به آرایه‌ی `THEMES` در `frontend/assets/js/theme.js` اضافه کن.
2. همان مقدار را به `allowedThemes` در `frontend/assets/js/settings.js` اضافه کن.
3. یک بلوک `:root[data-theme="NEW_NAME"]` در `style.css` بساز و توکن‌های پایه‌ی هر تم را تعریف کن.
4. کارت انتخاب تم را در `frontend/dashboard.html` با `data-theme-preset="NEW_NAME"` اضافه کن.
5. preview آن را با کلاس متناظر مانند `.theme-preview-NEW_NAME` و در صورت نیاز dot اضافه کن.
6. متن نام تم را در واژه‌نامه‌ی فارسی/انگلیسی `settings.js` اضافه کن.
7. بررسی کن `color-scheme`, متن، border، status colors، دکمه‌ی اصلی و focus-visible در آن تم خوانا باشند.
8. asset version را در ارجاعات HTML تغییر بده تا مرورگر فایل CSS/JS جدید را از کش قدیمی نخواند.
9. تست‌های مربوط به token parity/theme contract را اجرا و همه‌ی ده تم و حالت RTL/LTR را دستی بررسی کن.

نمونه‌ی selector:

```css
:root[data-theme="new-theme"] {
  color-scheme: dark;
  --bg: #101820;
  --bg-elevated: #1b2733;
  --bg-elevated-2: #15212c;
  --text: #eaf1f7;
  --text-muted: #b4c2ce;
  --text-faint: #8999a7;
  --border: rgba(180, 210, 230, .14);
  --border-soft: rgba(180, 210, 230, .08);
  --accent: #50c8b5;
  --accent-hover: #70ddcb;
  --accent-text: #70ddcb;
  --accent-soft: rgba(80, 200, 181, .14);
  --accent-line: rgba(80, 200, 181, .3);
}
```

این فقط الگوست؛ برای تم واقعی باید سایر توکن‌های مورد استفاده در کامپوننت‌ها هم تعریف شوند و کنتراست رنگ‌ها آزمایش شود.

## 7. تست و عیب‌یابی تم

- اگر انتخاب ذخیره نمی‌شود، در Developer Tools بررسی کن که `localStorage` قابل دسترسی باشد و مقدار `qz_theme` یکی از ده مقدار مجاز باشد.
- اگر کارت تم active نمی‌شود، رویداد `qz-theme-change` و مقدار `data-theme-preset` را بررسی کن.
- اگر یک کامپوننت در تم تازه رنگ قدیمی دارد، در `style.css` دنبال color literal یا selector خاصی بگرد که از token استفاده نمی‌کند.
- اگر صفحه‌ی انگلیسی هنوز راست‌چین است، مقدار `qz_language`, مقدار `document.documentElement.dir` و کلاس `qz-ltr` را بررسی کن.
- اگر تم widget با داشبورد فرق دارد، تنظیمات widget/embed را بررسی کن؛ آن را با `qz_theme` داشبورد یکی در نظر نگیر.

---

<a id="english-guide"></a>

## English guide

This document describes Prismo's frontend structure and theme system: where colors live, how theme and language changes work, which files own each behavior, and how to add a theme without scattering hard-coded styles.

### Main files

| Path | Responsibility |
|---|---|
| `frontend/index.html` | Login/registration page and initial theme setup |
| `frontend/auth-callback.html` | Google/Supabase auth callback |
| `frontend/dashboard.html` | User dashboard and settings panels |
| `frontend/admin.html` | Admin UI; forced to the dark theme in the current implementation |
| `frontend/widget-preview.html` | Dashboard widget preview |
| `frontend/widget.js` | Embeddable widget, styled independently from the dashboard |
| `frontend/assets/css/style.css` | Design tokens, component styles, layouts, responsive rules |
| `frontend/assets/js/theme.js` | Theme application, validation, persistence, and change events |
| `frontend/assets/js/settings.js` | Preferences, lightweight translations, language direction, theme controls |
| `frontend/assets/js/shell.js` | Sidebar shell, breadcrumb, and admin threat banner |
| `frontend/assets/js/dashboard.js` | Dashboard interactions and API calls |
| `frontend/assets/js/admin.js` | Admin panel interactions |
| `frontend/assets/js/api.js` | Shared API-request helpers and error handling |

### How themes work

The active theme is stored in `data-theme` on the root HTML element. `style.css` declares shared design tokens in `:root`, then overrides them for `:root[data-theme="light"]` and each named palette. Components should use semantic variables such as `var(--bg)`, `var(--text)`, `var(--accent)`, and `var(--border)` rather than hard-coded brand colors.

`theme.js` validates the selected name against its allowed list, reads/writes the `qz_theme` browser-storage key, updates `document.documentElement.dataset.theme`, and dispatches `qz-theme-change`. `settings.js` uses the shared `window.QZTheme.set(...)` API so the settings panel and global shell do not independently write conflicting theme state.

Available values: `dark`, `light`, `ocean`, `forest`, `sunset`, `lavender`, `mono`, `nord`, `amber`, and `rose`. The default is `dark`. The saved value is a browser preference, not a per-user database setting.

### Important design tokens

- `--bg`, `--bg-elevated`, `--bg-elevated-2`, `--bg-input`: background surfaces
- `--text`, `--text-muted`, `--text-faint`: text hierarchy
- `--border`, `--border-soft`: dividers and component borders
- `--accent`, `--accent-hover`, `--accent-soft`, `--accent-line`: primary interaction color
- `--success`, `--danger`, `--gold` and their soft variants: status colors
- `--sidebar-*`, `--topbar-bg`: navigation surfaces
- `--grad-brand`, `--grad-text`: brand gradients
- `--shadow-*`, `--glow-*`: depth and background decoration
- `--font-body`, `--font-mono`, `--radius-*`: typography and shape tokens

Edit tokens first when changing a palette. Avoid a new global override or unnecessary `!important` rules. New components should use the shared tokens so they remain compatible across themes.

### Language and direction

`settings.js` stores the language in `qz_language`, sets `document.documentElement.lang`, switches `dir` between `rtl` and `ltr`, toggles `qz-ltr`, and translates known UI strings through an internal dictionary. A `MutationObserver` also checks newly-rendered UI. This is a lightweight in-project translation layer rather than a full external i18n framework; new user-facing strings should be added to both languages and tested.

### Special cases

- `admin.html` uses `data-admin-dark-only`, so the admin page is forced to `dark` in the current implementation.
- `data-theme-settings-center` prevents the legacy floating theme toggle; users change the dashboard theme in Settings.
- CSS honors `prefers-reduced-motion`; the UI also exposes reduced-motion and high-contrast preferences.
- Vazirmatn and JetBrains Mono are loaded non-blockingly from Google Fonts with local font fallbacks.
- The embeddable widget has its own appearance settings (auto/light/dark plus its configured accent); it does not simply inherit the dashboard's `qz_theme`.

### Adding a theme

1. Add the name to `THEMES` in `theme.js` and `allowedThemes` in `settings.js`.
2. Define all required design tokens in `style.css` under `:root[data-theme="NEW_NAME"]`.
3. Add a preset button in `dashboard.html` using `data-theme-preset`.
4. Add a preview style and localized theme label.
5. Check text, controls, borders, status colors, keyboard focus, and contrast in RTL and LTR.
6. Bump static asset versions in HTML so browsers do not keep stale CSS/JS.
7. Run theme contract tests and manually verify all themes.

### Troubleshooting

- Check `localStorage.qz_theme` and make sure it is one of the allowed values.
- If a preset does not highlight, inspect `qz-theme-change` and its `data-theme-preset` value.
- If a component ignores the palette, search `style.css` for hard-coded colors or a more specific selector overriding tokens.
- If English remains RTL, inspect `qz_language`, `document.documentElement.dir`, and `qz-ltr`.
- If the embedded widget looks different, review widget/embed appearance options instead of the dashboard theme key.
