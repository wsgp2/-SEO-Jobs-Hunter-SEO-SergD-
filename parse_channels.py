"""
Скрипт для парсинга SEO вакансий из Telegram каналов с учетом ограничений API
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
from loguru import logger
import os
from seo_channels import SEO_CHANNELS
from telethon import TelegramClient, sync
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import FloodWaitError, SlowModeWaitError, ServerError
from dotenv import load_dotenv
import asyncio
import time
from tqdm import tqdm
import random
from openai import OpenAI
import json
import glob
from stop_words import contains_stop_words
from telegram_notifier import send_vacancy_notification

# Настройки Telegram клиента
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE = "+79222474175"

# Инициализация OpenAI клиента
openai_client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# Настройки файлов
DATA_FILE = "data_seohr.xlsx"
SEO_FILE = "seo_vacancies.xlsx"
PROGRESS_FILE = "parsing_progress.json"

# Настраиваем логирование
logger.add("parser_log.txt", rotation="1 day")

# Получаем дату год назад с учетом временной зоны
ONE_YEAR_AGO = datetime.now(timezone.utc) - timedelta(days=365)

# Константы для ограничений API
MAX_REQUESTS_PER_HOUR = 3000
REQUESTS_INTERVAL = 2  # минимальный интервал между запросами в секундах
MAX_BATCH_SIZE = 100   # максимальное количество сообщений за один запрос
HOURLY_REQUESTS = {}   # словарь для отслеживания количества запросов по каналам

class RateLimiter:
    """Класс для управления ограничениями API"""
    def __init__(self):
        self.last_request_time = 0
        self.hourly_requests = {}
    
    async def wait_if_needed(self, channel_username):
        """Проверка и ожидание перед следующим запросом"""
        current_time = time.time()
        
        # Проверяем ограничение запросов в час
        hour_key = f"{channel_username}_{int(current_time / 3600)}"
        self.hourly_requests[hour_key] = self.hourly_requests.get(hour_key, 0) + 1
        
        if self.hourly_requests[hour_key] > MAX_REQUESTS_PER_HOUR:
            wait_time = 3600 - (current_time % 3600)
            logger.warning(f"⚠️ Достигнут часовой лимит для {channel_username}, ждем {wait_time:.0f} секунд")
            await asyncio.sleep(wait_time)
            self.hourly_requests[hour_key] = 0
        
        # Проверяем минимальный интервал между запросами
        time_since_last = current_time - self.last_request_time
        if time_since_last < REQUESTS_INTERVAL:
            # Добавляем случайную задержку для естественности
            wait_time = REQUESTS_INTERVAL - time_since_last + random.uniform(0.1, 0.5)
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()

async def get_all_messages(client, channel_username, rate_limiter):
    """Получение всех сообщений из канала за последний год"""
    messages = []
    
    try:
        # Подключаемся к каналу
        channel = await client.get_entity(channel_username)
        
        # Создаем прогресс-бар
        with tqdm(desc=f"Загрузка сообщений из {channel_username}", unit=" сообщений") as pbar:
            offset_id = 0
            total_messages = 0
            retry_count = 0
            
            while True:
                try:
                    # Проверяем ограничения API
                    await rate_limiter.wait_if_needed(channel_username)
                    
                    history = await client(GetHistoryRequest(
                        peer=channel,
                        limit=MAX_BATCH_SIZE,
                        offset_date=None,
                        offset_id=offset_id,
                        max_id=0,
                        min_id=0,
                        add_offset=0,
                        hash=0
                    ))
                    
                    if not history.messages:
                        break
                        
                    # Проверяем дату последнего сообщения
                    last_message = history.messages[-1]
                    message_date = last_message.date.replace(tzinfo=timezone.utc)
                    if message_date < ONE_YEAR_AGO:
                        # Добавляем только сообщения за последний год
                        for message in history.messages:
                            message_date = message.date.replace(tzinfo=timezone.utc)
                            if message_date >= ONE_YEAR_AGO:
                                messages.append(message)
                        break
                    
                    messages.extend(history.messages)
                    offset_id = history.messages[-1].id
                    total_messages += len(history.messages)
                    pbar.update(len(history.messages))
                    
                    # Сбрасываем счетчик попыток после успешного запроса
                    retry_count = 0
                    
                except FloodWaitError as e:
                    retry_count += 1
                    wait_time = e.seconds * (2 ** retry_count)  # Экспоненциальная задержка
                    logger.warning(f"⚠️ Достигнут лимит запросов, ждем {wait_time} секунд (попытка {retry_count})")
                    await asyncio.sleep(wait_time)
                    continue
                    
                except SlowModeWaitError as e:
                    logger.warning(f"⚠️ Включен медленный режим, ждем {e.seconds} секунд")
                    await asyncio.sleep(e.seconds)
                    continue
                    
                except ServerError as e:
                    retry_count += 1
                    wait_time = 5 * (2 ** retry_count)  # Экспоненциальная задержка
                    logger.warning(f"⚠️ Ошибка сервера: {str(e)}, ждем {wait_time} секунд (попытка {retry_count})")
                    if retry_count > 5:  # Максимум 5 попыток для одного запроса
                        logger.error(f"❌ Превышено количество попыток для запроса")
                        break
                    await asyncio.sleep(wait_time)
                    continue
                    
    except Exception as e:
        logger.error(f"❌ Ошибка при получении сообщений из канала {channel_username}: {str(e)}")
    
    return messages

SYSTEM_PROMPT = """Ты HR ассистент, который анализирует вакансии SEO специалистов.
Твоя задача - определить, является ли текст релевантной вакансией SEO специалиста.

Правила отбора вакансий:

1. ОБЯЗАТЕЛЬНЫЕ КРИТЕРИИ (все должны выполняться):
   - Это должна быть вакансия для работы в штат компании, удаленная работа подходит (не агентство, не фриланс)
   - Вакансия должна быть для SEO-специалиста или специалиста, где SEO - основная часть работы
   - Работа должна быть на русском языке и для русскоязычных проектов
   - Должна быть указана конкретная компания или продукт

2. СТОП-ФАКТОРЫ (если есть хоть один - отклоняем):
   - Вакансия для работы с adult, gambling, казино, беттинг
   - Работа с PBN сетками или дроп доменами
   - Линкбилдинг как основная задача
   - Работа с буржунетом или англоязычными проектами
   - Криптовалюты, трейдинг, web3
   - Временная работа или проектная занятость
   - Вакансия из агентства или для агентства
   - Требуется английский язык выше базового уровня

3. ДОПОЛНИТЕЛЬНЫЕ ПРАВИЛА:
   - Если не указана зарплата - это нормально, не отклоняем
   - Если не указан полный список требований - это нормально
   - Если есть сомнения - отклоняем вакансию

Проанализируй текст и верни JSON:
{
    "is_seo": true/false,  # Подходит ли вакансия под наши критерии
    "reason": "string",    # Причина решения, особенно важно если отклоняем
    "contacts": "string",  # Найденные контакты (опционально)
    "salary": "string"     # Найденная зарплата (опционально)
}"""

def analyze_message(text):
    """Анализ сообщения на наличие упоминания SEO и контактов"""
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
        
        # Используем синхронный вызов, так как OpenAI Python SDK не поддерживает асинхронные вызовы
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.debug(f"✨ Результат анализа: {result}")
        
        # Добавляем небольшую задержку между запросами
        time.sleep(0.5)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при анализе сообщения: {e}")
        # В случае ошибки делаем более длительную паузу
        time.sleep(2)
        return {
            "is_seo": False,
            "reason": f"Ошибка анализа: {str(e)}",
            "contacts": None,
            "salary": None
        }

def is_seo_vacancy(text: str) -> tuple[bool, str]:
    """
    Предварительная проверка текста на SEO вакансию
    
    Returns:
        tuple: (прошел проверку, причина отказа если не прошел)
    """
    # Проверяем на None и пустой текст
    if text is None or not str(text).strip():
        return False, "Пустой текст"
    
    # Приводим к строке и нижнему регистру
    text = str(text).lower()
    
    # Проверяем наличие SEO в тексте
    if not any(keyword in text for keyword in ['seo', 'сео']):
        return False, "Нет упоминания SEO"
        
    # Проверяем на стоп-слова
    if contains_stop_words(text):
        return False, "Содержит стоп-слова"
        
    return True, ""

async def process_messages(messages):
    """Обработка списка сообщений"""
    all_messages = []
    seo_messages = []
    
    for message in messages:
        try:
            channel = message['channel']
            text = message['text']
            date = message['date']
            views = message.get('views', 0)
            forwards = message.get('forwards', 0)
            message_link = message.get('message_link', '')
            
            message_data = {
                'channel': channel,
                'text': text,
                'date': date,
                'views': views,
                'forwards': forwards,
                'message_link': message_link,
                'contains_seo_vacancy': False,
                'reason': "",
                'contacts': None,
                'salary': None
            }
            
            # Предварительная проверка
            passed_initial_check, reject_reason = is_seo_vacancy(text)
            
            if not passed_initial_check:
                message_data['reason'] = reject_reason
                all_messages.append(message_data)
                continue
            
            # Если прошли предварительную проверку, отправляем на анализ в ChatGPT
            analysis = await analyze_message(text)
            message_data.update({
                'contains_seo_vacancy': analysis['is_seo'],
                'reason': analysis['reason'],
                'contacts': analysis['contacts'],
                'salary': analysis['salary']
            })
            
            if analysis['is_seo']:
                seo_messages.append(message_data)
                
                # Сохраняем SEO вакансии сразу в основной файл
                df_seo = pd.DataFrame(seo_messages)
                df_seo.to_excel(SEO_FILE, index=False)
                logger.info(f"💾 Сохранено {len(seo_messages)} SEO вакансий")
            
            all_messages.append(message_data)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке сообщения: {e}")
            continue
    
    return all_messages, seo_messages

async def save_to_excel(messages):
    """Сохранение сообщений в Excel"""
    try:
        # Создаем DataFrame
        df = pd.DataFrame(messages)
        
        # Сортируем по дате
        df = df.sort_values('date', ascending=False)
        
        # Сохраняем текущую версию
        df.to_excel('seo_vacancies.xlsx', index=False)
        
        # Создаем бэкап с временной меткой
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        df.to_excel(f'seo_vacancies_{timestamp}.xlsx', index=False)
        
        logger.info(f"✅ Данные сохранены в Excel")
        
        # Отправляем уведомления о новых вакансиях
        for _, row in df.iterrows():
            if row['contains_seo_vacancy']:
                await send_vacancy_notification(row.to_dict())
        
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении в Excel: {e}")
        raise

def load_progress():
    """Загрузка прогресса парсинга"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"processed_channels": [], "last_message_ids": {}}

def save_progress(progress):
    """Сохранение прогресса парсинга"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def load_existing_data():
    """Загрузка существующих данных"""
    all_messages = []
    seo_messages = []
    
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_excel(DATA_FILE)
            all_messages = df.to_dict('records')
        except Exception as e:
            logger.error(f"⚠️ Ошибка при загрузке {DATA_FILE}: {e}")
    
    if os.path.exists(SEO_FILE):
        try:
            df = pd.read_excel(SEO_FILE)
            seo_messages = df.to_dict('records')
        except Exception as e:
            logger.error(f"⚠️ Ошибка при загрузке {SEO_FILE}: {e}")
    
    return all_messages, seo_messages

def clean_temp_files():
    """Удаление временных файлов"""
    for pattern in ["data_seohr_*_temp.xlsx", "seo_vacancies_*_temp.xlsx"]:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                logger.debug(f"🗑️ Удален временный файл: {file}")
            except Exception as e:
                logger.error(f"⚠️ Ошибка при удалении {file}: {e}")

async def parse_all_channels(client):
    """Парсинг всех каналов из списка"""
    # Загружаем прогресс и существующие данные
    progress = load_progress()
    all_messages, seo_messages = load_existing_data()
    rate_limiter = RateLimiter()
    
    for channel in SEO_CHANNELS:
        # Пропускаем уже обработанные каналы
        if channel['username'] in progress['processed_channels']:
            logger.info(f"⏩ Пропускаем обработанный канал: {channel['name']}")
            continue
            
        logger.info(f"🔄 Парсим канал: {channel['name']}")
        
        try:
            messages = await get_all_messages(client, channel['username'], rate_limiter)
            
            for msg in messages:
                # Проверяем, не обрабатывали ли мы уже это сообщение
                if str(msg.id) in progress.get('last_message_ids', {}).get(channel['username'], []):
                    continue
                    
                text = msg.message
                message_link = f"https://t.me/{channel['username']}/{msg.id}"
                message_date = msg.date.replace(tzinfo=None)
                
                message_data = {
                    'channel_name': channel['name'],
                    'channel_username': channel['username'],
                    'message_id': msg.id,
                    'date': message_date,
                    'text': text,
                    'views': getattr(msg, 'views', 0),
                    'forwards': getattr(msg, 'forwards', 0),
                    'message_link': message_link
                }
                
                # Предварительная проверка
                passed_initial_check, reject_reason = is_seo_vacancy(text)
                
                if not passed_initial_check:
                    message_data['contains_seo_vacancy'] = False
                    message_data['reason'] = reject_reason
                    all_messages.append(message_data)
                    continue
                
                # Если прошли предварительную проверку, отправляем на анализ в ChatGPT
                analysis = await analyze_message(text)
                message_data.update({
                    'contains_seo_vacancy': analysis['is_seo'],
                    'reason': analysis['reason'],
                    'contacts': analysis['contacts'],
                    'salary': analysis['salary']
                })
                
                if analysis['is_seo']:
                    seo_messages.append(message_data)
                    
                    # Сохраняем SEO вакансии сразу в основной файл
                    df_seo = pd.DataFrame(seo_messages)
                    df_seo.to_excel(SEO_FILE, index=False)
                    logger.info(f"💾 Сохранено {len(seo_messages)} SEO вакансий")
                
                all_messages.append(message_data)
                
                # Сохраняем все сообщения в основной файл
                if len(all_messages) % 10 == 0:
                    df = pd.DataFrame(all_messages)
                    df.to_excel(DATA_FILE, index=False)
                    logger.info(f"💾 Сохранено {len(all_messages)} сообщений")
                
                # Обновляем прогресс
                if channel['username'] not in progress['last_message_ids']:
                    progress['last_message_ids'][channel['username']] = []
                progress['last_message_ids'][channel['username']].append(str(msg.id))
                save_progress(progress)
            
            # Помечаем канал как обработанный
            progress['processed_channels'].append(channel['username'])
            save_progress(progress)
            
            logger.info(f"✅ Получено {len(messages)} сообщений из канала {channel['name']}")
            
        except Exception as e:
            logger.error(f"⚠️ Ошибка при парсинге канала {channel['name']}: {e}")
            # При ошибке сохраняем прогресс и продолжаем со следующего канала
            save_progress(progress)
            continue
    
    # Финальное сохранение
    df = pd.DataFrame(all_messages)
    df.to_excel(DATA_FILE, index=False)
    logger.info(f"💾 Все сообщения сохранены в {DATA_FILE}")
    
    df_seo = pd.DataFrame(seo_messages)
    df_seo.to_excel(SEO_FILE, index=False)
    logger.info(f"💾 SEO вакансии сохранены в {SEO_FILE}")
    
    # Очищаем временные файлы
    clean_temp_files()

async def main():
    """Основная функция"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            client = TelegramClient('seo_parser_session', API_ID, API_HASH)
            await client.start(PHONE)
            
            await parse_all_channels(client)
            break
            
        except Exception as e:
            retry_count += 1
            wait_time = 5 * (2 ** retry_count)
            logger.error(f"❌ Ошибка при выполнении парсинга: {e}")
            logger.info(f"🔄 Попытка {retry_count} из {max_retries}, ожидание {wait_time} секунд")
            await asyncio.sleep(wait_time)
            
        finally:
            try:
                await client.disconnect()
            except:
                pass
    
    if retry_count >= max_retries:
        logger.error("❌ Превышено максимальное количество попыток")

if __name__ == '__main__':
    asyncio.run(main())
