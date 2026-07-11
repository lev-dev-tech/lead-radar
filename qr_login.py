import asyncio
import os
import webbrowser

import qrcode
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

import config

SESSION = "vacancy_session"
QR_PNG = "qr_login.png"


def show_qr(url):
    qr_img = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=14,
        border=4,
    )
    qr_img.add_data(url)
    qr_img.make(fit=True)
    qr_img.make_image(fill_color="black", back_color="white").save(QR_PNG)

    path = os.path.abspath(QR_PNG)
    print(f"\n[QR] Картинка сохранена: {path}")
    try:
        webbrowser.open(path)
    except Exception:
        pass

    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.print_ascii(invert=True)


async def main():
    client = TelegramClient(SESSION, config.API_ID, config.API_HASH)
    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"[OK] Уже авторизован как {me.first_name} (@{me.username}). Запускай parser.py")
        await client.disconnect()
        return

    qr = await client.qr_login()
    print("Телефон -> Telegram -> Настройки -> Устройства -> Подключить устройство -> сканируй QR")
    show_qr(qr.url)

    while True:
        try:
            print("\n[i] Жду сканирование...")
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
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
