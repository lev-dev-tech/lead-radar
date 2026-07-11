#!/usr/bin/env python3
"""
Напоминание Льву в Telegram (в «Избранное» / Saved Messages): пора зайти в сессию
к ассистенту и обновить лиды. Шлётся с его же аккаунта самому себе.
Запускается Планировщиком за ~10 минут до авто-обновления парсера.
"""
import asyncio
from datetime import datetime

from telethon import TelegramClient

import config

MSG = (
    "🔔 Через ~10 минут обновятся лиды.\n\n"
    "Зайди в сессию к ассистенту и напиши: обнови лиды\n\n"
    "Я соберу свежие заказы из твоих каналов и напишу персональный отклик "
    "под каждый - останется только скопировать и отправить."
)


async def main() -> None:
    # Отправляем с расходного аккаунта на основной — тогда приходит пуш.
    client = TelegramClient(config.NOTIFY_FROM_SESSION,
                            config.BURNER_API_ID, config.BURNER_API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("[notify] второй аккаунт не авторизован"); await client.disconnect(); return
    try:
        await client.send_message(config.NOTIFY_TO, MSG)
        print(f"[notify] отправлено на @{config.NOTIFY_TO} {datetime.now():%H:%M}")
    except Exception as e:
        print(f"[notify] ошибка отправки: {e}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
