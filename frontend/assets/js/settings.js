/* Prismo Settings + global i18n layer — v2.7.5 */
(function () {
  "use strict";

  var SETTINGS_KEY = "qz_site_settings_v272";
  var LANGUAGE_KEY = "qz_language";
  var THEME_KEY = "qz_theme";
  var SETTINGS_TAB_KEY = "qz_settings_tab";
  var root = document.documentElement;
  var body = document.body;

  var defaults = {
    language: "fa",
    theme: "dark",
    streaming: true,
    autoScroll: true,
    responseSound: false,
    reducedMotion: false,
    compactSidebar: false,
    compactChat: false,
    highContrast: false,
    rememberView: true,
    rememberRail: true,
    rememberTab: true,
    chatEnterSend: true,
    showModelBadge: true,
    confirmClearChat: true,
    keyboardShortcuts: true,
  };

  var dict = {
    "خانه":"Home", "فاز اول":"Core", "اتصال مدل هوش مصنوعی":"AI model connection", "دانشنامه":"Knowledge base", "شخصی‌سازی رفتار":"Behavior & RAG", "آزمایشگاه تست":"Test lab", "ویجت و کد امبد":"Widget & embed", "تنظیمات":"Settings", "مدیریت":"Administration", "پنل ادمین":"Admin panel",
    "حساب من":"My account", "مدیر سیستم":"System admin", "کاربر":"User", "سیستم آماده":"System ready", "قدم بعدی چیه؟":"What’s next?", "افزودن سند به دانشنامه":"Add a knowledge document", "تست گفت‌وگو با RAG":"Test RAG chat", "گرفتن کد ویجت":"Get widget code",
    "سلام 👋":"Hello 👋", "یک نگاه سریع به وضعیت دستیار هوشمند و دانشنامه‌ات":"A quick look at your AI assistant and knowledge base", "اسناد دانشنامه":"Knowledge documents", "تکه‌های ایندکس‌شده":"Indexed chunks", "پیام‌های ثبت‌شده":"Logged messages", "نشست‌های آزمایشگاه":"Lab sessions", "نشست‌های ویجت":"Widget sessions", "ارائه‌دهنده‌ی مدل":"Model provider", "وضعیت سرویس":"Service status", "وضعیت فعلی ویجت و حساب کاربری را از API داشبورد می‌خوانیم.":"Current widget and account status from the dashboard API.", "فعال":"Active", "غیرفعال":"Offline",
    "مدل هوش مصنوعی":"AI models", "یک اتصال انتخاب کن و مدل‌ها را تنظیم کن.":"Choose a connection and configure your models.", "اتصال":"Connection", "مقایسه‌ی مدل‌ها":"Model battle", "منبع مدل":"Model source", "مدل‌های رایگان آماده یا API سازگار با OpenAI.":"Ready-to-use models or an OpenAI-compatible API.", "مدل‌های آماده":"Ready models", "رایگان آماده":"Ready-to-use", "API اختصاصی":"Custom API", "مدل چت":"Chat model", "مدل Embedding":"Embedding model", "ذخیره":"Save", "تست اتصال":"Test connection", "Base URL":"Base URL", "API Key":"API key", "دریافت مدل‌ها":"Discover models", "مدل embedding سازگار با پروژه پیدا نشد.":"No compatible embedding model was found.",
    "دانشنامه (Knowledge Base)":"Knowledge base", "اسناد و اطلاعاتی که دستیار هوشمند تو، پاسخ‌ها را از روی آن‌ها می‌سازد.":"Documents and information your assistant uses to answer.", "افزودن سند جدید":"Add document", "آپلود فایل":"Upload file", "حذف کامل دانشنامه":"Clear knowledge base", "فایل‌ها را اینجا رها کن یا کلیک کن":"Drop files here or click", "افزودن سند جدید بزن تا اولین سندت را وارد کنی.":"Add your first document.",
    "شخصی‌سازی رفتار دستیار":"Assistant behavior", "نقش، لحن و پارامترهای بازیابی از دانشنامه را تنظیم کن.":"Tune the role, tone, and retrieval parameters.", "پرامپت سیستمی (نقش و لحن دستیار)":"System prompt (role & tone)", "Temperature (میزان خلاقیت پاسخ)":"Temperature (creativity)", "Top-K (تعداد تکه‌ی بازیابی‌شده از دانشنامه)":"Top-K (retrieved chunks)", "Similarity Threshold (حداقل شباهت)":"Similarity threshold", "ذخیره‌ی تنظیمات":"Save settings",
    "آزمایشگاه تست داخلی":"Internal test lab", "قبل از انتشار ویجت، پاسخ‌گویی و RAG را همین‌جا امتحان کن.":"Test RAG and responses here before publishing the widget.", "گفت‌وگوی جدید":"New chat", "جست‌وجوی معنایی (Playground)":"Semantic search (Playground)", "تست گفت‌وگو":"Chat test", "یک سؤال درباره‌ی دانشنامه‌ات بپرس.":"Ask a question about your knowledge base.", "منابع بازیابی‌شده":"Retrieved sources", "هنوز سؤالی پرسیده نشده.":"No question asked yet.", "شروع گفت‌وگوی جدید":"Start new chat", "جست‌وجو":"Search", "نتیجه‌ای یافت نشد":"No results found", "پاسخ متوقف شد.":"Response stopped.", "در حال آماده‌سازی پاسخ…":"Preparing response…", "در حال پاسخ…":"Responding…", "ارسال":"Send", "توقف پاسخ":"Stop response",
    "ویجت و کد جاسازی":"Widget & embed", "ظاهر و رفتار ویجت را تنظیم کن؛ پیش‌نمایش سمت چپ همان لحظه عوض می‌شود.":"Configure the widget; the live preview updates instantly.", "ظاهر":"Appearance", "حیوان خانگی":"Pet", "گفت‌وگو":"Chat", "عنوان ویجت":"Widget title", "پیام خوش‌آمدگویی":"Welcome message", "رنگ اصلی":"Primary color", "محل ویجت روی صفحه":"Widget position", "پایین چپ":"Bottom left", "پایین راست":"Bottom right", "حیوان خانگی پیکسلی":"Pixel pet", "رنگ حیوان":"Pet color", "پیام تیزر":"Teaser message", "پاسخ‌های سریع (حداکثر ۴ مورد)":"Quick replies (max 4)", "ذخیره‌ی تغییرات":"Save changes", "پیش‌نمایش زنده":"Live preview", "ویجت واقعی؛ حتی قبل از ذخیره.":"Real widget preview, even before saving.", "بازنشانی":"Reset", "کد جاسازی":"Embed code", "کپی کد":"Copy code", "خودکار":"Auto", "روشن":"Light", "تیره":"Dark",
    "حساب کاربری":"Account", "اطلاعات حساب همین‌جا مدیریت می‌شود؛ نام و آیکونت همچنان پایین منوی کناری است.":"Manage your account here; your name and avatar stay at the bottom of the sidebar.", "نام کاربری":"Username", "نام سازمان":"Organization", "نقش":"Role", "وضعیت":"Status", "خروج از حساب":"Sign out",
    "مرکز کنترل":"Control center", "ذخیره محلی":"Saved locally", "تنظیمات سایت":"Site settings", "زبان، ظاهر، رفتار پاسخ‌ها، تجربه کاربری و حساب را از یکجا کنترل کن.":"Control language, appearance, response behavior, UX, and your account from one place.", "زبان و جهت صفحه":"Language & direction", "با انتخاب English، رابط کاربری کاملاً چپ‌چین می‌شود.":"Choosing English switches the interface fully to left-to-right.", "فارسی":"Persian", "راست‌چین":"Right to left", "Left to right":"Left to right", "رنگ و حال‌وهوای محیط":"Theme & atmosphere", "۱۰ پوسته‌ی آماده با ذخیره‌سازی فوری.":"Ten ready-made themes with instant saving.", "روشن کلاسیک":"Classic light", "تیره کلاسیک":"Classic dark", "اقیانوس":"Ocean", "جنگل":"Forest", "غروب":"Sunset", "لاوندر":"Lavender", "مینیمال":"Minimal", "نورد":"Nord", "آبی سرد و آرام":"Cool, calm blue", "کهربا":"Amber", "گرم با حس ترمینال قدیمی":"Warm, retro terminal", "رز":"Rose", "صورتی تیره و شیک":"Elegant dark rose",
    "رفتار پاسخ":"Response behavior", "این گزینه مستقیماً روی چت داخلی داشبورد اعمال می‌شود.":"These options directly affect the dashboard chat.", "نمایش تکه‌تکه‌ی پاسخ":"Stream the answer", "پاسخ مدل هم‌زمان با رسیدن توکن‌ها نمایش داده شود.":"Show the response as tokens arrive.", "اسکرول خودکار گفتگو":"Auto-scroll chat", "هنگام دریافت پاسخ، پایین گفتگو را دنبال کند.":"Keep the latest response in view.", "هشدار صوتی پایان پاسخ":"Response sound", "بعد از تمام شدن پاسخ، یک صدای کوتاه پخش شود.":"Play a short sound when a response finishes.", "ارسال با Enter":"Send with Enter", "با Enter ارسال کن و با Shift+Enter خط جدید بساز.":"Send with Enter and use Shift+Enter for a new line.", "نمایش نشان مدل":"Show model badge", "مدل فعال کنار پاسخ‌ها نمایش داده شود.":"Show the active model next to responses.", "چیدمان فشرده چت":"Compact chat", "فاصله‌ها و حباب‌های پیام کمی جمع‌وجورتر شوند.":"Use tighter spacing and more compact message bubbles.", "تأیید پاک‌کردن گفتگو":"Confirm clear chat", "قبل از پاک‌کردن یا شروع گفت‌وگوی تازه تأیید بگیر.":"Ask for confirmation before clearing or starting a new chat.",
    "تجربه کاربری":"User experience", "جزئیاتی که روی سرعت حس‌شده و کار با پنل اثر می‌گذارند.":"Controls that affect perceived speed and usability.", "حالت کم‌تحرک":"Reduced motion", "انیمیشن‌ها و حرکت‌های غیرضروری را کاهش می‌دهد.":"Reduce non-essential motion.", "سایدبار فشرده":"Compact sidebar", "منوی کناری را به حالت آیکونی کوچک می‌کند.":"Use an icon-only sidebar.", "کنتراست بیشتر":"High contrast", "مرزها و متن‌های کم‌رنگ را خواناتر می‌کند.":"Increase border and muted-text contrast.",
    "حافظه و حریم تجربه":"Local preferences", "تنظیمات شخصی این مرورگر در همین دستگاه ذخیره می‌شوند.":"Personal preferences are stored locally on this device.", "بازگردانی آخرین بخش":"Remember last section", "پس از ورود دوباره، همان بخش قبلی باز شود.":"Reopen the last section after signing in.", "بازگردانی اندازه منو":"Remember sidebar", "وضعیت باز/بسته بودن سایدبار حفظ شود.":"Remember the sidebar size/state.", "آخرین تب تنظیمات":"Remember settings tab", "آخرین تب تنظیمات بازشده حفظ شود.":"Remember the last settings tab.", "میانبرهای صفحه‌کلید":"Keyboard shortcuts", "برای کارهای پرتکرار سریع‌تر از میانبرها استفاده کن.":"Use shortcuts for frequent actions.", "فعال‌سازی میانبرها":"Enable shortcuts", "بازنشانی تنظیمات سایت":"Reset site settings",
    "ظاهر":"Appearance", "پوسته‌ها":"Themes", "زبان":"Language", "چت":"Chat", "فضای کاری":"Workspace", "حساب":"Account", "میانبرها":"Shortcuts", "تنظیمات پیشرفته":"Advanced settings",
    "Ctrl/⌘ + Shift + N":"Ctrl/⌘ + Shift + N", "Ctrl/⌘ + K":"Ctrl/⌘ + K", "Ctrl/⌘ + ,":"Ctrl/⌘ + ,", "Ctrl/⌘ + Shift + Delete":"Ctrl/⌘ + Shift + Delete", "Esc":"Esc",
    "ساخت یک گفت‌وگوی تازه":"Start a new chat", "تمرکز روی کادر پیام":"Focus the message box", "باز کردن تنظیمات":"Open settings", "پاک‌کردن / شروع چت تازه":"Clear / start a new chat", "بستن پنجره یا سایدبار":"Close modal or sidebar",
    "بازگشت":"Back", "نمایش":"View", "ذخیره تغییرات":"Save changes", "ثبت":"Save", "بستن":"Close", "لغو":"Cancel", "تلاش دوباره":"Retry", "خطا در بارگذاری ویجت":"Widget loading error", "مشاهده":"View", "بررسی":"Review",
    "کل کاربران":"Total users", "کاربران فعال":"Active users", "کاربران مسدود":"Blocked users", "مدیران سیستم":"System admins", "کل نشست‌های گفت‌وگو":"Total chat sessions", "کل پیام‌ها":"Total messages", "نشست‌های ویجت عمومی":"Public widget sessions", "نشست‌های آزمایشگاه تست":"Test lab sessions", "پیام‌های علامت‌گذاری‌شده":"Flagged messages", "مواردِ بررسی‌نشده":"Unresolved items", "مسدودسازی":"Block", "رفع مسدودیت":"Unblock", "ورود به‌جای کاربر":"Sign in as user", "بازرسی":"Inspect", "تنزل به کاربر عادی":"Downgrade to user", "ارتقا به ادمین":"Promote to admin", "مدل رایگان آماده":"Ready free model", "کلید ثبت‌شده":"Key configured", "بدون کلید":"No key", "دستیار هوشمند":"Smart Assistant", "سلام! چطور می‌تونم کمکتون کنم؟":"Hello! How can I help you?",
    "سندی ثبت نشده.":"No documents yet.", "نشستی ثبت نشده.":"No sessions yet.", "هنوز مکالمه‌ای ثبت نشده.":"No conversations yet.", "موردی برای بررسی نیست":"Nothing to review", "بستن":"Close", "هشدار بحرانی":"Critical alert", "هشدار با شدت بالا":"High severity alerts", "شدت متوسط":"Medium severity", "تلاش برای گرفتن سیستم‌پرامپت":"Prompt extraction attempts", "ویجت عمومی":"Public widget", "آزمایشگاه":"Test lab", "آزمایشگاه تست":"Test lab", "مشکوک":"Flagged", "بررسی‌شده":"Resolved", "مشاهده‌ی گفت‌وگو":"View conversation", "مسدودکردن کاربر":"Block user", "بررسی شد":"Mark reviewed", "بازرسی کاربر":"Inspect user", "پیام‌های نشست":"Session messages", "نام کاربری":"Username", "نقش فعلی":"Current role", "ارائه‌دهنده‌ی مدل":"Model provider", "مدل چت / امبدینگ":"Chat / embedding model", "پرامپت سیستمی اختصاصی کاربر":"User system prompt", "تنزل به کاربر عادی":"Demote to user", "ارتقا به ادمین":"Promote to admin",
    "سرویس موقتاً در دسترس نیست.":"The service is temporarily unavailable.", "سرویس موقتاً در دسترس نیست":"The service is temporarily unavailable.", "ارتباط با سرویس قطع شد.":"The connection to the service was interrupted.", "ارتباط با سرور برقرار نشد. مطمئن شوید بک‌اند در حال اجراست.":"Could not connect to the server. Make sure the backend is running.", "نشست شما منقضی شده؛ دوباره وارد شوید.":"Your session has expired. Please sign in again.", "کاربر یافت نشد.":"User not found.", "این بخش فقط برای مدیر سیستم در دسترس است.":"This section is available only to system administrators.", "این نام کاربری قبلاً ثبت شده است.":"This username is already registered.", "نام کاربری یا رمز عبور اشتباه است.":"Incorrect username or password.", "حساب کاربری شما مسدود شده است.":"Your account is blocked.", "ویجت یافت نشد.":"Widget not found.", "تعداد درخواست‌ها زیاد است. چند لحظه بعد دوباره تلاش کنید.":"Too many requests. Please try again in a moment.",
    "ایجاد حساب":"Create account", "ورود":"Sign in", "رمز عبور":"Password", "حداقل ۶ کاراکتر":"At least 6 characters", "ساخت حساب و شروع":"Create account and start", "ورود به حساب":"Sign in", "نام سازمان / برند شما (اختیاری)":"Organization / brand name (optional)", "هر کاربر، دانشنامه و ویجتِ کاملاً مجزا و اختصاصیِ خودش را دارد.":"Each user has an isolated knowledge base and widget.", "Prismo را چطور اجرا کنیم؟":"How should Prismo run?", "برای این اجرا یکی را انتخاب کن.":"Choose how to run this instance.", "کاملاً لوکال":"Fully local", "سریع‌ترین حالت":"Fastest", "Supabase":"Supabase", "ابری":"Cloud", "در حال تنظیم اجرای کاملاً لوکال…":"Configuring local mode…", "در حال تنظیم اتصال Supabase…":"Configuring Supabase…",
  };

  // Additional static/admin/dashboard phrases. Keeping them in the same dictionary
  // makes dynamic HTML generated after page load obey the exact same locale.
  Object.assign(dict, {
    "پنل مدیریت — Prismo":"Prismo — Admin panel", "آمار کلان":"Overview", "مدیریت کاربران":"User management", "گزارش مکالمات":"Conversation reports", "نظارت امنیتی":"Security monitoring", "بازگشت به داشبورد کاربری":"Back to user dashboard", "مدیر سیستم":"System admin", "باز و بسته‌کردن منو":"Toggle menu", "مسیر صفحه":"Breadcrumb", "تغییر حالت نمایش":"Toggle appearance",
    "آمار کلان و تله‌متری سیستم":"System overview & telemetry", "یک نگاه کلی به وضعیت پلتفرم در سطح تمام کاربران.":"A platform-wide view across all users.", "مدیریت و پایش کاربران":"User management & monitoring", "لیست تمام کاربران ثبت‌نام‌شده، مسدودسازی، تغییر نقش و بازرسی حساب.":"All registered users, blocking, role changes, and account inspection.", "جست‌وجو بر اساس نام کاربری یا سازمان…":"Search by username or organization…", "کاربر":"User", "اسناد":"Documents", "نشست‌ها":"Sessions", "ثبت‌نام":"Registered", "عملیات":"Actions",
    "گزارش جامع مکالمات":"Conversation reports", "مکالمات کاربران (چه از آزمایشگاه تست، چه از ویجت عمومی) را برای نظارت بر کیفیت پاسخ‌ها بررسی کن.":"Review user conversations from the test lab and public widget to monitor response quality.", "همه":"All", "بازدیدکننده":"Visitor", "تعداد پیام":"Messages", "تاریخ":"Date", "منبع":"Source", "فیلتر شدت":"Severity filter", "همه شدت‌ها":"All severities", "بحرانی":"Critical", "بالا":"High", "متوسط":"Medium", "بررسی‌نشده":"Unresolved",
    "نظارت امنیتی":"Security monitoring", "تلاش برای گرفتن سیستم‌پرامپت، نادیده‌گرفتن دستورها و دورزدن محدودیت‌ها همین‌جا و به‌صورت زنده نشان داده می‌شود.":"Prompt extraction attempts, instruction bypassing, and other security signals appear here in real time.", "بررسی‌نشده":"Unresolved", "بازرسی کاربر":"Inspect user", "پیام‌های نشست":"Session messages",
    "کل کاربران":"Total users", "کاربران فعال":"Active users", "کاربران مسدود":"Blocked users", "مدیران سیستم":"System admins", "اسناد دانشنامه":"Knowledge documents", "تکه‌های ایندکس‌شده":"Indexed chunks", "کل نشست‌های گفت‌وگو":"Total chat sessions", "کل پیام‌ها":"Total messages", "نشست‌های ویجت عمومی":"Public widget sessions", "نشست‌های آزمایشگاه تست":"Test lab sessions", "پیام‌های علامت‌گذاری‌شده":"Flagged messages", "مواردِ بررسی‌نشده":"Unresolved items",
    "فعال":"Active", "مسدود":"Blocked", "ادمین":"Admin", "تکه":"chunks", "بازدیدکننده":"Visitor", "وارد حساب این کاربر شوی؟ می‌تونی بعداً به پنل ادمین برگردی.":"Sign in as this user? You can return to the admin panel later.", "نقش کاربر تغییر کرد.":"User role updated.", "کاربر مسدود شد.":"User blocked.", "مسدودیت کاربر رفع شد.":"User unblocked.", "مورد به‌عنوان بررسی‌شده علامت‌گذاری شد.":"Item marked as reviewed.",
    "این کاربر مسدود شود؟ دسترسی او به پنل و ویجتش بلافاصله قطع می‌شود.":"Block this user? Their dashboard and widget access will be disabled immediately.", "نمی‌توانید حساب خودتان را مسدود کنید.":"You cannot block your own account.", "حداقل یک مدیر فعال باید در سیستم باقی بماند.":"At least one active administrator must remain.", "وارد حساب این کاربر شوی؟ می‌تونی بعداً به پنل ادمین برگردی.":"Sign in as this user? You can return to the admin panel later.",
    "بازرسی:":"Inspect:", "نقش فعلی":"Current role", "مدیر سیستم":"System admin", "کاربر عادی":"Regular user", "ارائه‌دهنده‌ی مدل":"Model provider", "مدل رایگان آماده":"Ready free model", "اتصال اختصاصی":"Custom connection", "کلید ثبت‌شده":"Key configured", "بدون کلید":"No key", "مدل چت / امبدینگ":"Chat / embedding model", "پرامپت سیستمی اختصاصی کاربر":"User system prompt", "نشست‌های گفت‌وگو":"Chat sessions", "نشست‌های گفت‌وگو (":"Chat sessions (", "سندی ثبت نشده.":"No documents yet.", "نشستی ثبت نشده.":"No sessions yet.", "ویجت عمومی":"Public widget", "آزمایشگاه تست":"Test lab", "مشاهده":"View", "ورود به‌جای این کاربر":"Sign in as this user", "تنزل به کاربر عادی":"Demote to regular user", "ارتقا به ادمین":"Promote to admin",
    "هشدار بحرانی":"Critical alert", "هشدار با شدت بالا":"High severity alerts", "شدت متوسط":"Medium severity", "تلاش برای گرفتن سیستم‌پرامپت":"Prompt extraction attempts", "مسدودکردن کاربر":"Block user", "بررسی شد":"Mark reviewed", "موردی برای بررسی نیست":"Nothing to review", "مشکوک":"Flagged", "بررسی‌شده":"Resolved", "مشاهده‌ی گفت‌وگو":"View conversation", "آخرین:":"Latest:", "کاربر:":"User:", "منبع:":"Source:",
    "مدل هوش مصنوعی":"AI models", "یک اتصال انتخاب کن و مدل‌ها را تنظیم کن.":"Choose a connection and configure your models.", "اتصال":"Connection", "مقایسه‌ی مدل‌ها":"Model battle", "منبع مدل":"Model source", "مدل‌های آماده":"Ready models", "رایگان آماده":"Ready-to-use", "API اختصاصی":"Custom API", "کلید مدل چت و embedding":"Shared chat + embedding API key", "همان API Key چت":"Use the same chat API key", "API Key جداگانه":"Separate API keys", "اعتبار اتصال Embedding":"Embedding connection", "در حالت جدا، Base URL و API Key embedding مستقل بررسی می‌شوند.":"Separate mode checks the embedding Base URL and API key independently.", "مدل چت تأییدشده":"Verified chat model", "مدل Embedding تأییدشده":"Verified embedding model", "فقط مدل‌هایی نمایش داده می‌شوند که واقعاً endpoint مربوطه را پاسخ دهند و ابعاد embedding آن‌ها با پروژه برابر باشد.":"Only models that actually answer the relevant endpoint and match the project embedding dimensions are shown.", "مقایسه‌ی مدل‌های آماده":"Ready-model comparison", "یک پرامپت را هم‌زمان به دو مدل رایگان بفرست.":"Send the same prompt to two ready models at once.", "مدل اول":"First model", "مدل دوم":"Second model", "پرامپت آزمایشی":"Test prompt", "شروع مقایسه":"Start comparison",
    "آپلود فایل":"Upload file", "انتخاب یا رها کردن فایل":"Choose or drop a file", "فایل‌ها را اینجا رها کن یا کلیک کن":"Drop files here or click", "افزودن سند جدید":"Add document", "ذخیره و ایندکس‌کردن":"Save & index", "در حال آماده‌سازی سند…":"Preparing document…", "افزودن سند جدید بزن تا اولین سندت را وارد کنی.":"Add a new document to get started.", "حذف کامل دانشنامه":"Clear knowledge base", "در حال بارگذاری…":"Loading…", "پیش‌نمایش ویجت":"Widget preview", "رنگ اصلی ویجت":"Widget primary color", "رنگ‌های آماده":"Presets", "انتخاب حیوان":"Choose a pet", "مثلاً: ساعت کاری؟":"e.g. What are your opening hours?", "مثلاً: هزینه ارسال":"e.g. What is the shipping cost?", "اختیاری":"Optional", "این‌ها به‌شکل دکمه زیر پیام خوش‌آمدگویی دیده می‌شوند و بعد از اولین پیام مخفی می‌شوند.":"These appear as buttons below the welcome message and hide after the first message.", "در حال بارگذاری…":"Loading…", "کد کپی شد.":"Code copied.", "بخش کد امبد در دسترس نیست.":"Embed code is unavailable.", "کد جاسازی":"Embed code", "این کد را پیش از <span class=":"Place this code before <span class=", "تم ویجت در سایت شما":"Widget theme on your site", "«خودکار» تم ویجت را با تم دستگاه بازدیدکننده هماهنگ می‌کند.":"Auto matches the widget theme to the visitor’s device.",
    "سلام! برای تست، یک سؤال درباره‌ی دانشنامه‌ات بپرس.":"Hello! Ask a question about your knowledge base to test the assistant.", "پیامت را بنویس…":"Type your message…", "مدل فعال":"Active model", "هنوز سؤالی پرسیده نشده.":"No question asked yet.", "شروع گفت‌وگوی جدید":"Start a new chat", "عبارت جست‌وجو":"Search query", "مثلاً: هزینه ارسال چقدره؟":"e.g. What is the shipping cost?", "رفتار دستیار ذخیره شد.":"Assistant behavior saved.", "عنوان و پیام خوش‌آمدگویی نمی‌توانند خالی باشند.":"Widget title and welcome message cannot be empty.", "تنظیمات ویجت ذخیره شد.":"Widget settings saved.", "ذخیره‌ی حیوان خانگی و پاسخ‌های سریع نیاز به یک‌بار اجرای migration شماره‌ی ۰۰۲ دارد.":"Saving pets and quick replies requires migration 002 to exist.",
    "برای این اجرا یکی را انتخاب کن.":"Choose how to run this instance.", "Prismo را چطور اجرا کنیم؟":"How should Prismo run?", "سریع‌ترین حالت":"Fastest", "کاملاً لوکال":"Fully local", "ابری":"Cloud", "در حال تنظیم اجرای کاملاً لوکال…":"Configuring local mode…", "در حال تنظیم اتصال Supabase…":"Configuring Supabase…",
    "Prismo — ویجت هوشمند دانش‌محور":"Prismo — Knowledge-powered AI widget", "دانشنامه‌ی خودت را بده، یک ویجت چت هوشمند تحویل بگیر":"Give your knowledge base and get an AI chat widget", "هر داده و مستندی که وارد می‌کنی، به یک دستیار گفت‌وگوی هوشمند تبدیل می‌شود که می‌تونی با یک خط کد داخل هر وب‌سایتی جاسازی‌اش کنی؛ کاملاً شخصی‌سازی‌شده و مخصوص خودت.":"Turn your data and documents into a smart assistant that you can embed into any website with one line of code.", "ثبت‌نام کن و مدل هوش مصنوعی موردنظرت را وصل کن (یا از مدل‌های رایگان آماده استفاده کن)":"Sign up and connect your preferred AI model (or use ready free models)", "اسناد و اطلاعاتت را به دانشنامه اضافه کن و رفتار دستیار را شخصی‌سازی کن":"Add your documents and customize the assistant behavior", "کد ویجت را کپی و داخل وب‌سایتت جاسازی کن":"Copy the widget code and embed it on your website", "دستیار هوشمند شما":"Your smart assistant", "سلام!":"Hello!", "هر سوالی درباره‌ی دانشنامه‌ات داری بپرس":"Ask anything about your knowledge base", "ساعت کاری پشتیبانی چیه؟":"What are support hours?", "طبق سندی که آپلود کردی، پشتیبانی هر روز ۹ تا ۱۸ فعاله.":"According to your uploaded document, support is available daily from 9 AM to 6 PM.", "پیامت رو بنویس…":"Type your message…", "برای ساخت و مدیریت ویجت‌هایت وارد شو":"Sign in to build and manage your widgets", "ساخت حساب جدید":"Create a new account", "چند ثانیه طول می‌کشد؛ همین حالا شروع کن":"It only takes a few seconds; start now", "ثبت‌نام":"Sign up", "ورود به حساب":"Sign in", "Prismo":"Prismo",
    "در حال آماده‌سازی پاسخ…":"Preparing response…", "پاسخ مدل هم‌زمان با رسیدن tokenها نمایش داده شود؛ خاموش باشد پاسخ یک‌جا می‌آید.":"Show model output as tokens arrive; when off, show the complete response at once.", "مثلاً: یک پاراگراف کوتاه درباره‌ی اهمیت RAG بنویس.":"e.g. Write a short paragraph about why RAG matters.",
  });

  Object.assign(dict, {
  "خطا (${res.status})": "Error (${res.status})",
  "بارگذاری بخشی از صفحه ناموفق بود؛ اتصال اینترنت را بررسی کن.": "Part of the page failed to load; check your internet connection.",
  "در حال بارگذاری": "Loading",
  "ارتباط با سرور برقرار نشد.": "Could not connect to the server.",
  "خطا در دریافت پاسخ.": "Failed to receive the response.",
  "در حال دریافت…": "Fetching…",
  "در حال خواندن /models سرویس…": "Reading the service /models endpoint…",
  "در حال بررسی…": "Checking…",
  "DNS: resolve نشد": "DNS: resolution failed",
  "نوع خطا:": "Error type:",
  "زمان:": "Time:",
  "ابتدا مدل چت را انتخاب کن.": "Select a chat model first.",
  "یک پرامپت بنویس.": "Write a prompt.",
  "ویرایش": "Edit",
  "حذف": "Delete",
  "ویرایش سند": "Edit document",
  "این سند حذف شود؟ این کار قابل بازگشت نیست.": "Delete this document? This action cannot be undone.",
  "سند حذف شد.": "Document deleted.",
  "همه‌ی اسناد دانشنامه حذف شوند؟ این کار قابل بازگشت نیست.": "Delete all knowledge-base documents? This action cannot be undone.",
  "دانشنامه پاک شد.": "Knowledge base cleared.",
  "نکته: جست‌وجوی معنایی فقط دنبال کلمهٔ دقیق نمی‌گردد؛ مفهوم سؤال را هم در نظر می‌گیرد.": "Tip: semantic search does not only match exact words; it also considers the meaning of the question.",
  "یادآوری: بعد از ایندکس، پاسخ‌های تست و ویجت می‌توانند از همین دانشنامه استفاده کنند.": "Reminder: after indexing, test-lab and widget answers can use this knowledge base.",
  "نکته: هرچه متن سند منظم‌تر و بخش‌بندی‌شده‌تر باشد، بازیابی اطلاعات دقیق‌تر می‌شود.": "Tip: better-structured documents usually produce more accurate retrieval.",
  "قابلیت جالب: مدل می‌تواند از چند بخش مرتبط سند، یک پاسخ یکپارچه بسازد.": "Nice: the model can combine several relevant document chunks into one answer.",
  "پشت صحنه: برای هر بخش، یک نمایش عددی ساخته می‌شود تا پیدا کردن اطلاعات مرتبط سریع شود.": "Behind the scenes: each chunk gets a numerical representation so related information can be found quickly.",
  "در حال پردازش سند…": "Processing document…",
  "عنوان و محتوا را پر کن.": "Fill in the title and content.",
  "در حال ذخیره…": "Saving…",
  "سند بروزرسانی شد.": "Document updated.",
  "در حال تبدیل و ایندکس…": "Converting and indexing…",
  "در حال ذخیره و ایندکس سند…": "Saving and indexing document…",
  "همه بخش‌های سند با موفقیت ذخیره شد؛ دانشنامه آماده است ✓": "All document chunks were saved successfully; the knowledge base is ready ✓",
  "سند اضافه و ایندکس شد.": "Document added and indexed.",
  "ایندکس سند ناموفق بود.": "Document indexing failed.",
  "در حال پردازش…": "Processing…",
  "ایمپورت قبلی هنوز تمام نشده است.": "The previous import has not finished yet.",
  "در حال وارد کردن": "Importing",
  "در حال خواندن": "Reading",
  "آماده‌ی بازبینی": "Ready for review",
  "در حال ایندکس‌کردن…": "Indexing…",
  "ناموفق": "Failed",
  "پردازش همه فایل‌ها تمام شد": "All files finished processing",
  "پردازش تمام شد": "Processing finished",
  "موردی برای بررسی نیست": "Nothing to review",
  "تغییرات ذخیره‌نشده دارید": "You have unsaved changes",
  "شناسه درخواست:": "Request ID:",
  "رفتار دستیار ذخیره شد.": "Assistant behavior saved.",
  "فهرست مدل‌ها با probe واقعی تأیید شد.": "The model list was verified with a real capability probe.",
  "هیچ مدل چتی که probe موفق داشته باشد پیدا نشد.": "No chat model passed the capability probe.",
  "مدل چت قابل استفاده پیدا نشد.": "No usable chat model was found.",
  "مدل embedding قابل استفاده پیدا نشد.": "No usable embedding model was found.",
  "مدل چت تأیید شد": "chat model verified",
  "مدل embedding تأیید شد": "embedding model verified",
  "مدل embedding سازگار با ابعاد": "embedding model compatible with dimension",
  "فهرست مدل‌ها": "model list",
  "کلید ذخیره شده": "saved key",
  "کلیدی ذخیره نشده است.": "No key is saved.",
  "کلید embedding ذخیره شده است؛ برای امنیت نمایش داده نمی‌شود.": "The embedding key is saved; it is hidden for security.",
  "کلید جداگانه‌ای ذخیره نشده است.": "No separate key is saved.",
  "برای نمایش مدل‌های این سرویس، روی «دریافت مدل‌ها» بزن.": "Click “Discover models” to list models from this service.",
  "اتصال آماده ذخیره شد.": "Ready connection saved.",
  "ابتدا لیست مدل‌های سرویس را دریافت کن.": "Discover the service models first.",
  "این سرویس مدل embedding سازگار با پروژه ارائه نمی‌کند.": "This service does not provide an embedding model compatible with the project.",
  "اتصال API اختصاصی ذخیره شد.": "Custom API connection saved.",
  "مدل:": "Model:",
  "در حال دریافت": "Fetching",
  "پاسخ متوقف شد.": "Response stopped.",
  "پاسخ متوقف شد": "Response stopped",
  "تنظیمات ویجت دریافت نشد. اتصال سرور را بررسی کنید.": "Widget settings could not be loaded. Check the server connection.",
  "باز و بسته‌کردن منو": "Toggle menu",
  "مسیر صفحه": "Page path",
  "تغییر حالت نمایش": "Change view mode",
  "بازگشت به داشبورد کاربری": "Back to user dashboard",
  "آمار کلان و تله‌متری سیستم": "System-wide metrics and telemetry",
  "یک نگاه کلی به وضعیت پلتفرم در سطح تمام کاربران.": "A platform-wide view across all users.",
  "مدیریت و پایش کاربران": "User management and monitoring",
  "لیست تمام کاربران ثبت‌نام‌شده، مسدودسازی، تغییر نقش و بازرسی حساب.": "Registered users, blocking, role changes, and account inspection.",
  "جست‌وجو بر اساس نام کاربری یا سازمان…": "Search by username or organization…",
  "اسناد": "Documents",
  "نشست‌ها": "Sessions",
  "ثبت‌نام": "Registration",
  "عملیات": "Actions",
  "گزارش جامع مکالمات": "Conversation report",
  "همه": "All",
  "منبع": "Source",
  "بازدیدکننده": "Visitor",
  "تعداد پیام": "Message count",
  "تاریخ": "Date",
  "نظارت امنیتی": "Security monitoring",
  "شدت متوسط": "Medium severity",
  "هشدار با شدت بالا": "High-severity alert",
  "هشدار بحرانی": "Critical alert",
  "مشکوک": "Suspicious",
  "بررسی‌شده": "Reviewed",
  "مشاهده‌ی گفت‌وگو": "View conversation",
  "مسدودکردن کاربر": "Block user",
  "بررسی شد": "Reviewed",
  "بازرسی کاربر": "Inspect user",
  "پیام‌های نشست": "Session messages",
  "نقش فعلی": "Current role",
  "مدل چت / امبدینگ": "Chat / embedding model",
  "پرامپت سیستمی اختصاصی کاربر": "User custom system prompt",
  "تلاش برای گرفتن سیستم‌پرامپت": "Attempt to read system prompt",
  "ویجت عمومی": "Public widget",
  "آزمایشگاه": "Lab",
  "آزمایشگاه تست": "Test lab",
  "بازرسی:": "Inspect:",
  "تعداد تکه‌ها": "Chunk count",
  "نشست‌های گفت‌وگو (": "Chat sessions (",
  "سرویس موقتاً در دسترس نیست.": "The service is temporarily unavailable.",
  "سرویس موقتاً در دسترس نیست": "The service is temporarily unavailable",
  "ارتباط با سرویس قطع شد.": "The connection to the service was interrupted.",
  "نشست شما منقضی شده؛ دوباره وارد شوید.": "Your session has expired; please sign in again.",
  "کاربر یافت نشد.": "User not found.",
  "این بخش فقط برای مدیر سیستم در دسترس است.": "This section is available only to system administrators.",
  "این نام کاربری قبلاً ثبت شده است.": "This username is already registered.",
  "نام کاربری یا رمز عبور اشتباه است.": "Incorrect username or password.",
  "حساب کاربری شما مسدود شده است.": "Your account is blocked.",
  "ویجت یافت نشد.": "Widget not found.",
  "تعداد درخواست‌ها زیاد است. چند لحظه بعد دوباره تلاش کنید.": "Too many requests. Please try again in a moment.",
  "ایجاد حساب": "Create account",
  "ورود": "Sign in",
  "رمز عبور": "Password",
  "حداقل ۶ کاراکتر": "At least 6 characters",
  "ساخت حساب و شروع": "Create account and start",
  "ورود به حساب": "Sign in",
  "نام سازمان / برند شما (اختیاری)": "Organization / brand name (optional)",
  "هر کاربر، دانشنامه و ویجتِ کاملاً مجزا و اختصاصیِ خودش را دارد.": "Every user gets a completely separate knowledge base and widget.",
  "Prismo را چطور اجرا کنیم؟": "How should Prismo run?",
  "برای این اجرا یکی را انتخاب کن.": "Choose one for this run.",
  "کاملاً لوکال": "Fully local",
  "این نسخه روی Vercel اجرا می‌شود": "This version runs on Vercel",
  "انتخاب دیتابیس در Vercel از متغیرهای محیطی انجام می‌شود؛ این صفحه نباید برای اجرای عادی نمایش داده شود.": "Vercel database selection is controlled by environment variables; this page should not appear during normal use.",
  "در حال انتقال به صفحه اصلی…": "Redirecting to the main page…",
  "تنظیمات ذخیره نشد.": "Settings were not saved.",
  "Supabase انتخاب شد. در حال بررسی آماده‌شدن سرور…": "Supabase selected. Checking server readiness…",
  "حالت لوکال انتخاب شد. در حال اجرای Prismo…": "Local mode selected. Starting Prismo…",
  "برنامه اصلی اجرا نشد.": "The main application did not start.",
  "راه‌اندازی بیشتر از حد معمول طول کشید. فایل data/prismo-startup.log را بررسی کن.": "Startup took longer than expected. Check data/prismo-startup.log.",
  "خطا در تنظیم پروژه.": "Project setup failed.",
  "مثلاً: فروشگاه آنلاین رویا": "e.g. Online Roya Store",
  "فعال‌کردن حالت تیره": "Enable dark mode",
  "فعال‌کردن حالت روشن": "Enable light mode",
  "پنل مدیریت": "Admin panel",
  "پنل ادمین": "Admin panel",
  "پنل Administration": "Admin panel",
  "پاسخی دریافت نشد.": "No response received.",
  "✓ اضافه شد": "✓ Added",
  "این کد را پیش از </body> هر صفحه‌ی وب‌سایتت بگذار.": "Add this code before </body> on every page of your website.",
  "این کد را پیش از": "Add this code before",
  "هر صفحه‌ی وب‌سایتت بگذار.": "on every page of your website.",
  "قبل از انتشار ویجت، رفتار دستیار را همین‌جا امتحان کن.": "Test the assistant’s behavior here before publishing the widget.",
  "هنوز Documentی اضافه نکرده‌ای": "No document has been added yet.",
  "هنوز سندی اضافه نکرده‌ای": "No document has been added yet.",
  "این پروژه سه بخش اصلی داره — All رو از منوی کناری در دسترس داری.": "This project has three main sections — you can access them all from the sidebar.",
  "این پروژه سه بخش اصلی داره — همه رو از منوی کناری در دسترس داری.": "This project has three main sections — you can access them all from the sidebar.",
  "پنل مدیریت — Prismo": "Admin panel — Prismo",
  "هفت پوسته‌ی دست‌ساز با کنتراست، کارت و glow متفاوت برای کار طولانی.": "Seven handcrafted themes with distinct contrast, cards, and glow for long sessions.",
  "پس از اتمام پاسخ، یک صدای کوتاه پخش شود.": "Play a short sound after the response finishes.",
  "کنترل‌هایی برای کاهش کلیک، حرکت و شلوغی محیط.": "Controls to reduce extra clicks, motion, and visual clutter.",
  "باز یا بسته بودن منوی کناری به خاطر سپرده شود.": "Remember whether the sidebar is expanded or collapsed.",
  "آخرین تب انتخاب‌شده در دفعه بعد باز شود.": "Restore the last selected tab next time.",
  "محتوا": "Content",
  "نشست": "Session",
  "در حال دریافت پاسخ…": "Receiving responses…",
  "مدل انتخاب‌شده در لیست مدل‌های رایگان آماده نیست.": "The selected model is not in the ready-to-use model list.",
  "کل کاربران": "Total users",
  "کاربران فعال": "Active users",
  "کاربران مسدود": "Blocked users",
  "مدیران سیستم": "System administrators",
  "اسناد دانشنامه": "Knowledge base documents",
  "تکه‌های ایندکس‌شده": "Indexed chunks",
  "کل نشست‌های گفت‌وگو": "Total chat sessions",
  "کل پیام‌ها": "Total messages",
  "گزارش مکالمات": "Conversation reports",
  "آمار کلان": "Overview",
  "مدیریت کاربران": "User management",
  "نظارت امنیتی": "Security monitoring",
  "هنوز سندی ثبت نشده است.": "No documents have been added yet.",
  "سند": "Document"
});

  // Complete phrases for the English UI, including Settings and Test Lab.
  Object.assign(dict, {
    'مرکز کنترل': 'Control center',
    'ذخیره محلی': 'Saved locally',
    'تنظیمات سایت': 'Site settings',
    'زبان، ظاهر، چت، میانبرها و حساب را از یک مرکز کنترل سریع مدیریت کن.': 'Manage language, appearance, chat, shortcuts, and your account from one quick control center.',
    'ظاهر و زبان': 'Appearance & language',
    'تغییرات این بخش فوری ذخیره می‌شوند و روی تمام صفحات سایت اعمال می‌شوند.': 'Changes in this section are saved instantly and applied across the entire site.',
    'با انتخاب English، متن‌های ثابت داشبورد، ادمین، تست‌لب و ویجت همگی انگلیسی و LTR می‌شوند.': 'Selecting English translates the dashboard, admin panel, test lab, and widget UI to English and switches the layout to LTR.',
    'زبان و جهت صفحه': 'Language & layout direction',
    'رنگ و حال‌وهوای محیط': 'Theme & atmosphere',
    'هفت پوسته‌ی دست‌ساز با کنتراست، کارت و glow متفاوت برای کار طولانی.': 'Seven handcrafted themes with distinct contrast, cards, and glow for long sessions.',
    'رفتار چت': 'Chat behavior',
    'این گزینه‌ها واقعاً روی Test Lab و گفت‌وگوی اصلی اثر می‌گذارند.': 'These options affect both the Test Lab and the main chat.',
    'نمایش تکه‌تکه‌ی پاسخ': 'Stream responses',
    'پاسخ مدل هم‌زمان با رسیدن tokenها نمایش داده شود؛ خاموش باشد پاسخ یک‌جا می‌آید.': 'Show model output as tokens arrive. When disabled, show the complete response at once.',
    'اسکرول خودکار گفتگو': 'Auto-scroll chat',
    'هنگام دریافت پاسخ، پایین گفتگو را دنبال کند.': 'Keep the latest response in view while a reply is arriving.',
    'ارسال با Enter': 'Send with Enter',
    'Enter ارسال کند و Shift+Enter خط جدید بسازد.': 'Press Enter to send and Shift+Enter to insert a new line.',
    'نمایش نشان مدل': 'Show model badge',
    'مدل فعال کنار پاسخ نمایش داده شود.': 'Show the active model next to each response.',
    'چیدمان فشرده چت': 'Compact chat layout',
    'فاصله‌ی حباب‌ها و عناصر چت کمی کمتر شود.': 'Reduce spacing between chat bubbles and controls.',
    'هشدار صوتی پایان پاسخ': 'Response completion sound',
    'پس از اتمام پاسخ، یک صدای کوتاه پخش شود.': 'Play a short sound when a response finishes.',
    'تأیید پاک‌کردن گفتگو': 'Confirm before clearing chat',
    'قبل از ساخت چت تازه با میانبر، تأیید بگیر.': 'Ask for confirmation before starting a fresh chat with a shortcut.',
    'فضای کاری و میانبرها': 'Workspace & shortcuts',
    'کنترل‌هایی برای کاهش کلیک، حرکت و شلوغی محیط.': 'Controls that reduce clicks, motion, and visual clutter.',
    'حالت کم‌تحرک': 'Reduced motion',
    'انیمیشن‌ها و حرکت‌های غیرضروری را کاهش می‌دهد.': 'Reduce non-essential animations and movement.',
    'سایدبار فشرده': 'Compact sidebar',
    'منوی کناری را به حالت آیکونی کوچک می‌کند.': 'Collapse the sidebar to an icon-only rail.',
    'کنتراست بیشتر': 'Higher contrast',
    'مرزها و متن‌های کم‌رنگ را خواناتر می‌کند.': 'Improve the legibility of borders and muted text.',
    'بازگردانی آخرین بخش': 'Restore last section',
    'بعد از ورود دوباره همان بخش قبلی باز شود.': 'Reopen the last section after signing in again.',
    'حفظ وضعیت سایدبار': 'Remember sidebar state',
    'باز یا بسته بودن منوی کناری به خاطر سپرده شود.': 'Remember whether the sidebar is expanded or collapsed.',
    'آخرین تب تنظیمات': 'Remember settings tab',
    'آخرین تب انتخاب‌شده در دفعه بعد باز شود.': 'Restore the previously selected settings tab next time.',
    'فعال‌سازی میانبرها': 'Enable keyboard shortcuts',
    'میانبرهای آماده برای چت، تنظیمات و بستن پنجره‌ها.': 'Ready-made shortcuts for chat, settings, and closing dialogs.',
    'میانبرهای آماده': 'Quick shortcuts',
    'بازنشانی تنظیمات سایت': 'Reset site settings',
    'حساب کاربری': 'Account',
    'اطلاعات حساب همین‌جا دیده می‌شود؛ نام و آیکون همچنان پایین سایدبار باقی می‌ماند.': 'Manage account details here; your name and avatar remain at the bottom of the sidebar.',
    'نام کاربری': 'Username',
    'نام سازمان': 'Organization',
    'نقش': 'Role',
    'وضعیت': 'Status',
    'فعال': 'Active',
    'خروج از حساب': 'Sign out',
    'پنل مدیریت': 'Admin panel',
    'پنل ادمین': 'Admin panel',
    'پنل Administration': 'Admin panel',
    'تست گفت‌وگوی RAG': 'Chat test',
    'تست گفت‌وگو با RAG': 'Chat test',
    'تست گفت‌وگو': 'Chat test',
    'تست چت RAG': 'Chat test',
    'تست چتِ RAG': 'Chat test',
    'تست چتی RAG': 'Chat test',
    'سلام! برای تست، یک سؤال درباره‌ی دانشنامه‌ات بپرس.': 'Hello! Ask a question about your knowledge base to test the assistant.',
    'منبعی از دانشنامه پیدا نشد.': 'No knowledge-base sources were found.',
    'مدل فعال': 'Active model',
    'منابع بازیابی‌شده': 'Retrieved sources',
    'هنوز سؤالی پرسیده نشده.': 'No question has been asked yet.',
    'شروع گفت‌وگوی جدید': 'Start a new chat',
    'عبارت جست‌وجو': 'Search query',
    'مثلاً: هزینه ارسال چقدره؟': 'e.g. What is the shipping cost?',
    'جست‌وجوی معنایی (Playground)': 'Semantic search (Playground)',
    'بازگشت به پنل ادمین': 'Back to Admin panel',
    'حالت آماده': 'Ready mode',
    'حالت اختصاصی': 'Custom mode',
    'روی «افزودن سند جدید» بزن تا اولین سندت را وارد کنی.': 'Click “Add document” to add your first document.',
    'روی لبه‌ی بالای ویجت راه می‌رود، بعد می‌ایستد و با کلیک قلب می‌دهد.': 'The pet walks along the top of the widget, pauses, and reacts with a heart when clicked.',
    'چند ثانیه بعد از ورود، پیام خوش‌آمدگویی بالای دکمه‌ی ویجت ظاهر می‌شود.': 'A welcome message appears above the widget button a few seconds after you sign in.',
    'مدال افزودن/ویرایش سند': 'Add/Edit document dialog',
    'عنوان سند': 'Document title',
    'برای این اجرا یکی را انتخاب کن. این صفحه فقط از طریق': 'Choose how to run this instance. This page is shown only through',
    'نمایش داده می‌شود و اجرای عادی سایت دیگر این سؤال را نشان نمی‌دهد.': 'and is not shown during normal site startup.',
    'SQLite داخلی، بدون Supabase و مناسب اجرای سریع روی همین سیستم. داده‌ها روی همین پروژه باقی می‌مانند.': 'Built-in SQLite, no Supabase required, and optimized for fast local use. Data stays in this project.',
    'PostgreSQL / Supabase با تنظیمات قبلی پروژه، مناسب اجرای ابری یا اتصال مستقیم به دیتابیس مشترک.': 'PostgreSQL / Supabase using the project’s existing settings, suitable for cloud hosting or a shared database.',
    'در Vercel این صفحه وارد چرخه اجرای برنامه نمی‌شود و انتخاب دیتابیس از طریق Environment Variables پروژه انجام می‌شود.': 'On Vercel, this page is not part of the app startup flow; database selection is controlled by project environment variables.',
    'Prismo را چطور اجرا کنیم؟': 'How should Prismo run?',
    'Prismo — ویجت هوشمند دانش‌محور': 'Prismo — Knowledge-powered AI widget',
    'داشبورد — Prismo': 'Prismo — Dashboard',
    'پنل مدیریت — Prismo': 'Prismo — Admin panel',
    'راه‌اندازی Prismo': 'Prismo — Setup',
    'Prismo': 'Prismo',
    'پنل مدیریت — Prismo': 'Prismo — Admin panel',
  });

  var phraseMap = Object.keys(dict).sort(function (a, b) { return b.length - a.length; });
  var reverseDict = {};
  Object.keys(dict).forEach(function (fa) { reverseDict[dict[fa]] = fa; });

  function read() {
    try { return Object.assign({}, defaults, JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}")); } catch (_) { return Object.assign({}, defaults); }
  }
  function save(next) { try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(next)); } catch (_) {} }
  var state = read();

  var allowedThemes = ["light", "dark", "ocean", "forest", "sunset", "lavender", "mono", "nord", "amber", "rose"];
  function currentTheme() {
    try {
      var stored = localStorage.getItem(THEME_KEY);
      if (allowedThemes.indexOf(stored) !== -1) return stored;
    } catch (_) {}
    return allowedThemes.indexOf(state.theme) !== -1 ? state.theme : "dark";
  }
  function getLanguage() { return state.language === "en" ? "en" : "fa"; }

  function latinizeUiNumbers(text, language) {
    if (language !== "en") return text;
    var eastern = "۰۱۲۳۴۵۶۷۸۹";
    var arabic = "٠١٢٣٤٥٦٧٨٩";
    return String(text).replace(/[۰-۹٠-٩٪]/g, function (digit) {
      if (digit === "٪") return "%";
      var idx = eastern.indexOf(digit);
      if (idx < 0) idx = arabic.indexOf(digit);
      return idx < 0 ? digit : String(idx);
    });
  }

  function translateString(text, language) {
    var value = String(text || "");
    if (!value) return value;
    var exact = language === "en" ? dict[value] : reverseDict[value];
    if (exact) return latinizeUiNumbers(exact, language);
    var out = value;
    var changed = false;
    if (language === "en") {
      phraseMap.forEach(function (fa) {
        if (out.indexOf(fa) !== -1) { out = out.split(fa).join(dict[fa]); changed = true; }
      });
    } else {
      phraseMap.forEach(function (fa) {
        var en = dict[fa];
        if (out.indexOf(en) !== -1) { out = out.split(en).join(fa); changed = true; }
      });
    }
    return latinizeUiNumbers(changed ? out : value, language);
  }

  function shouldSkipTextNode(node) {
    if (!node || !node.parentElement) return true;
    var el = node.parentElement;
    if (el.closest("[data-user-content], textarea, input, pre, code, .reply-text, .chat-msg.user, .chat-msg[data-runtime-message=\"1\"], .embed-code-box, .mono, .qz-widget-preview")) return true;
    return false;
  }

  var translationObserver = null;
  var isTranslating = false;
  function translateNode(node, allowWhileTranslating) {
    if (!node || (isTranslating && !allowWhileTranslating)) return;
    var walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    var sourceLanguage = getLanguage();
    var updates = [];
    while (walker.nextNode()) {
      var n = walker.currentNode;
      if (shouldSkipTextNode(n)) continue;
      var value = n.nodeValue.trim();
      if (!value) continue;
      var translated = translateString(value, sourceLanguage);
      if (translated !== value) updates.push([n, translated]);
    }
    updates.forEach(function (item) { item[0].nodeValue = item[1]; });

    // Semantic labels override phrase matching where text can be split or mixed with Latin acronyms.
    document.querySelectorAll("[data-i18n-fa][data-i18n-en]").forEach(function (el) {
      var nextText = sourceLanguage === "en" ? el.getAttribute("data-i18n-en") : el.getAttribute("data-i18n-fa");
      if (nextText != null && el.textContent !== nextText) el.textContent = nextText;
    });

    document.querySelectorAll("input[placeholder], textarea[placeholder], [title], [aria-label], [data-i18n-value]").forEach(function (el) {
      if (el.placeholder) el.placeholder = translateString(el.placeholder, sourceLanguage);
      if (el.title) el.title = translateString(el.title, sourceLanguage);
      if (el.getAttribute("aria-label")) el.setAttribute("aria-label", translateString(el.getAttribute("aria-label"), sourceLanguage));
      if (el.hasAttribute("data-i18n-value") && "value" in el) el.value = translateString(el.getAttribute("data-i18n-value"), sourceLanguage);
    });
    document.documentElement.lang = sourceLanguage;
    document.documentElement.dir = sourceLanguage === "en" ? "ltr" : "rtl";
    body.classList.toggle("qz-ltr", sourceLanguage === "en");
    if (document.title) document.title = translateString(document.title, sourceLanguage);
  }

  function setTheme(theme, persist) {
    // Keep one theme authority for both the global shell and the settings view.
    // Previously settings.js and theme.js each wrote the root/localStorage
    // independently, allowing stale or invalid saved values to desynchronise
    // the active preset state from the CSS tokens.
    if (allowedThemes.indexOf(theme) === -1) theme = "dark";
    if (window.QZTheme && typeof window.QZTheme.set === "function") {
      window.QZTheme.set(theme, !!persist);
      theme = window.QZTheme.get();
    } else {
      root.dataset.theme = theme;
      if (persist) { try { localStorage.setItem(THEME_KEY, theme); } catch (_) {} }
      document.dispatchEvent(new CustomEvent("qz-theme-change", { detail: { theme: theme } }));
    }
    state.theme = theme;
    if (persist) save(state);
    document.querySelectorAll("[data-theme-preset]").forEach(function (el) {
      var active = el.dataset.themePreset === theme;
      el.classList.toggle("active", active);
      el.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  document.addEventListener("qz-theme-change", function (event) {
    var theme = event && event.detail && event.detail.theme;
    if (allowedThemes.indexOf(theme) === -1) return;
    document.querySelectorAll("[data-theme-preset]").forEach(function (el) {
      var active = el.dataset.themePreset === theme;
      el.classList.toggle("active", active);
      el.setAttribute("aria-pressed", active ? "true" : "false");
    });
  });

  function setLanguage(lang, persist) {
    state.language = lang === "en" ? "en" : "fa";
    if (persist) { try { localStorage.setItem(LANGUAGE_KEY, state.language); } catch (_) {} save(state); }
    if (translationObserver) translationObserver.disconnect();
    isTranslating = true;
    try { translateNode(document.body, true); } finally {
      isTranslating = false;
      if (translationObserver) translationObserver.observe(document.body, { childList: true, subtree: true, characterData: true });
    }
    document.querySelectorAll("[data-language]").forEach(function (el) { el.classList.toggle("active", el.dataset.language === state.language); });
    document.dispatchEvent(new CustomEvent("qz-language-change", { detail: { language: state.language } }));
  }

  function playDoneSound() {
    if (!state.responseSound || !window.AudioContext) return;
    try {
      var ctx = new AudioContext(); var osc = ctx.createOscillator(); var gain = ctx.createGain();
      osc.frequency.value = 740; gain.gain.value = 0.035; osc.connect(gain); gain.connect(ctx.destination); osc.start(); osc.stop(ctx.currentTime + 0.08);
      osc.onended = function () { ctx.close(); };
    } catch (_) {}
  }

  function setCompactSidebar(on) { body.classList.toggle("sidebar-rail", !!on); if (state.rememberRail) { try { localStorage.setItem("qz_rail", on ? "1" : "0"); } catch (_) {} } }
  function setCompactChat(on) { body.classList.toggle("qz-compact-chat", !!on); }

  function bindSwitch(id, key, handler) {
    var el = document.getElementById(id); if (!el) return;
    el.checked = !!state[key];
    el.addEventListener("change", function () { state[key] = el.checked; save(state); if (handler) handler(el.checked); updateBadge(); });
  }

  function updateBadge() {
    var badge = document.getElementById("settingsSavedBadge");
    if (badge) badge.textContent = getLanguage() === "en" ? "Saved locally" : "ذخیره محلی";
  }

  function applySettingsTabs() {
    var tabs = document.querySelectorAll("[data-settings-tab]");
    var panes = document.querySelectorAll("[data-settings-pane]");
    if (!tabs.length) return;
    var selected = state.rememberTab ? (localStorage.getItem(SETTINGS_TAB_KEY) || "appearance") : "appearance";
    if (!document.querySelector('[data-settings-pane="' + selected + '"]')) selected = "appearance";
    tabs.forEach(function (tab) {
      var active = tab.dataset.settingsTab === selected;
      tab.classList.toggle("active", active); tab.setAttribute("aria-selected", active ? "true" : "false");
      tab.addEventListener("click", function () {
        selected = tab.dataset.settingsTab;
        tabs.forEach(function (t) { var on = t === tab; t.classList.toggle("active", on); t.setAttribute("aria-selected", on ? "true" : "false"); });
        panes.forEach(function (pane) { pane.hidden = pane.dataset.settingsPane !== selected; });
        if (state.rememberTab) { try { localStorage.setItem(SETTINGS_TAB_KEY, selected); } catch (_) {} }
      });
    });
    panes.forEach(function (pane) { pane.hidden = pane.dataset.settingsPane !== selected; });
  }

  function shortcutHelp() {
    var target = document.getElementById("shortcutHelpText");
    if (!target) return;
    target.innerHTML = getLanguage() === "en"
      ? "<kbd>Ctrl/⌘ + Shift + N</kbd> new chat · <kbd>Ctrl/⌘ + K</kbd> focus message · <kbd>Ctrl/⌘ + ,</kbd> settings · <kbd>Ctrl/⌘ + Shift + Delete</kbd> clear chat · <kbd>Esc</kbd> close"
      : "<kbd>Ctrl/⌘ + Shift + N</kbd> گفت‌وگوی تازه · <kbd>Ctrl/⌘ + K</kbd> تمرکز پیام · <kbd>Ctrl/⌘ + ,</kbd> تنظیمات · <kbd>Ctrl/⌘ + Shift + Delete</kbd> پاک‌کردن چت · <kbd>Esc</kbd> بستن";
  }

  function bindShortcuts() {
    document.addEventListener("keydown", function (e) {
      if (!state.keyboardShortcuts || !(e.ctrlKey || e.metaKey) && e.key !== "Escape") return;
      var key = String(e.key).toLowerCase();
      if (e.key === "Escape") {
        var shown = document.querySelector(".modal-overlay.show");
        if (shown) { var close = shown.querySelector(".icon-btn"); if (close) close.click(); else shown.classList.remove("show"); e.preventDefault(); return; }
        var mobile = document.getElementById("sidebarScrim"); if (mobile) mobile.click();
        return;
      }
      if (!(e.ctrlKey || e.metaKey)) return;
      var newChat = key === "n" && e.shiftKey;
      var focusChat = key === "k" && !e.shiftKey;
      var openSettings = key === "," && !e.shiftKey;
      var clearChat = (key === "delete" || key === "backspace") && e.shiftKey;
      if (newChat || clearChat) {
        var btn = document.getElementById("newSessionBtn");
        if (btn) { e.preventDefault(); if (clearChat && state.confirmClearChat && !confirm(getLanguage() === "en" ? "Start a new chat and clear the current conversation?" : "گفت‌وگوی فعلی پاک و یک نشست تازه ساخته شود؟")) return; btn.click(); }
      } else if (focusChat) {
        var input = document.getElementById("chatInput"); if (input) { e.preventDefault(); input.focus(); }
      } else if (openSettings) {
        var nav = document.querySelector('[data-nav="settings"]'); if (nav) { e.preventDefault(); nav.click(); }
      }
    });
  }

  function initControls() {
    document.querySelectorAll("[data-theme-preset]").forEach(function (el) { el.addEventListener("click", function () { setTheme(el.dataset.themePreset, true); }); });
    document.querySelectorAll("[data-language]").forEach(function (el) { el.addEventListener("click", function () { setLanguage(el.dataset.language, true); }); });
    bindSwitch("settingStreaming", "streaming"); bindSwitch("settingAutoScroll", "autoScroll"); bindSwitch("settingResponseSound", "responseSound");
    bindSwitch("settingChatEnterSend", "chatEnterSend"); bindSwitch("settingShowModelBadge", "showModelBadge"); bindSwitch("settingCompactChat", "compactChat", setCompactChat); bindSwitch("settingConfirmClearChat", "confirmClearChat");
    bindSwitch("settingReducedMotion", "reducedMotion", function (on) { body.classList.toggle("qz-reduced-motion", on); });
    bindSwitch("settingCompactSidebar", "compactSidebar", setCompactSidebar); bindSwitch("settingHighContrast", "highContrast", function (on) { body.classList.toggle("qz-high-contrast", on); });
    bindSwitch("settingRememberView", "rememberView"); bindSwitch("settingRememberRail", "rememberRail"); bindSwitch("settingRememberTab", "rememberTab"); bindSwitch("settingKeyboardShortcuts", "keyboardShortcuts");
    var reset = document.getElementById("resetSiteSettingsBtn");
    if (reset) reset.addEventListener("click", function () { if (!confirm(getLanguage() === "en" ? "Reset all local site preferences?" : "همه تنظیمات محلی سایت بازنشانی شود؟")) return; state = Object.assign({}, defaults); save(state); try { localStorage.removeItem(THEME_KEY); localStorage.removeItem(SETTINGS_TAB_KEY); } catch (_) {} location.reload(); });
    applySettingsTabs(); shortcutHelp(); bindShortcuts();
  }

  translationObserver = new MutationObserver(function (mutations) {
    if (isTranslating || !mutations || getLanguage() !== "en") return;
    translationObserver.disconnect();
    isTranslating = true;
    try {
      mutations.forEach(function (m) {
        if (m.type === "childList") m.addedNodes.forEach(function (n) {
          if (n.nodeType === 1) translateNode(n, true);
          else if (n.nodeType === 3 && n.nodeValue.trim() && !shouldSkipTextNode(n)) {
            var raw = n.nodeValue.trim(); var translated = translateString(raw, "en");
            if (translated !== raw) n.nodeValue = translated;
          }
        });
        else if (m.type === "characterData" && m.target && m.target.nodeValue && !shouldSkipTextNode(m.target)) {
          var value = m.target.nodeValue.trim(); var translatedValue = translateString(value, "en");
          if (value && translatedValue !== value) m.target.nodeValue = translatedValue;
        }
      });
      shortcutHelp();
    } finally {
      isTranslating = false;
      translationObserver.observe(document.body, { childList: true, subtree: true, characterData: true });
    }
  });

  window.QZI18n = {
    getLanguage: getLanguage,
    t: function (text) { return translateString(text, getLanguage()); },
    apply: function () { translateNode(document.body); },
  };

  window.QZSettings = {
    get: function (key) { return state[key]; }, state: function () { return Object.assign({}, state); },
    setTheme: setTheme, setLanguage: setLanguage, playDoneSound: playDoneSound,
    translate: function (text) { return translateString(text, getLanguage()); },
    isEnglish: function () { return getLanguage() === "en"; },
    apply: function () {
      setTheme(currentTheme(), false);
      body.classList.toggle("qz-reduced-motion", !!state.reducedMotion); body.classList.toggle("qz-high-contrast", !!state.highContrast); setCompactChat(!!state.compactChat); if (state.compactSidebar) setCompactSidebar(true);
      try { if (localStorage.getItem(LANGUAGE_KEY) === "en") state.language = "en"; } catch (_) {}
      setLanguage(state.language, false); updateBadge(); shortcutHelp();
    }
  };

  window.addEventListener("qz-response-complete", playDoneSound);
  document.addEventListener("qz-language-change", shortcutHelp);
  function init() { initControls(); QZSettings.apply(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true }); else init();
})();
