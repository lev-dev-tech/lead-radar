#!/usr/bin/env python3
"""
Вход в аккаунт Льва (@levv_ddev) по QR-коду — БЕЗ передачи кода кому-либо.
Секрет остаётся у тебя в телефоне: ты просто сканируешь QR своим Telegram.

Запуск:
    PYTHONIOENCODING=utf-8 .venv\\Scripts\\python.exe login_lev.py

Как войти:
    1. Запусти команду выше — откроется картинка qr_lev.png (и QR в терминале).
    2. Телефон -> Telegram -> Настройки -> Устройства -> Подключить устройство.
    3. Наведи камеру на QR. Всё. Если стоит облачный пароль (2FA) — введёшь его
       сам в этом окне.
    4. Появится "[OK] Вход выполнен" — напиши мне, я переключу парсер на твою папку.
"""
import asyncio
import os
import webbrowser

import qrcode
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

import config

SESSION = config.LEV_SESSION
QR_PNG = "qr_lev.png"


def show_qr(url: str) -> None:
    img = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                        box_size=14, border=4)
    img.add_data(url)
    img.make(fit=True)
    img.make_image(fill_color="black", back_color="white").save(QR_PNG)
    path = os.path.abspath(QR_PNG)
    print(f"\n[QR] Картинка сохранена: {path}")
    try:
        webbrowser.open(path)
    except Exception:
        pass
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.print_ascii(invert=True)


async def main() -> None:
    client = TelegramClient(SESSION, config.LEV_API_ID, config.LEV_API_HASH)
    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"[OK] Уже авторизован как {me.first_name} (@{me.username}). Готово.")
        await client.disconnect()
        return

    qr = await client.qr_login()
    print("Телефон -> Telegram -> Настройки -> Устройства -> Подключить устройство -> сканируй QR")
    show_qr(qr.url)

    while True:
        try:
            print("\n[i] Жду сканирование…")
            await qr.wait(timeout=60)
            break
        except asyncio.TimeoutError:
            await qr.recreate()
            print("[i] QR обновлён.")
            show_qr(qr.url)
        except SessionPasswordNeededError:
            import getpass
            pwd = getpass.getpass("\n[2FA] Облачный пароль Telegram: ")
            await client.sign_in(password=pwd)
            break

    me = await client.get_me()
    print(f"\n[OK] Вход выполнен: {me.first_name} (@{me.username})")
    print("Напиши ассистенту — переключу парсер на твою папку с каналами.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
