#!/usr/bin/env python3
"""
Читает свежие личные переписки аккаунта Льва (@levv_ddev) и складывает в inbox.json
для показа на сайте во вкладке «Ответы». Только личные чаты (не группы, не боты).
Ничего не отправляет и не помечает прочитанным - только читает.
"""
import asyncio
import io
import json
from datetime import datetime
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import User

import config

HERE = Path(__file__).resolve().parent
INBOX_FILE = HERE / "inbox.json"
LIMIT = 40


async def main() -> None:
    client = TelegramClient(config.LEV_SESSION, config.LEV_API_ID, config.LEV_API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("[inbox] сессия не авторизована"); await client.disconnect(); return

    items = []
    async for dialog in client.iter_dialogs(limit=LIMIT):
        ent = dialog.entity
        if not isinstance(ent, User):
            continue
        if ent.bot or ent.is_self or ent.deleted or ent.id == 777000:
            continue
        msg = dialog.message
        if msg is None:
            continue
        name = " ".join(filter(None, [ent.first_name, ent.last_name])) or "(без имени)"
        items.append({
            "name": name,
            "username": ent.username or "",
            "uid": ent.id,
            "text": (msg.message or "[вложение]")[:400],
            "date": msg.date.astimezone().strftime("%Y-%m-%d %H:%M"),
            "ts": msg.date.timestamp(),
            "unread": int(dialog.unread_count or 0),
            "incoming": not msg.out,   # последнее сообщение пришло от собеседника
        })

    items.sort(key=lambda x: x["ts"], reverse=True)
    io.open(INBOX_FILE, "w", encoding="utf-8").write(
        json.dumps(items, ensure_ascii=False, indent=1))
    unread = sum(1 for i in items if i["unread"])
    print(f"[inbox] переписок: {len(items)}, непрочитанных: {unread} ({datetime.now():%H:%M})")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
