import asyncio
import aiohttp
import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN, ADMIN_ID, POLL_INTERVAL, API_URL, STATE_FILE

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

sent_ids = set()


def load_state():
    """Загрузка ID отправленных тикетов из файла"""
    global sent_ids
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                sent_ids = set(data)
                print(f"✅ Загружено {len(sent_ids)} ID отправленных тикетов")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки состояния: {e}")
            sent_ids = set()
    else:
        print("📂 Файл состояния не найден, создаём новый")
        sent_ids = set()
    save_state()


def save_state():
    """Сохранение ID отправленных тикетов в файл"""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(sent_ids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка сохранения состояния: {e}")


def format_ticket(ticket: dict) -> str:
    """Форматирование тикета для отправки в Telegram"""
    if ticket is None:
        return "⚠️ Ошибка: тикет не найден"
    
    emoji_sentiment = {
        'negative': '🔴',
        'neutral': '🟡',
        'positive': '🟢'
    }
    
    sentiment = ticket.get('sentiment', 'unknown')
    emoji = emoji_sentiment.get(sentiment, '⚪')
    
    text = f"""
{emoji} <b>Новое обращение #{ticket.get('email_id', 'N/A')}</b>

👤 <b>ФИО:</b> {ticket.get('fio', 'Не указано')}
🏢 <b>Объект:</b> {ticket.get('object_name', 'Не указано')}
📞 <b>Телефон:</b> {ticket.get('phone', 'Не указано')}
📧 <b>Email:</b> {ticket.get('email', 'Не указано')}

📋 <b>Категория:</b> {ticket.get('category', 'Не указано')}
😊 <b>Тональность:</b> {sentiment} ({ticket.get('sentiment_confidence', 0):.0%})

📝 <b>Суть вопроса:</b> {ticket.get('description', 'Не указано')[:500]}

⏰ <b>Дата получения:</b> {ticket.get('date', 'Не указано')}
"""
    return text


async def fetch_tickets(session: aiohttp.ClientSession) -> list:
    """Получение тикетов из API"""
    try:
        async with session.get(API_URL, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                # API возвращает список напрямую, а не {'tickets': [...]}
                return data if isinstance(data, list) else []
            else:
                print(f"⚠️ Ошибка API: {response.status}")
                return []
    except Exception as e:
        print(f"❌ Ошибка получения тикетов: {e}")
        return []


async def send_ticket(ticket: dict):
    """Отправка тикета в Telegram"""
    try:
        if ticket is None:
            print("⚠️ Тикет равен None, пропускаем")
            return False
        
        # Проверяем, что ticket - это словарь
        if not isinstance(ticket, dict):
            print(f"⚠️ Тикет не является словарём: {type(ticket)}")
            return False
        
        ticket_id = ticket.get('email_id')
        if not ticket_id:
            print("⚠️ У тикета нет email_id")
            return False
        
        message = format_ticket(ticket)
        await bot.send_message(ADMIN_ID, message, parse_mode='HTML')
        print(f"✅ Отправлен тикет #{ticket_id}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки тикета: {e}")
        return False


async def check_new_tickets():
    """Проверка новых тикетов"""
    async with aiohttp.ClientSession() as session:
        tickets = await fetch_tickets(session)
        
        if not tickets:
            print("💤 Нет тикетов в API")
            return 0
        
        new_count = 0
        for ticket in tickets:
            # Проверяем, что ticket не None
            if ticket is None:
                continue
            
            ticket_id = ticket.get('email_id')
            if ticket_id and ticket_id not in sent_ids:
                if await send_ticket(ticket):
                    sent_ids.add(ticket_id)
                    new_count += 1
        
        if new_count > 0:
            save_state()
        
        return new_count


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start"""
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            f"🤖 <b>Бот мониторинга обращений ЭРИС запущен</b>\n\n"
            f"📊 Отправлено тикетов: {len(sent_ids)}\n"
            f"⏱ Интервал опроса: {POLL_INTERVAL} сек\n"
            f"🔗 API: {API_URL}",
            parse_mode='HTML'
        )
    else:
        await message.answer("❌ Доступ запрещён")


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """Команда /status"""
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            f"📊 <b>Статус бота</b>\n\n"
            f"✅ Отправлено тикетов: {len(sent_ids)}\n"
            f"⏱ Интервал опроса: {POLL_INTERVAL} сек\n"
            f"🔗 API: {API_URL}\n"
            f"👤 Admin ID: {ADMIN_ID}",
            parse_mode='HTML'
        )
    else:
        await message.answer("❌ Доступ запрещён")


@dp.message(Command("check"))
async def cmd_check(message: types.Message):
    """Команда /check - ручная проверка"""
    if message.from_user.id == ADMIN_ID:
        msg = await message.answer("🔍 Проверяю новые тикеты...")
        count = await check_new_tickets()
        await msg.edit_text(f"✅ Проверка завершена. Найдено новых тикетов: {count}")
    else:
        await message.answer("❌ Доступ запрещён")


async def background_polling():
    """Периодическая проверка новых тикетов"""
    while True:
        try:
            now = datetime.now().strftime('%H:%M:%S')
            print(f"\n🔍 Опрос API... ({now})")
            
            count = await check_new_tickets()
            
            if count > 0:
                print(f"🆕 Найдено {count} новых тикетов")
            else:
                print("✅ Нет новых тикетов")
            
        except Exception as e:
            print(f"❌ Ошибка в фоне: {e}")
        
        await asyncio.sleep(POLL_INTERVAL)


async def on_startup():
    """Инициализация при старте бота"""
    print("="*60)
    print("🚀 ЗАПУСК TELEGRAM БОТА")
    print("="*60)
    print(f"👤 Admin ID: {ADMIN_ID}")
    print(f"⏱ Poll Interval: {POLL_INTERVAL} сек")
    print(f"🔗 API URL: {API_URL}")
    print(f"📂 State File: {STATE_FILE}")
    print("="*60)
    
    load_state()
    
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🤖 <b>Бот запущен!</b>\n\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"📊 Загружено {len(sent_ids)} ID отправленных тикетов",
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"⚠️ Не удалось отправить сообщение о запуске: {e}")


async def main():
    """Основная функция"""
    await on_startup()
    
    # Запуск поллинга и бота параллельно
    await asyncio.gather(
        dp.start_polling(bot),
        background_polling()
    )


if __name__ == "__main__":
    asyncio.run(main())
