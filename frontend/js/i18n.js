// frontend/js/i18n.js

// زبان پیش‌فرض: انگلیسی
const DEFAULT_LANG = "en";

const TRANSLATIONS = {
  en: {
    // ---------- Layout / header ----------
    "layout.app_title": "v2rayscan Monitoring Panel",

    // ---------- Login ----------
    "login.title": "Admin login",
    "login.subtitle": "Sign in to access the monitoring panel.",
    "login.language.label": "Language",
    "login.language.en": "English",
    "login.language.fa": "Persian",
    "login.username": "Username",
    "login.password": "Password",
    "login.button": "Login",
    "login.footer": "v2rayscan monitoring panel",

    // ---------- Settings ----------
    "settings.title": "Global settings",

    "settings.telegram_bot_token": "Telegram bot token",
    "settings.telegram_bot_token.placeholder": "Telegram bot token",

    "settings.telegram_chat_id": "Destination chat_id",
    "settings.telegram_chat_id.placeholder": "Destination chat_id",

    "settings.check_interval": "Check interval (seconds)",

    "settings.telegram.notify_recover":
      "Send notification when server recovers",

    "settings.telegram.down_threshold":
      "Consecutive failed tests to mark server as DOWN",
    "settings.telegram.down_threshold.help":
      "For example, 3 means if 3 tests in a row FAIL, send a DOWN message.",

    "settings.proxy.title": "Proxy settings for Telegram",
    "settings.proxy.use_proxy": "Send Telegram messages via a proxy",

    "settings.proxy.mode": "Proxy mode for Telegram",
    "settings.proxy.mode.none": "No proxy (direct)",
    "settings.proxy.mode.socks": "External SOCKS5 proxy",
    "settings.proxy.mode.server": "Use one of the servers (XRAY)",

    "settings.proxy.socks_host": "SOCKS host",
    "settings.proxy.socks_host.placeholder": "e.g. 127.0.0.1 or proxy host",
    "settings.proxy.socks_port": "SOCKS port",
    "settings.proxy.socks_port.placeholder": "e.g. 1080",

    "settings.proxy.socks_user": "SOCKS username (optional)",
    "settings.proxy.socks_pass": "SOCKS password (optional)",

    "settings.proxy.server_id": "Server ID used as proxy for Telegram (Null For Automatic)",

    "settings.button.save": "Save settings",
    "settings.status.ok": "Settings saved",
    "settings.status.error": "Failed to save settings",

    // ---------- Live monitor ----------
    "live.title": "Live config monitoring (via XRAY)",
    "live.link.label": "Config link (vless:// or vmess://)",
    "live.interval.label": "Sampling interval (seconds)",
    "live.start": "Start monitoring",
    "live.stop": "Stop",

    "live.metrics.total": "Total samples: ",
    "live.metrics.success": "Success: ",
    "live.metrics.down": "Down: ",
    "live.metrics.success_rate": "Success rate: ",
    "live.metrics.avg_latency": "Average latency: ",
    "live.metrics.last_latency": "Last latency: ",
    "live.metrics.consecutive_down": "Consecutive down: ",
    "live.metrics.last_error": "Last error: ",

    // ---------- Add server ----------
    "addserver.title": "Add new server",
    "addserver.name.label": "Server name (optional)",
    "addserver.name.placeholder": "e.g. Germany-1",
    "addserver.link.label": "Config link (vless/vmess/...)",
    "addserver.link.placeholder":
      "Paste full link here, e.g. vless://...",
    "addserver.button": "Add",
    "addserver.status.error_required": "Please enter the link",
    "addserver.status.error": "Failed to add server",
    "addserver.status.ok": "Server added successfully",

    // ---------- Servers list / table ----------
    "servers.title": "Servers list",

    "servers.column.id": "ID",
    "servers.column.name": "Name",
    "servers.column.group": "Group",
    "servers.column.address": "Address",
    "servers.column.type": "Type",
    "servers.column.raw_link": "Full link",
    "servers.column.status": "Status",
    "servers.column.latency": "Latency",
    "servers.column.last_check": "Last check",
    "servers.column.actions": "Actions",

    "servers.action.toggle": "Enable / Disable",
    "servers.action.test": "Test",
    "servers.action.chart": "Chart",
    "servers.action.monitor": "Live monitor",
    "servers.action.edit": "Edit",
    "servers.action.delete": "Delete",

    "servers.error.link_required": "Please enter the link",
    "servers.error.add": "Failed to add server",
    "servers.success.add": "Server added successfully",
    "servers.error.toggle": "Failed to change server status",
    "servers.error.delete": "Failed to delete server",
    "servers.error.test": "Failed to test server",
    "servers.confirm.delete": "Delete this server?",

    // ---------- Groups ----------
    "groups.new": "New group",
    "groups.all": "All",
    "groups.ungrouped": "Ungrouped",
    "groups.actions.edit": "Edit group",
    "groups.actions.delete": "Delete group",
    "groups.prompt.new": "Enter a name for the new group:",
    "groups.prompt.color_new":
      "Group color (e.g. #0ea5e9) - optional:",
    "groups.prompt.rename": "New group name:",
    "groups.prompt.color_edit":
      "Group color (e.g. #0ea5e9):",
    "groups.confirm.delete":
      "Delete group? Servers will become ungrouped.",

    // ---------- Chart ----------
    "chart.title": "Server status chart",
    "chart.range.label": "Time range",
    "chart.range.60": "Last 1 hour",
    "chart.range.180": "Last 3 hours",
    "chart.range.720": "Last 12 hours",
    "chart.range.1440": "Last 24 hours",
    "chart.range.10080": "Last 7 days",

    "chart.stats": "Number of DOWN in this range: —",

    // ---------- Edit server modal ----------
    "edit.title": "Edit config",
    "edit.name": "Name",
    "edit.group": "Group",
    "edit.group.none": "No group",
    "edit.link": "Full link (raw_link)",
    "edit.enabled": "Enabled",
    "edit.cancel": "Cancel",
    "edit.save": "Save",

    // ---------- Monitor errors ----------
    "monitor.error.fetch_link": "Error getting server link",
    "monitor.error.unavailable": "Live monitor function is not available",
    "monitor.error.start": "Error starting live monitor",

    // ---------- Common ----------
    "common.error.network": "Network error",
  },

  fa: {
    // ---------- Layout / header ----------
    "layout.app_title": "پنل مانیتورینگ v2rayscan",
    // ---------- Login ----------
    "login.title": "ورود مدیر",
    "login.subtitle": "برای ورود به پنل مانیتورینگ، اطلاعات را وارد کنید.",
    "login.language.label": "زبان",
    "login.language.en": "انگلیسی",
    "login.language.fa": "فارسی",
    "login.username": "نام کاربری",
    "login.password": "رمز عبور",
    "login.button": "ورود",
    "login.footer": "پنل مانیتورینگ v2rayscan",
    
    // ---------- Settings ----------
    "settings.title": "تنظیمات عمومی",

    "settings.telegram_bot_token": "توکن ربات تلگرام",
    "settings.telegram_bot_token.placeholder": "توکن ربات تلگرام",

    "settings.telegram_chat_id": "chat_id مقصد",
    "settings.telegram_chat_id.placeholder": "chat_id مقصد",

    "settings.check_interval": "بازه چک کردن (ثانیه)",

    "settings.telegram.notify_recover":
      "ارسال نوتیف زمانی که سرور دوباره وصل شد",

    "settings.telegram.down_threshold":
      "تعداد تست ناموفق پیاپی برای اعلام DOWN بودن سرور",
    "settings.telegram.down_threshold.help":
      "مثلاً ۳ یعنی اگر ۳ بار پشت‌سرهم تست FAIL شد، پیام DOWN بفرست.",

    "settings.proxy.title": "تنظیمات پراکسی برای تلگرام",
    "settings.proxy.use_proxy": "ارسال پیام‌های تلگرام از طریق پراکسی",

    "settings.proxy.mode": "نوع پراکسی برای تلگرام",
    "settings.proxy.mode.none": "بدون پراکسی (مستقیم)",
    "settings.proxy.mode.socks": "پراکسی SOCKS5 خارجی",
    "settings.proxy.mode.server": "استفاده از یکی از سرورها (XRAY)",

    "settings.proxy.socks_host": "هاست SOCKS",
    "settings.proxy.socks_host.placeholder":
      "مثلاً 127.0.0.1 یا آدرس پراکسی",
    "settings.proxy.socks_port": "پورت SOCKS",
    "settings.proxy.socks_port.placeholder": "مثلاً 1080",

    "settings.proxy.socks_user": "نام کاربری SOCKS (اختیاری)",
    "settings.proxy.socks_pass": "رمز عبور SOCKS (اختیاری)",

    "settings.proxy.server_id": "ID سروری که به عنوان پراکسی تلگرام استفاده می‌شود",

    "settings.button.save": "ذخیره تنظیمات",
    "settings.status.ok": "تنظیمات ذخیره شد",
    "settings.status.error": "خطا در ذخیره تنظیمات",

    // ---------- Live monitor ----------
    "live.title": "رصد لحظه‌ای کانفیگ (از طریق XRAY)",
    "live.link.label": "لینک کانفیگ (vless:// یا vmess://)",
    "live.interval.label": "بازه نمونه‌برداری (ثانیه)",
    "live.start": "شروع رصد",
    "live.stop": "توقف",

    "live.metrics.total": "کل نمونه‌ها: ",
    "live.metrics.success": "موفق: ",
    "live.metrics.down": "Down: ",
    "live.metrics.success_rate": "درصد موفقیت: ",
    "live.metrics.avg_latency": "میانگین پینگ: ",
    "live.metrics.last_latency": "آخرین پینگ: ",
    "live.metrics.consecutive_down": "Down پیاپی: ",
    "live.metrics.last_error": "آخرین خطا: ",

    // ---------- Add server ----------
    "addserver.title": "افزودن سرور جدید",
    "addserver.name.label": "نام سرور (اختیاری)",
    "addserver.name.placeholder": "مثلاً Germany-1",
    "addserver.link.label": "لینک کانفیگ (vless/vmess/...)",
    "addserver.link.placeholder":
      "لینک کامل مثل vless://... را اینجا پیست کن",
    "addserver.button": "افزودن",
    "addserver.status.error_required": "لینک را وارد کن",
    "addserver.status.error": "خطا در افزودن سرور",
    "addserver.status.ok": "سرور اضافه شد",

    // ---------- Servers list / table ----------
    "servers.title": "لیست سرورها",

    "servers.column.id": "شناسه",
    "servers.column.name": "نام",
    "servers.column.group": "گروه",
    "servers.column.address": "آدرس",
    "servers.column.type": "نوع",
    "servers.column.raw_link": "لینک کامل",
    "servers.column.status": "وضعیت",
    "servers.column.latency": "پینگ",
    "servers.column.last_check": "آخرین چک",
    "servers.column.actions": "عملیات",

    "servers.action.toggle": "فعال / غیرفعال",
    "servers.action.test": "تست",
    "servers.action.chart": "گراف",
    "servers.action.monitor": "رصد لحظه‌ای",
    "servers.action.edit": "ویرایش",
    "servers.action.delete": "حذف",

    "servers.error.link_required": "لینک را وارد کن",
    "servers.error.add": "خطا در افزودن سرور",
    "servers.success.add": "سرور اضافه شد",
    "servers.error.toggle": "خطا در تغییر وضعیت سرور",
    "servers.error.delete": "خطا در حذف سرور",
    "servers.error.test": "خطا در تست سرور",
    "servers.confirm.delete": "سرور حذف شود؟",

    // ---------- Groups ----------
    "groups.new": "گروه جدید",
    "groups.all": "همه",
    "groups.ungrouped": "بدون گروه",
    "groups.actions.edit": "ویرایش گروه",
    "groups.actions.delete": "حذف گروه",
    "groups.prompt.new": "نام گروه جدید را وارد کنید:",
    "groups.prompt.color_new":
      "رنگ گروه (مثلاً #0ea5e9) - اختیاری:",
    "groups.prompt.rename": "نام جدید گروه:",
    "groups.prompt.color_edit":
      "رنگ گروه (مثلاً #0ea5e9):",
    "groups.confirm.delete":
      "گروه حذف شود؟ سرورها بدون گروه می‌شوند.",

    // ---------- Chart ----------
    "chart.title": "گراف وضعیت سرور",
    "chart.range.label": "بازه زمانی",
    "chart.range.60": "۱ ساعت اخیر",
    "chart.range.180": "۳ ساعت اخیر",
    "chart.range.720": "۱۲ ساعت اخیر",
    "chart.range.1440": "۲۴ ساعت اخیر",
    "chart.range.10080": "۷ روز اخیر",

    "chart.stats": "تعداد DOWN در این بازه: —",

    // ---------- Edit server modal ----------
    "edit.title": "ویرایش کانفیگ",
    "edit.name": "نام",
    "edit.group": "گروه",
    "edit.group.none": "بدون گروه",
    "edit.link": "لینک کامل (raw_link)",
    "edit.enabled": "فعال باشد",
    "edit.cancel": "انصراف",
    "edit.save": "ذخیره",

    // ---------- Monitor errors ----------
    "monitor.error.fetch_link": "خطا در دریافت لینک سرور",
    "monitor.error.unavailable":
      "تابع رصد لحظه‌ای در دسترس نیست",
    "monitor.error.start": "خطا در شروع رصد لحظه‌ای",

    // ---------- Common ----------
    "common.error.network": "خطا در ارتباط با سرور",
  },
};


let currentLang =
    window.localStorage.getItem("panel_lang") || DEFAULT_LANG;

function setLanguage(lang) {
    if (!TRANSLATIONS[lang]) {
        lang = DEFAULT_LANG;
    }
    currentLang = lang;
    window.localStorage.setItem("panel_lang", lang);

    // جهت صفحه
    const html = document.documentElement;
    if (lang === "fa") {
        html.setAttribute("lang", "fa");
        html.setAttribute("dir", "rtl");
    } else {
        html.setAttribute("lang", "en");
        html.setAttribute("dir", "ltr");
    }

    applyTranslations();
}

function t(key) {
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS[DEFAULT_LANG];
    return dict[key] || key;
}

function applyTranslations() {
    // همه‌ی المان‌هایی که data-i18n دارند
    document
        .querySelectorAll("[data-i18n]")
        .forEach((el) => {
            const key = el.getAttribute("data-i18n");
            const text = t(key);
            if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
                if (el.placeholder) {
                    el.placeholder = text;
                } else {
                    el.value = text;
                }
            } else if (el.tagName === "OPTION") {
                el.textContent = text;
            } else {
                el.textContent = text;
            }
        });

    // همه‌ی المان‌هایی که data-i18n-placeholder دارند
    document
        .querySelectorAll("[data-i18n-placeholder]")
        .forEach((el) => {
            const key = el.getAttribute("data-i18n-placeholder");
            el.placeholder = t(key);
        });
}

// سوییچر زبان روی تمام صفحات
function initLanguageSwitcher() {
    // selectهایی که نام کلاس lang-select دارند
    document
        .querySelectorAll(".lang-select")
        .forEach((sel) => {
            sel.value = currentLang;
            sel.addEventListener("change", () => {
                setLanguage(sel.value);
                // همه‌ی selectها sync شوند
                document
                    .querySelectorAll(".lang-select")
                    .forEach((s) => {
                        if (s !== sel) s.value = sel.value;
                    });
            });
        });
}

// روی load اولیه، تنظیم کن
document.addEventListener("DOMContentLoaded", () => {
    setLanguage(currentLang);
    initLanguageSwitcher();
});

// برای استفاده در سایر فایل‌ها
window.setLanguage = setLanguage;
window.t = t;
window.currentLang = () => currentLang;
