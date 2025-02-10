"""
Скрипт для мониторинга новых SEO вакансий из Telegram каналов
"""

import asyncio
from datetime import datetime, timezone, timedelta
from loguru import logger
import os
import pandas as pd
from telethon import TelegramClient, events
from dotenv import load_dotenv

# Импорт локальных модулей
from parse_channels import analyze_message as original_analyze_message
from parse_channels import is_seo_vacancy as original_is_seo_vacancy
from telegram_notifier import send_vacancy_notification
from seo_channels import SEO_CHANNELS

# Загрузка переменных окружения
load_dotenv()
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')
SEO_FILE = 'seo_vacancies.xlsx'

# Инициализация логгера
logger.add(
    "parser.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="1 week"
)

async def is_message_processed(channel_id: int, message_id: int) -> bool:
    """Проверка, было ли сообщение уже обработано"""
    try:
        if not os.path.exists(SEO_FILE):
            return False
            
        df = pd.read_excel(SEO_FILE)
        
        # Проверяем наличие нужных столбцов
        if 'channel_id' not in df.columns or 'message_id' not in df.columns:
            return False
            
        return any((df['channel_id'] == channel_id) & (df['message_id'] == message_id))
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке обработанных сообщений: {e}")
        return False

async def save_vacancy_to_excel(vacancy_data: dict):
    """Сохранение вакансии в Excel файл"""
    try:
        # Проверяем наличие обязательных полей
        if 'channel_id' not in vacancy_data or 'message_id' not in vacancy_data:
            logger.error("❌ Отсутствуют обязательные поля channel_id или message_id")
            return
            
        # Загружаем существующий Excel файл или создаем новый DataFrame
        if os.path.exists(SEO_FILE):
            df = pd.read_excel(SEO_FILE)
            # Проверяем наличие нужных столбцов
            if 'channel_id' not in df.columns:
                df['channel_id'] = None
            if 'message_id' not in df.columns:
                df['message_id'] = None
        else:
            df = pd.DataFrame()
        
        # Проверяем, нет ли уже такой вакансии
        if df.empty or not any((df['channel_id'] == vacancy_data['channel_id']) & 
                              (df['message_id'] == vacancy_data['message_id'])):
            
            # Добавляем новую вакансию
            vacancy_data['contains_seo_vacancy'] = True  # Добавляем флаг SEO вакансии
            new_df = pd.DataFrame([vacancy_data])
            df = pd.concat([df, new_df], ignore_index=True)
            
            # Сохраняем обновленный файл
            df.to_excel(SEO_FILE, index=False)
            logger.info("💾 Вакансия сохранена в Excel")
        else:
            logger.debug("ℹ️ Вакансия уже существует в Excel")
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении в Excel: {str(e)}")

async def check_recent_messages(client, channel_id: int):
    """Проверка сообщений за последние 24 часа"""
    try:
        # Получаем время 7 дней назад
        week_ago = datetime.now() - timedelta(days=7)
        logger.debug(f"🕒 Проверяем сообщения с {week_ago} для канала {channel_id}")
        
        message_count = 0
        seo_count = 0
        
        # Получаем сообщения из канала (увеличиваем лимит до 1000)
        channel_name = ""
        try:
            channel = await client.get_entity(channel_id)
            channel_name = getattr(channel, 'title', str(channel_id))
        except Exception as e:
            logger.error(f"❌ Ошибка при получении информации о канале: {str(e)}")
            channel_name = str(channel_id)
            
        logger.info(f"📺 Проверяем канал: {channel_name}")
        
        async for message in client.iter_messages(channel_id, offset_date=week_ago, reverse=True, limit=2000):
            message_count += 1
            
            # Проверяем, не обрабатывали ли мы уже это сообщение
            if not await is_message_processed(channel_id, message.id):
                # Получаем текст сообщения
                message_text = message.text or ''
                if not message_text.strip():
                    continue
                    
                # Проверяем наличие ключевых слов
                keywords = ['seo', 'сео', 'сэо']
                found_keywords = [kw for kw in keywords if kw in message_text.lower()]
                if found_keywords:
                    logger.info(f"🔍 Найдены ключевые слова {', '.join(found_keywords)} в сообщении {message.id} в канале {channel_name}")
                    
                logger.debug(f"📝 Проверяем сообщение {message.id} из канала {channel_id}")
                
                # Проверяем наличие слова SEO в разных вариантах написания
                if any(variant in message_text.lower() for variant in ['seo', 'сео', 'сэо']):
                    seo_count += 1
                    logger.info(f"🔍 Найдено сообщение с SEO за последние 7 дней в канале {channel_id}")
                    
                    # Проверка на SEO-релевантность
                    is_seo, reason = original_is_seo_vacancy(message_text)
                    if is_seo:
                        try:
                            # Анализ через GPT
                            analysis_result = original_analyze_message(message_text)
                            
                            if isinstance(analysis_result, dict) and analysis_result.get('is_seo', False):
                                # Подготовка данных
                                vacancy_data = {
                                    'text': message_text,
                                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'message_link': f"https://t.me/c/{channel_id}/{message.id}",
                                    'channel_name': message.chat.title if hasattr(message.chat, 'title') else str(channel_id),
                                    'views': getattr(message, 'views', 0) or 0,
                                    'forwards': getattr(message, 'forwards', 0) or 0,
                                    'contacts': analysis_result.get('contacts'),
                                    'salary': analysis_result.get('salary'),
                                    'channel_id': channel_id,
                                    'message_id': message.id
                                }
                                
                                # Отправка уведомления
                                await send_vacancy_notification(vacancy_data)
                                
                                # Сохранение в Excel
                                await save_vacancy_to_excel(vacancy_data)
                        except Exception as e:
                            logger.error(f"❌ Ошибка при анализе GPT: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке сообщений канала {channel_id}: {str(e)}")

async def monitor_new_vacancies():
    """Мониторинг новых вакансий в каналах"""
    logger.info("🔍 Запуск мониторинга вакансий...")
    
    # Инициализация клиента
    logger.info(f"🔑 Инициализация Telegram клиента (API ID: {API_ID})")
    client = TelegramClient('seo_parser_session', API_ID, API_HASH)
    
    # Подготовка списка каналов
    channels_to_monitor = []
    
    try:
        # Подключение к Telegram
        logger.info("🔄 Подключение к Telegram...")
        await client.connect()
        
        if not await client.is_user_authorized():
            logger.info("🔒 Необходима авторизация...")
            await client.start(phone=PHONE)
        
        logger.info("✅ Успешно подключились к Telegram")
        
        # Получаем ID всех каналов из SEO_CHANNELS
        for channel in SEO_CHANNELS:
            try:
                entity = await client.get_entity(channel['username'])
                channels_to_monitor.append(entity.id)
                logger.info(f"✅ Добавлен канал {channel['name']} (ID: {entity.id})")
            except Exception as e:
                logger.error(f"❌ Не удалось получить ID канала {channel['name']}: {e}")
        
        logger.info(f"📱 Мониторинг каналов: {channels_to_monitor}")
        
        # Проверяем сообщения за последние 24 часа
        logger.info("🕐 Проверка сообщений за последние 24 часа...")
        for channel_id in channels_to_monitor:
            await check_recent_messages(client, channel_id)
        logger.info("✅ Проверка завершена")
        
        # Обработчик новых сообщений
        @client.on(events.NewMessage(chats=channels_to_monitor))
        async def handle_new_message(event):
            try:
                # Проверка на дубликат
                if await is_message_processed(event.chat_id, event.message.id):
                    logger.debug(f"🔄 Сообщение {event.message.id} уже обработано")
                    return
                
                # Получаем текст сообщения
                message_text = event.message.text or ''
                if not message_text.strip():
                    logger.debug("❌ Пустое сообщение")
                    return
                
                logger.info(f"💬 Новое сообщение из канала {event.chat_id}")
                
                # Проверяем наличие слова SEO в тексте
                if any(variant in message_text.lower() for variant in ['seo', 'сео', 'сэо']):
                    # Проверка на SEO-релевантность
                    is_seo, reason = original_is_seo_vacancy(message_text)
                    if is_seo:
                        logger.info(f"🔍 Найдена потенциальная SEO вакансия: {reason}")
                    
                        try:
                            # Анализ сообщения через GPT
                            logger.debug("🔍 Запуск анализа через GPT...")
                            analysis_result = original_analyze_message(message_text)
                            
                            # Проверяем результат анализа
                            logger.debug(f"🔍 Результат анализа: {analysis_result}")
                            
                            if isinstance(analysis_result, dict) and analysis_result.get('is_seo', False):
                                logger.info(f"✅ Вакансия подтверждена GPT: {analysis_result.get('reason', 'No reason provided')}")
                                
                                # Подготовка данных
                                vacancy_data = {
                                    'text': message_text,
                                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Используем локальное время
                                    'message_link': f"https://t.me/c/{event.chat_id}/{event.message.id}",
                                    'channel_name': event.chat.title if hasattr(event.chat, 'title') else str(event.chat_id),
                                    'views': getattr(event.message, 'views', 0) or 0,
                                    'forwards': getattr(event.message, 'forwards', 0) or 0,
                                    'contacts': analysis_result.get('contacts'),
                                    'salary': analysis_result.get('salary'),
                                    'channel_id': event.chat_id,
                                    'message_id': event.message.id
                                }
                                
                                # Отправка уведомления
                                await send_vacancy_notification(vacancy_data)
                                logger.info("📢 Уведомление отправлено")
                                
                                # Сохранение в Excel
                                await save_vacancy_to_excel(vacancy_data)
                                
                        except Exception as e:
                            logger.error(f"❌ Ошибка при анализе GPT: {str(e)}")
                    else:
                        logger.debug(f"❌ Сообщение не прошло проверку SEO: {reason}")
                else:
                    logger.debug("❌ Сообщение не содержит SEO")
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке сообщения: {str(e)}")
        
        # Запускаем прослушивание событий
        logger.info("📡 Начинаем мониторинг...")
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске клиента: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(monitor_new_vacancies())
