#!/usr/bin/env python3
"""
Радар лидов: обновляет парсер вакансий, отбирает горячие заказы под стек Льва
(боты / mini app / GetCourse / парсеры / вебинары / автоматизация), пишет готовый
черновик отклика под каждый и складывает всё в заметку Obsidian с пометкой NEW.

Запуск:  PYTHONIOENCODING=utf-8 .venv\\Scripts\\python.exe lead_radar.py
Ничего не отправляет — только готовит. Отправляешь ты, вручную.
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

import config

HERE = Path(__file__).resolve().parent
SEEN_FILE = HERE / "seen_leads.json"
PORTFOLIO = "lev-dev-tech.github.io"

# Куда класть заметку с лидами (хранилище Obsidian)
OBSIDIAN_NOTE = Path(r"D:\obsidian\проекты\1\Горячие лиды (авто).md")
# Приложение-дашборд (открывается двойным кликом в браузере) — локальное, с «Ответами»
HTML_FILE = HERE / "Лиды.html"
# Публичная версия для GitHub Pages: только «Заказы», с паролем, БЕЗ личных переписок
PUBLIC_FILE = HERE / "docs" / "index.html"

# --- Классификация заказа по теме -------------------------------------------
CATEGORIES = [
    ("miniapp",  ["mini app", "mini-app", "миниапп", "мини апп", "мини-апп"]),
    ("getcourse", ["геткурс", "getcourse", "гет курс"]),
    ("crm",      ["bitrix", "битрикс", "amocrm", "амосрм", "amo crm", " crm", "црм"]),
    ("webinar",  ["вебинар", "автовебинар"]),
    ("parser",   ["парсер", "парсинг", "спарсить", "скрап", "выгруз"]),
    ("ai",       ["ии-агент", "ии агент", "ai-агент", "ai агент", "нейросет", "нейронк",
                  "искусственн интеллект", "промпт под"]),
    ("bot",      ["бот", "aiogram", "telethon", "чат-бот", "чатбот", "mini app"]),
    ("site",     ["лендинг", "веб-приложение", "web-app", "интернет-магазин"]),
]

# Признаки того, что это КЛИЕНТ ищет исполнителя (а не фрилансер рекламирует себя)
CLIENT_INTENT = [
    "ищу", "ищем", "нужен", "нужна", "нужно", "требуется", "требуются",
    "в команду", "на проект", "кто сделает", "кто возьм", "кто может",
    "заказ", "вакансия", "сделать", "настроить", "разработать", "бюджет",
]

# Признаки рекламы конкурента-фрилансера — такие пропускаем
COMPETITOR_ADS = [
    "предоставляю услуги", "мои услуги", "предлагаю услуги", "предлагаю свои",
    "я разработчик", "я программист", "я python", "я веб-разработчик",
    "я full", "full-stack разработчик", "fullstack", "услуги кодера",
    "разрабатываем", "берёмся за задачи", "беремся за задачи",
    "стоимость проекта от", "разработка под ключ от", "занимаюсь программированием",
    "готовые проекты:", "услуги full", "услуги разработчика",
    "я технический специалист", "я техспец", "меня зовут", "могу взять на себя",
    "какие задачи я могу", "я знаю как настроить", "возьму заказ", "беру заказы",
    "чем занимаюсь", "о себе:", "javascript/python developer", "python developer",
]

# Грязь/серые темы — пропускаем
GREY = [
    "adult", "адалт", "модельн", "скаут", "usdt за реферала", "стримит",
    "рассылка по", "рассылки по чатам", "инвайтинг", "спам", "разблокировк инстаграм",
    "gambling", "igaming", "gambling", "media buyer", "медиабайер", "медиа байер",
    "байер", "казино", "беттинг", "betting",
]

# Не наши роли (даже если есть тех-слово) — ассистенты, продажи, дизайн, закупщики
NONFIT_ROLES = [
    "ассистент в instagram", "ассистент в инстаграм", "по готовым скриптам",
    "готовыми скриптами", "на рассылки", "ассистента в рекламное",
    "отправлять сообщения в директ", "комментинг",
    "менеджер по прода", "менеджера по прода", "менеджеров по прода",
    "менеджер отдела продаж", "отдела продаж", "менеджеров на удал",
    "sales-менеджер", "sales менеджер", "b2b sales", "sales‑менеджер",
    "заряженного менеджера", "куратор в онлайн", "администратор-куратор",
    "закупщик", "закупщика", "закупщиков",
    "графический дизайнер", "ищем дизайнер", "нужен дизайнер", "арбитражник",
    "таргетолог", "бизнес-ассистент", "лидогенератор", "рассыльщик",
    "angular разработчик", "штатного", "штатный",
]

# Заказ уже закрыт — исполнитель выбран
TAKEN = ["выбран исполнитель", "исполнитель выбран", "закрыт", "закрыта вакансия"]


def low(s: str) -> str:
    return (s or "").lower()


def has_any(text: str, words: list[str]) -> list[str]:
    t = low(text)
    return [w for w in words if w in t]


def classify(text: str) -> str | None:
    for cat, words in CATEGORIES:
        if has_any(text, words):
            return cat
    return None


def is_client_order(text: str) -> bool:
    if has_any(text, COMPETITOR_ADS):
        return False
    if has_any(text, GREY):
        return False
    if has_any(text, NONFIT_ROLES):
        return False
    if has_any(text, TAKEN):
        return False
    return bool(has_any(text, CLIENT_INTENT))


# --- Черновики откликов по категориям ---------------------------------------
BODIES = {
    "bot": (
        'Увидел, что вам нужен Telegram-бот, готов взяться. Сделаю бота на Python (aiogram): '
        'продумаю сценарии и логику диалога, подключу базу данных, при необходимости - приём '
        'оплаты, рассылки и уведомления, соберу простую аналитику по действиям пользователей. '
        'Работаю по короткому ТЗ, с фиксированной ценой и сроком, держу на связи на каждом '
        'этапе и не пропадаю после сдачи. Небольшой бот обычно занимает 3-5 дней, задачу '
        'покрупнее разобью на понятные этапы.',
        'Расскажите подробнее, что должен уметь бот, - предложу оптимальное решение и назову цену.'),
    "miniapp": (
        'Смотрю, нужен Telegram mini app - это как раз моя тема. Сделаю полноценное '
        'веб-приложение внутри Telegram: интерфейс, каталог, корзину и оформление, подключу '
        'оплату и свяжу с базой или вашей CRM, чтобы заявки и заказы попадали куда нужно. '
        'Заложу структуру так, чтобы потом легко добавлять новые разделы, товары и функции '
        'без переделки. Делал mini app с оплатой и ботов с каталогом, так что подводные '
        'камни знаю.',
        'Опишите проект подробнее - предложу, как лучше реализовать, и назову сроки и цену.'),
    "getcourse": (
        'Вижу, нужна настройка GetCourse - помогу. Настрою приём оплат и подключение '
        'платёжных систем, соберу воронки и автоворонки, письма и рассылки, выдачу доступов '
        'к продуктам и нужные интеграции с ботами, сайтом или CRM. Проверю, чтобы вся цепочка '
        'от заявки до оплаты и выдачи доступа работала без сбоев, и подскажу, где процесс '
        'можно упростить. Работаю по ТЗ, с понятными сроками и фиксированной ценой.',
        'Напишите, что именно нужно настроить, - сориентирую по срокам и цене.'),
    "crm": (
        'Заинтересовала задача - работаю с CRM и автоматизацией бизнес-процессов. Настрою '
        'воронки и этапы сделок, автоматизацию рутинных действий, интеграции с сайтом, '
        'ботами и телефонией, приведу в порядок логику обработки заявок, чтобы ничего не '
        'терялось. Мне важно не просто "настроить систему", а выстроить реальный процесс '
        'продаж под вашу команду и перевести бизнес-задачи в конкретные технические решения. '
        'Умею общаться с заказчиком, разбирать нестандартные задачи и доводить до удобного '
        'для команды результата.',
        'Расскажите про ваши процессы и что хотите улучшить - предложу решение и сроки.'),
    "webinar": (
        'Готов взять техническое сопровождение вебинара под ключ. Настрою площадку и '
        'трансляцию, страницу и форму регистрации, автоматическую выдачу доступов и '
        'напоминания участникам, заранее проверю всю связку и звук. На самом эфире буду на '
        'подстраховке, чтобы при любой заминке всё быстро починить, а вы спокойно вели '
        'вебинар. Если нужен автовебинар - настрою расписание и автозапуск, чтобы он шёл '
        'сам по графику.',
        'Подскажите платформу, дату и формат (живой или авто) - включусь и назову цену.'),
    "parser": (
        'Вижу, нужен парсер - соберу под вашу задачу. Настрою сбор нужных данных с сайтов '
        'или каналов, их обработку и очистку, выгрузку в удобном виде (Excel или Google '
        'Sheets) с автоматическим обновлением по расписанию. Обойду простые блокировки и '
        'сделаю так, чтобы данные собирались стабильно и без вашего участия. Писал парсеры '
        'на Python (BeautifulSoup, Selenium) с выгрузкой и фильтрацией - подобное делал не раз.',
        'Опишите источник и какие поля нужны - предложу решение, сроки и цену.'),
    "ai": (
        'Заинтересовала задача с ИИ, готов помочь. Разберу процессы и рутинные задачи, '
        'подберу подходящие нейросети и готовые связки под конкретные функции, настрою '
        'автоматизацию и, если нужно, соберу ИИ-агента или бота под ваши сценарии. Отдельно '
        'покажу команде, как этим реально пользоваться в работе, а не просто отдам список '
        'сервисов. Работаю по задачам и в рамках бюджета, с понятным планом и результатом.',
        'Опишите, какие процессы хотите автоматизировать, - предложу план и сроки.'),
    "site": (
        'Вижу, нужен сайт или лендинг - сделаю. Соберу чистую адаптивную страницу, которая '
        'хорошо смотрится и на телефоне, и на компьютере, со светлой и тёмной темой, быстрой '
        'загрузкой и понятной структурой под ваши цели. Подключу формы заявок, аналитику и '
        'всё, что нужно для сбора лидов. Работаю по ТЗ, с фиксированной ценой и сроком.',
        'Опишите, что за сайт и сколько блоков нужно, - назову цену и срок.'),
}
GENERIC_BODY = (
    'Готов взяться за вашу техническую задачу. Разберусь в деталях, предложу оптимальное '
    'решение и реализую его под ключ - аккуратно, по ТЗ, с фиксированной ценой и сроком. '
    'Держу на связи на каждом этапе и не пропадаю после сдачи, при необходимости беру '
    'проект на сопровождение. Работаю с ботами, парсерами, mini app, сайтами, CRM и '
    'автоматизацией, так что подберу подходящий под задачу подход.',
    'Опишите задачу подробнее - предложу решение, сроки и цену.')


_AI_SYSTEM = (
    "Ты - Лев, фриланс-разработчик. Стек: Python, Telegram-боты (aiogram) и mini app, "
    "парсеры, автоматизация, GetCourse, CRM/Bitrix, лендинги. Пишешь отклик на заказ от "
    "первого лица. Требования к отклику: живой человеческий тон без канцелярита и клише; "
    "4-5 предложений про то, что конкретно ты сделаешь именно по этой задаче; затем с новой "
    "строки 'Портфолио: lev-dev-tech.github.io'; затем с новой строки короткий вопрос-CTA. "
    "Только прямые кавычки \" и обычное тире -, без длинного тире и ёлочек. Без выдумок про "
    "несуществующий опыт и без указания конкретных цен. Верни только текст отклика."
)


def ai_draft(cat: str, name_hint: str, text: str) -> str | None:
    key = getattr(config, "ANTHROPIC_API_KEY", "").strip()
    if not key or not text.strip():
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        who = f"Обращайся по имени: {name_hint}. " if name_hint else "Имя заказчика неизвестно. "
        msg = client.messages.create(
            model=getattr(config, "AI_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=450,
            system=_AI_SYSTEM,
            messages=[{"role": "user", "content":
                       f"{who}Категория задачи: {CAT_RU.get(cat, cat)}.\n"
                       f"Текст заказа:\n{text[:1200]}"}],
        )
        out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        return out or None
    except Exception as e:
        print(f"[radar] AI-черновик недоступен, использую шаблон: {e}")
        return None


def draft(cat: str, name_hint: str, text: str = "") -> str:
    hi = f"Здравствуйте, {name_hint}!" if name_hint else "Здравствуйте!"
    ai = ai_draft(cat, name_hint, text)   # тексто-специфичный вариант, если есть API-ключ
    if ai:
        return ai
    body, cta = BODIES.get(cat, GENERIC_BODY)
    return f"{hi}\n\n{body}\n\nПортфолио: {PORTFOLIO}\n\n{cta}"


def name_from_contact(contact: str) -> str:
    """Достаём имя для приветствия, если оно человеческое (не @username/телефон)."""
    if not contact:
        return ""
    head = contact.split("(")[0].split("/")[0].strip()
    if head.startswith("@") or any(c.isdigit() for c in head) or not head:
        return ""
    first = head.split()[0]
    if 2 <= len(first) <= 20 and first.replace("-", "").isalpha():
        return first
    return ""


def load_seen() -> set[str]:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_seen(seen: set[str]) -> None:
    SEEN_FILE.write_text(json.dumps(sorted(seen), ensure_ascii=False), encoding="utf-8")


def _venv_py() -> str:
    py = HERE / ".venv" / "Scripts" / "python.exe"
    return str(py) if py.exists() else sys.executable


def refresh_parser() -> None:
    """Запускаем парсер, чтобы обновить xlsx свежими вакансиями."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    print("[radar] Обновляю вакансии (парсер)…")
    r = subprocess.run([_venv_py(), str(HERE / "parser.py")], cwd=str(HERE), env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = "\n".join(l for l in (r.stdout or "").splitlines()
                     if l.startswith("[+]") or l.startswith("[!]"))
    print(tail or "[radar] парсер отработал")


def refresh_inbox() -> None:
    """Читаем входящие личные сообщения аккаунта Льва (вкладка «Ответы»)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([_venv_py(), str(HERE / "inbox.py")], cwd=str(HERE), env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    for l in (r.stdout or "").splitlines():
        if l.startswith("[inbox]"):
            print(l)


def load_inbox() -> list[dict]:
    f = HERE / "inbox.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def load_overrides() -> dict:
    """Ручные (написанные ассистентом в сессии) отклики: {ссылка: текст}.
    Имеют приоритет над шаблоном и переживают авто-обновления."""
    f = HERE / "drafts_override.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def collect_hot() -> list[dict]:
    xlsx = HERE / config.OUTPUT_FILE
    if not xlsx.exists():
        print("[radar] нет файла с вакансиями"); return []
    overrides = load_overrides()
    wb = openpyxl.load_workbook(xlsx)
    ws = wb.active
    hot = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        cells = (list(row) + [None] * 6)[:6]
        _, contact, link, chat, date, text = cells
        text = str(text or "")
        link = str(link or "")
        if not is_client_order(text):
            continue
        cat = classify(text)
        if not cat:
            continue
        hot.append({
            "contact": str(contact or "(не указан)"),
            "link": link,
            "chat": str(chat or ""),
            "date": str(date or ""),
            "text": text.strip(),
            "cat": cat,
            "draft": overrides.get(link) or draft(cat, name_from_contact(str(contact or "")), text),
        })
    hot.sort(key=lambda r: r["date"], reverse=True)
    return hot


CAT_RU = {"miniapp": "Mini App", "getcourse": "GetCourse", "crm": "CRM/Bitrix",
          "webinar": "Вебинар", "parser": "Парсер/выгрузка", "ai": "ИИ/автоматизация",
          "bot": "Telegram-бот", "site": "Сайт/лендинг"}


def write_note(hot: list[dict], seen: set[str]) -> tuple[int, int]:
    new = [h for h in hot if h["link"] and h["link"] not in seen]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def block(h: dict) -> str:
        tprev = h["text"][:280] + ("…" if len(h["text"]) > 280 else "")
        quoted = h["draft"].replace("\n", "\n> ")
        return (f"### [{CAT_RU.get(h['cat'], h['cat'])}] {h['chat']} · {h['date']}\n"
                f"- **Контакт:** {h['contact']}\n"
                f"- **Ссылка:** {h['link']}\n"
                f"- **Заказ:** {tprev}\n"
                f"- **Черновик отклика:**\n> {quoted}\n")

    out = io.StringIO()
    out.write(f"# 🛰 Горячие лиды (авто) — обновлено {now}\n\n")
    out.write("> Готовит радар лидов. Ничего не отправлено — копируй черновик и "
              "отправляй **сам, вручную, по одному**.\n\n")
    out.write(f"**Новых с прошлого запуска: {len(new)} · всего актуальных: {len(hot)}**\n\n")
    if new:
        out.write("## 🆕 Новые\n\n")
        for h in new:
            out.write(block(h) + "\n")
    out.write("## 📋 Все актуальные\n\n")
    for h in hot:
        out.write(block(h) + "\n")

    OBSIDIAN_NOTE.parent.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_NOTE.write_text(out.getvalue(), encoding="utf-8")

    for h in hot:
        if h["link"]:
            seen.add(h["link"])
    save_seen(seen)
    return len(new), len(hot)


HTML_TEMPLATE = r"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="1800">
<title>Лиды — Lev Dev</title>
<style>
  :root{--bg:#0f1420;--card:#1a2236;--mut:#8a97b3;--txt:#e8edf7;--acc:#4f8cff;
        --new:#22c55e;--chip:#243050;--chipa:#4f8cff;--box:#111830;--bd:#2a3550}
  @media (prefers-color-scheme:light){
    :root{--bg:#f4f6fb;--card:#fff;--mut:#5a6785;--txt:#141a2b;--acc:#2f6bff;
          --new:#16a34a;--chip:#e7ecf7;--chipa:#2f6bff;--box:#f0f3fa;--bd:#dbe2f0}}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
       font:15px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif}
  header{position:sticky;top:0;background:var(--bg);padding:16px 18px 10px;
         border-bottom:1px solid var(--bd);z-index:5}
  h1{margin:0 0 2px;font-size:20px}
  .sub{color:var(--mut);font-size:13px}
  .bar{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;align-items:center}
  .chip{background:var(--chip);color:var(--txt);border:0;border-radius:20px;
        padding:6px 13px;font-size:13px;cursor:pointer}
  .chip.on{background:var(--chipa);color:#fff}
  input[type=search]{flex:1;min-width:160px;background:var(--card);color:var(--txt);
        border:1px solid var(--bd);border-radius:20px;padding:7px 14px;font-size:14px}
  label.tgl{display:flex;gap:6px;align-items:center;color:var(--mut);font-size:13px;cursor:pointer}
  main{padding:16px 18px 60px;max-width:900px;margin:0 auto}
  .card{background:var(--card);border:1px solid var(--bd);border-radius:14px;
        padding:15px 16px;margin-bottom:14px}
  .top{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:8px}
  .badge{font-size:12px;font-weight:600;background:var(--chip);color:var(--acc);
         padding:3px 9px;border-radius:8px}
  .new{background:var(--new);color:#fff}
  .meta{color:var(--mut);font-size:12px;margin-left:auto}
  .contact{font-weight:600;margin:2px 0 8px}
  .contact a{color:var(--acc);text-decoration:none}
  .order{color:var(--mut);font-size:13.5px;white-space:pre-wrap;max-height:78px;
         overflow:hidden;position:relative;cursor:pointer}
  .order.open{max-height:none}
  .order.clip:after{content:"… показать";color:var(--acc);position:absolute;right:0;bottom:0;
         background:var(--card);padding-left:8px;font-size:12px}
  .draftbox{background:var(--box);border:1px solid var(--bd);border-radius:10px;
        padding:11px 12px;margin-top:10px;white-space:pre-wrap;font-size:14px}
  .acts{display:flex;gap:8px;margin-top:9px;flex-wrap:wrap}
  .btn{background:var(--acc);color:#fff;border:0;border-radius:9px;padding:8px 14px;
       font-size:13.5px;cursor:pointer;text-decoration:none;display:inline-block}
  .btn.ghost{background:transparent;border:1px solid var(--bd);color:var(--txt)}
  .empty{color:var(--mut);text-align:center;padding:40px}
  .tabs{display:flex;gap:8px;margin-top:12px}
  .tab{background:var(--chip);color:var(--txt);border:0;border-radius:20px;
       padding:8px 16px;font-size:14px;font-weight:600;cursor:pointer}
  .tab.on{background:var(--chipa);color:#fff}
  .unread{background:#ef4444;color:#fff}
  .msg{color:var(--txt);font-size:14px;white-space:pre-wrap;margin:6px 0}
  .hide{display:none}
</style>
</head>
<body>
<header>
  <h1>🛰 Лиды — Lev Dev</h1>
  <div class="sub">Обновлено __UPDATED__ · <span id="cnt"></span></div>
  <div class="tabs">
    <button class="tab on" id="tabOrders">📋 Заказы</button>
    <button class="tab" id="tabInbox">💬 Ответы</button>
  </div>
  <div class="bar" id="chips"></div>
  <div class="bar" id="searchbar">
    <input type="search" id="q" placeholder="Поиск по тексту, чату, контакту…">
    <label class="tgl"><input type="checkbox" id="onlynew"> только новые</label>
  </div>
</header>
<main>
  <div id="list"></div>
  <div id="inbox" class="hide"></div>
</main>
<script>
const DATA = __DATA__;
const INBOX = __INBOX__;
const list=document.getElementById('list'), inboxEl=document.getElementById('inbox');
const chipsEl=document.getElementById('chips'), searchbar=document.getElementById('searchbar');
let cat='Все', q='', onlyNew=false;
const cats=['Все',...[...new Set(DATA.map(d=>d.cat))]];
const nNew=DATA.filter(d=>d.isNew).length;
const nUnread=INBOX.filter(m=>m.unread>0).length;
document.getElementById('cnt').textContent=
  `заказов ${DATA.length} (новых ${nNew}) · ответов ${INBOX.length} (непрочитанных ${nUnread})`;
document.getElementById('tabInbox').textContent=`💬 Ответы${nUnread?' ('+nUnread+')':''}`;

cats.forEach(c=>{const b=document.createElement('button');b.className='chip'+(c===cat?' on':'');
  b.textContent=c;b.onclick=()=>{cat=c;[...chipsEl.children].forEach(x=>x.classList.remove('on'));
  b.classList.add('on');renderOrders()};chipsEl.appendChild(b)});
document.getElementById('q').oninput=e=>{q=e.target.value.toLowerCase();renderOrders()};
document.getElementById('onlynew').onchange=e=>{onlyNew=e.target.checked;renderOrders()};

const tO=document.getElementById('tabOrders'), tI=document.getElementById('tabInbox');
tO.onclick=()=>switchTab('orders');
tI.onclick=()=>switchTab('inbox');
function switchTab(w){
  const orders=w==='orders';
  tO.classList.toggle('on',orders); tI.classList.toggle('on',!orders);
  list.classList.toggle('hide',!orders); inboxEl.classList.toggle('hide',orders);
  chipsEl.classList.toggle('hide',!orders); searchbar.classList.toggle('hide',!orders);
}

function tg(contact){const m=(contact||'').match(/@([A-Za-z][A-Za-z0-9_]{3,31})/);
  return m?`https://t.me/${m[1]}`:null}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}

function renderOrders(){
  let rows=DATA.filter(d=>(cat==='Все'||d.cat===cat)&&(!onlyNew||d.isNew)&&
    (!q||(d.text+d.chat+d.contact+d.draft).toLowerCase().includes(q)));
  if(!rows.length){list.innerHTML='<div class="empty">Ничего не найдено</div>';return}
  list.innerHTML=rows.map((d,i)=>{
    const t=tg(d.contact);
    const contact=t?`<a href="${t}" target="_blank">${esc(d.contact)}</a>`:esc(d.contact);
    const src=d.link?`<a class="btn ghost" href="${d.link}" target="_blank">Открыть заказ ↗</a>`:'';
    return `<div class="card">
      <div class="top"><span class="badge">${esc(d.cat)}</span>
        ${d.isNew?'<span class="badge new">NEW</span>':''}
        <span class="meta">${esc(d.chat)} · ${esc(d.date)}</span></div>
      <div class="contact">${contact}</div>
      <div class="order clip" onclick="this.classList.toggle('open');this.classList.remove('clip')">${esc(d.text)}</div>
      <div class="draftbox" id="d${i}">${esc(d.draft)}</div>
      <div class="acts">
        <button class="btn" onclick="copy('d'+${i},this)">📋 Копировать отклик</button>
        ${src}
      </div></div>`}).join('');
}

function renderInbox(){
  if(!INBOX.length){inboxEl.innerHTML='<div class="empty">Пока нет переписок</div>';return}
  inboxEl.innerHTML=INBOX.map((m,i)=>{
    const u=m.username?`https://t.me/${m.username}`:`tg://user?id=${m.uid}`;
    const who=m.username?'@'+m.username:'id '+m.uid;
    const dir=m.incoming?'':'<span class="meta">вы ответили</span>';
    return `<div class="card">
      <div class="top">
        ${m.unread>0?'<span class="badge unread">НЕПРОЧИТАНО '+m.unread+'</span>':(m.incoming?'<span class="badge new">ОТВЕТИЛИ</span>':'')}
        <span class="meta">${esc(m.date)}</span></div>
      <div class="contact"><a href="${u}" target="_blank">${esc(m.name)}</a> · ${esc(who)}</div>
      <div class="msg" id="m${i}">${esc(m.text)}</div>
      <div class="acts">
        <a class="btn" href="${u}" target="_blank">Открыть чат ↗</a>
        <button class="btn ghost" onclick="copy('m'+${i},this)">📋 Скопировать сообщение</button>
      </div></div>`}).join('');
}

function copy(id,btn){navigator.clipboard.writeText(document.getElementById(id).textContent)
  .then(()=>{const o=btn.textContent;btn.textContent='✅ Скопировано';setTimeout(()=>btn.textContent=o,1400)})}

renderOrders(); renderInbox();
</script>
</body>
</html>"""


PUBLIC_TEMPLATE = r"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="1800">
<title>Лиды — Lev Dev</title>
<style>
  :root{--bg:#0f1420;--card:#1a2236;--mut:#8a97b3;--txt:#e8edf7;--acc:#4f8cff;
        --new:#22c55e;--chip:#243050;--chipa:#4f8cff;--box:#111830;--bd:#2a3550}
  @media (prefers-color-scheme:light){
    :root{--bg:#f4f6fb;--card:#fff;--mut:#5a6785;--txt:#141a2b;--acc:#2f6bff;
          --new:#16a34a;--chip:#e7ecf7;--chipa:#2f6bff;--box:#f0f3fa;--bd:#dbe2f0}}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
       font:15px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif}
  header{position:sticky;top:0;background:var(--bg);padding:16px 18px 10px;
         border-bottom:1px solid var(--bd);z-index:5}
  h1{margin:0 0 2px;font-size:20px}
  .sub{color:var(--mut);font-size:13px}
  .bar{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;align-items:center}
  .chip{background:var(--chip);color:var(--txt);border:0;border-radius:20px;
        padding:6px 13px;font-size:13px;cursor:pointer}
  .chip.on{background:var(--chipa);color:#fff}
  input[type=search]{flex:1;min-width:160px;background:var(--card);color:var(--txt);
        border:1px solid var(--bd);border-radius:20px;padding:7px 14px;font-size:14px}
  main{padding:16px 18px 60px;max-width:900px;margin:0 auto}
  .card{background:var(--card);border:1px solid var(--bd);border-radius:14px;
        padding:15px 16px;margin-bottom:14px}
  .top{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:8px}
  .badge{font-size:12px;font-weight:600;background:var(--chip);color:var(--acc);
         padding:3px 9px;border-radius:8px}
  .new{background:var(--new);color:#fff}
  .meta{color:var(--mut);font-size:12px;margin-left:auto}
  .contact{font-weight:600;margin:2px 0 8px}
  .contact a{color:var(--acc);text-decoration:none}
  .order{color:var(--mut);font-size:13.5px;white-space:pre-wrap;max-height:78px;
         overflow:hidden;cursor:pointer}
  .order.open{max-height:none}
  .draftbox{background:var(--box);border:1px solid var(--bd);border-radius:10px;
        padding:11px 12px;margin-top:10px;white-space:pre-wrap;font-size:14px}
  .acts{display:flex;gap:8px;margin-top:9px;flex-wrap:wrap}
  .btn{background:var(--acc);color:#fff;border:0;border-radius:9px;padding:8px 14px;
       font-size:13.5px;cursor:pointer;text-decoration:none;display:inline-block}
  .btn.ghost{background:transparent;border:1px solid var(--bd);color:var(--txt)}
  .empty{color:var(--mut);text-align:center;padding:40px}
  #gate{position:fixed;inset:0;background:var(--bg);z-index:20;display:flex;
        flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:20px}
  #gate input{background:var(--card);color:var(--txt);border:1px solid var(--bd);
        border-radius:12px;padding:12px 16px;font-size:16px;text-align:center;width:220px}
  #gate .btn{padding:11px 22px;font-size:15px}
</style>
</head>
<body>
<div id="gate">
  <div style="font-size:34px">🔒</div>
  <div style="font-weight:600">Лиды — Lev Dev</div>
  <input type="password" id="pw" placeholder="Пароль" autofocus>
  <button class="btn" onclick="checkpw()">Войти</button>
  <div id="err" class="sub" style="color:#ef4444;min-height:18px"></div>
</div>
<div id="app" style="display:none">
<header>
  <h1>🛰 Лиды — Lev Dev</h1>
  <div class="sub">Обновлено __UPDATED__ · <span id="cnt"></span></div>
  <div class="bar" id="chips"></div>
  <div class="bar">
    <input type="search" id="q" placeholder="Поиск по тексту, чату, контакту…">
  </div>
</header>
<main id="list"></main>
</div>
<script>
const PW = "__PW__";
const DATA = __DATA__;
function checkpw(){
  const v=document.getElementById('pw').value;
  if(v===PW){try{localStorage.setItem('leadpw',v)}catch(e){}; open_app();}
  else document.getElementById('err').textContent='Неверный пароль';
}
document.getElementById('pw').addEventListener('keydown',e=>{if(e.key==='Enter')checkpw()});
function open_app(){
  document.getElementById('gate').style.display='none';
  document.getElementById('app').style.display='block';
  init();
}
let cat='Все', q='';
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function tg(contact){const m=(contact||'').match(/@([A-Za-z][A-Za-z0-9_]{3,31})/);
  return m?`https://t.me/${m[1]}`:null}
function init(){
  const chipsEl=document.getElementById('chips');
  const cats=['Все',...[...new Set(DATA.map(d=>d.cat))]];
  const nNew=DATA.filter(d=>d.isNew).length;
  document.getElementById('cnt').textContent=`заказов ${DATA.length}, новых ${nNew}`;
  cats.forEach(c=>{const b=document.createElement('button');b.className='chip'+(c===cat?' on':'');
    b.textContent=c;b.onclick=()=>{cat=c;[...chipsEl.children].forEach(x=>x.classList.remove('on'));
    b.classList.add('on');render()};chipsEl.appendChild(b)});
  document.getElementById('q').oninput=e=>{q=e.target.value.toLowerCase();render()};
  render();
}
function render(){
  const list=document.getElementById('list');
  let rows=DATA.filter(d=>(cat==='Все'||d.cat===cat)&&
    (!q||(d.text+d.chat+d.contact+d.draft).toLowerCase().includes(q)));
  if(!rows.length){list.innerHTML='<div class="empty">Ничего не найдено</div>';return}
  list.innerHTML=rows.map((d,i)=>{
    const t=tg(d.contact);
    const contact=t?`<a href="${t}" target="_blank">${esc(d.contact)}</a>`:esc(d.contact);
    const src=d.link?`<a class="btn ghost" href="${d.link}" target="_blank">Открыть заказ ↗</a>`:'';
    return `<div class="card">
      <div class="top"><span class="badge">${esc(d.cat)}</span>
        ${d.isNew?'<span class="badge new">NEW</span>':''}
        <span class="meta">${esc(d.chat)} · ${esc(d.date)}</span></div>
      <div class="contact">${contact}</div>
      <div class="order" onclick="this.classList.toggle('open')">${esc(d.text)}</div>
      <div class="draftbox" id="d${i}">${esc(d.draft)}</div>
      <div class="acts">
        <button class="btn" onclick="copy('d'+${i},this)">📋 Копировать отклик</button>
        ${src}
      </div></div>`}).join('');
}
function copy(id,btn){navigator.clipboard.writeText(document.getElementById(id).textContent)
  .then(()=>{const o=btn.textContent;btn.textContent='✅ Скопировано';setTimeout(()=>btn.textContent=o,1400)})}
// Авто-вход, если пароль уже сохранён (в самом конце — после инициализации всех переменных)
try{if(localStorage.getItem('leadpw')===PW) open_app();}catch(e){}
</script>
</body>
</html>"""


def write_public_html(hot: list[dict], new_links: set[str]) -> None:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    data = [{
        "cat": CAT_RU.get(h["cat"], h["cat"]), "chat": h["chat"], "date": h["date"],
        "contact": h["contact"], "link": h["link"], "text": h["text"],
        "draft": h["draft"], "isNew": h["link"] in new_links,
    } for h in hot]
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    pw = json.dumps(getattr(config, "PUBLIC_PASSWORD", "lead2026"))[1:-1]
    html = (PUBLIC_TEMPLATE.replace("__UPDATED__", now)
            .replace("__DATA__", payload).replace("__PW__", pw))
    PUBLIC_FILE.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_FILE.write_text(html, encoding="utf-8")


def write_html(hot: list[dict], new_links: set[str], inbox: list[dict]) -> None:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    data = []
    for h in hot:
        data.append({
            "cat": CAT_RU.get(h["cat"], h["cat"]),
            "chat": h["chat"],
            "date": h["date"],
            "contact": h["contact"],
            "link": h["link"],
            "text": h["text"],
            "draft": h["draft"],
            "isNew": h["link"] in new_links,
        })
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    inbox_payload = json.dumps(inbox, ensure_ascii=False).replace("</", "<\\/")
    html = (HTML_TEMPLATE.replace("__UPDATED__", now)
            .replace("__DATA__", payload)
            .replace("__INBOX__", inbox_payload))
    HTML_FILE.write_text(html, encoding="utf-8")


def main() -> None:
    cloud = os.getenv("RADAR_ACCOUNT", "lev").lower() == "burner"
    if "--no-refresh" not in sys.argv:
        refresh_parser()
        if not cloud:            # вкладка «Ответы» читает основной аккаунт — только локально
            refresh_inbox()
    seen = load_seen()
    hot = collect_hot()
    inbox = load_inbox()
    new_links = {h["link"] for h in hot if h["link"] and h["link"] not in seen}
    # Защита: не затирать сайт пустой страницей, если парсинг вернул 0 заказов
    # (например, аккаунт временно ограничен). Оставляем прошлую рабочую версию.
    if hot:
        write_public_html(hot, new_links)
    else:
        print("[radar] Заказов 0 — публичный сайт НЕ переписываю, оставляю прошлую версию.")
    if cloud:
        n_new, n_all = len(new_links), len(hot)
    else:
        write_html(hot, new_links, inbox)
        n_new, n_all = write_note(hot, seen)
    unread = sum(1 for i in inbox if i.get("unread"))
    print(f"[radar] Готово: заказов {n_all} (новых {n_new}), переписок {len(inbox)} "
          f"(непрочитанных {unread})")
    print(f"[radar] Сайт: {PUBLIC_FILE}")


if __name__ == "__main__":
    main()
