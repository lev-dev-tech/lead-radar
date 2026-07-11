#!/usr/bin/env python3
"""
Вход в расходный аккаунт (burner) для облачной автоматизации.
Запускаешь ТЫ сам, код из Telegram вводишь ТЫ сам в этом окне — я код не ввожу.

Заполни в credentials.py: BURNER_API_ID, BURNER_API_HASH, BURNER_PHONE
Запуск:
    PYTHONIOENCODING=utf-8 .venv\\Scripts\\python.exe login_burner.py
Введёшь номер (уже подставлен), код из Telegram, при 2FA — облачный пароль.
После "[OK] Вход выполнен" создастся burner_session.session.
"""
import asyncio

from telethon import TelegramClient

import config

SESSION = "burner_session"


async def main() -> None:
    if not config.BURNER_API_ID or not config.BURNER_API_HASH:
        print("[!] Заполни BURNER_API_ID и BURNER_API_HASH в credentials.py")
        return
    client = TelegramClient(SESSION, config.BURNER_API_ID, config.BURNER_API_HASH)
    await client.start(phone=lambda: config.BURNER_PHONE or input("Телефон: "))
    me = await client.get_me()
    print(f"\n[OK] Вход выполнен: {me.first_name} (@{me.username}) +{me.phone}")
    print("Готово. Скажи ассистенту — переключу уведомления и автоматизацию на этот аккаунт.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
