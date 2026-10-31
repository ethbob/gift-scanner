import os
from telethon import TelegramClient, events
import asyncio
import re

# --------- НАСТРОЙКИ ----------
api_id = int(os.environ["TG_API_ID"])
api_hash = os.environ["TG_API_HASH"]
session_name = 'test_session'

target_group = 'testgiftscanner'
price_bot = 'PriceNFTbot'
delay = 4
timeout = 20
output_file = 'found_users.txt'
# ------------------------------

found_users = []

import re

def extract_info(text: str) -> str:
    # Удалим все невидимые юникод-символы типа \u2066-\u2069, которые встречаются вокруг цифр
    clean_text = re.sub(r'[\u2060-\u206F\u200B-\u200D]', '', text)

    # Поиск количества NFT (рус и англ)
    nft_match = re.search(
        r"(?:has|имеет)\D*(\d+)\D*(?:visible NFTs|публичных NFT)",
        clean_text,
        re.IGNORECASE
    )
    nft_count = nft_match.group(1) if nft_match else "?"

    # Поиск Floor price
    floor_match = re.search(r"Floor price:\s*(.+)", clean_text, re.IGNORECASE)
    floor = floor_match.group(1).strip() if floor_match else "нет данных"

    # Поиск AVG price
    avg_match = re.search(r"AVG price:\s*(.+)", clean_text, re.IGNORECASE)
    avg = avg_match.group(1).strip() if avg_match else "нет данных"

    return f"NFT: {nft_count} | Floor: {floor} | AVG: {avg}"

async def check_user(client: TelegramClient, username: str):
    event = asyncio.Event()
    response_text = None

    @client.on(events.NewMessage(from_users=price_bot))
    async def handler(event_message):
        nonlocal response_text
        response_text = event_message.raw_text
        event.set()

    try:
        await client.send_message(price_bot, f"@{username}")
        print(f"🔁 Отправил @{username} в бота")

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"⏱ @{username} — таймаут ответа от бота")
            client.remove_event_handler(handler)
            return False

        client.remove_event_handler(handler)

        lowered = response_text.lower()
        if "юзернеймом" in lowered or "not found" in lowered:
            print(f"❌ @{username} — нет подарков")
            return False
        elif "имеет" in lowered or "has" in lowered:
            info = extract_info(response_text)
            print(f"✅ @{username} — есть подарки! ({info})")
            found_users.append(username)
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"@{username} — {info}\n")
            return True
        else:
            print(f"❔ @{username} — неизвестный ответ: {response_text[:60]}...")
            return False

    except Exception as e:
        print(f"⚠️ @{username} — ошибка: {e}")
        return False

async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()
    me = await client.get_me()
    print(f'✅ Авторизация прошла: {me.username or me.first_name}')

    try:
        chat = await client.get_entity(target_group)
    except Exception as e:
        print(f"❌ Ошибка при получении чата {target_group}: {e}")
        return

    print("📥 Получаю участников чата...")
    participants = await client.get_participants(chat, aggressive=True)
    print(f"👥 Найдено участников: {len(participants)}")

    for user in participants:
        if not user.username:
            continue

        username = user.username

        if username in found_users:
            print(f"⏩ @{username} уже проверен")
            continue

        await check_user(client, username)
        await asyncio.sleep(delay)

    print("\n🎉 Готово!")
    print(f"🎁 С подарками: {len(found_users)}")
    print(f"💾 Сохранено в файл: {output_file}")

# Запуск
asyncio.run(main())
