import asyncio

from telethon import TelegramClient
from telethon.errors import FloodWaitError, PhoneNumberInvalidError

import config

SESSION = "vacancy_session"


async def main():
    client = TelegramClient(SESSION, config.API_ID, config.API_HASH)
    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"[OK] Уже авторизован как {me.first_name} (@{me.username}), id={me.id}")
        await client.disconnect()
        return

    print(f"[i] Запрашиваю код для номера: {config.PHONE}")
    try:
        sent = await client.send_code_request(config.PHONE)
    except FloodWaitError as e:
        print(f"[БЛОКИРОВКА] Подождать {e.seconds} сек (~{e.seconds // 60} мин).")
        await client.disconnect()
        return
    except PhoneNumberInvalidError:
        print("[ОШИБКА] Неверный номер. Проверь PHONE в config.py.")
        await client.disconnect()
        return
    except Exception as e:
        print(f"[ОШИБКА] {type(e).__name__}: {e}")
        await client.disconnect()
        return

    t = type(sent.type).__name__
    print(f"[i] Код отправлен. Способ доставки: {t}")
    print(f"    next_type: {sent.next_type}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
