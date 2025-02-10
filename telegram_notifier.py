import os
import asyncio
from datetime import datetime
from loguru import logger
import telebot
from telebot.async_telebot import AsyncTeleBot
import emoji
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация бота
BOT_TOKEN = "7670172403:AAFtYayGm9ocfG6wyNoXox0SPKXfSvcXj9M"
CHANNEL_ID = "-1002422777931"

# Инициализация бота
bot = AsyncTeleBot(BOT_TOKEN)

async def send_vacancy_notification(vacancy_data: dict):
    """Отправка уведомления о новой вакансии в канал"""
    try:
        # Форматируем дату
        date = datetime.strptime(vacancy_data['date'], '%Y-%m-%d %H:%M:%S')
        date_str = date.strftime('%d.%m.%Y %H:%M')
        
        # Форматируем текст вакансии (обрезаем если слишком длинный)
        vacancy_text = vacancy_data['text'][:1000]
        if len(vacancy_data['text']) > 1000:
            vacancy_text += "..."
        
        # Формируем текст сообщения в HTML
        message = (
            f'<b>🔍 Новая SEO вакансия!</b>\n\n'
            f'📌 <i>Pin: @vikapaleshko</i>\n\n'
            f'<b>📝 Описание:</b>\n'
            f'<pre>{vacancy_text}</pre>\n\n'
            f'<b>💼 Канал:</b> <code>{vacancy_data["channel_name"]}</code>\n'
            f'<b>📅 Дата публикации:</b> <code>{date_str}</code>\n'
        )
        
        # Добавляем контакты, если есть
        if vacancy_data.get('contacts'):
            message += f'<b>📞 Контакты:</b> <code>{vacancy_data["contacts"]}</code>\n'
            
        # Добавляем зарплату, если есть
        if vacancy_data.get('salary'):
            message += f'<b>💰 Зарплата:</b> <code>{vacancy_data["salary"]}</code>\n'
            
        # Добавляем статистику
        message += f'\n<b>📊 Статистика:</b>\n'
        message += f'👁 Просмотры: <code>{vacancy_data["views"]}</code>\n'
        message += f'🔄 Репосты: <code>{vacancy_data["forwards"]}</code>\n'
        
        # Добавляем разделитель
        message += '\n' + '─' * 30 + '\n'
        
        # Добавляем ссылку на оригинал
        message += f'🔗 <a href="{vacancy_data["message_link"]}">Ссылка на оригинал</a>'
        
        # Отправляем сообщение
        await bot.send_message(
            CHANNEL_ID,
            message,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        logger.info(f"✅ Уведомление о вакансии отправлено в канал")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке уведомления: {e}")

async def test_notification():
    """Тестовая отправка уведомления"""
    test_data = {
        'text': 'Ищем опытного SEO-специалиста в нашу команду! 🚀\n\nТребования:\n- Опыт работы от 2 лет\n- Знание основных инструментов SEO\n- Умение работать с аналитикой\n\nУсловия:\n- Удаленная работа\n- Гибкий график\n- Дружная команда',
        'channel_name': '🔍 SEO Вакансии',
        'date': '2025-02-07 21:55:00',
        'contacts': 'HR менеджер: @test_contact\nТелефон: +7 (999) 999-99-99',
        'salary': '150 000 - 200 000 ₽',
        'views': 1250,
        'forwards': 15,
        'message_link': 'https://t.me/test_channel/123'
    }
    try:
        await send_vacancy_notification(test_data)
    finally:
        # Закрываем сессию бота
        await bot.close_session()
        await asyncio.sleep(0.250)  # Даем время на закрытие соединений

if __name__ == '__main__':
    # Тестируем отправку уведомления
    asyncio.run(test_notification())
