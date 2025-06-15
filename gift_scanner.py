from telethon import TelegramClient, events
import asyncio

# --------- НАСТРОЙКИ ----------
api_id = 15351605  # ← Замени на свой
api_hash = 'REMOVED'  # ← Замени на свой
session_name = 'test_session'

target_group = 'annahabell_chat'  # ← username чата
price_bot = 'PriceNFTbot'
delay = 4  # задержка между запросами
timeout = 20  # максимум ожидания ответа
output_file = 'found_users.txt'
# ------------------------------

found_users = []

async def check_user(client: TelegramClient, username: str):
    event = asyncio.Event()
    response_text = None

    @client.on(events.NewMessage(from_users=price_bot))
    async def handler(event_message):
        nonlocal response_text
        response_text = event_message.raw_text.lower()
        event.set()  # сигнализируем, что ответ получен

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

        if "юзернеймом" in response_text or "not found" in response_text:
            print(f"❌ @{username} — нет подарков")
            return False
        elif "имеет" in response_text or 'has' in response_text:
            print(f"✅ @{username} — есть подарки!")
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

        has_gift = await check_user(client, username)
        if has_gift:
            found_users.append(username)
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f"{username}\n")

        await asyncio.sleep(delay)

    print("\n🎉 Готово!")
    print(f"🎁 С подарками: {len(found_users)}")
    print(f"💾 Сохранено в файл: {output_file}")

# Запуск
asyncio.run(main())
