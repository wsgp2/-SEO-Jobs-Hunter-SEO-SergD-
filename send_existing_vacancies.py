import asyncio
import pandas as pd
from telegram_notifier import send_vacancy_notification
from loguru import logger
import time

async def send_all_vacancies():
    """Отправка всех существующих вакансий в канал"""
    try:
        # Загружаем данные из Excel
        df = pd.read_excel('seo_vacancies.xlsx')
        
        # Преобразуем столбец даты в datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Получаем время 24 часа назад
        last_24h = pd.Timestamp.now() - pd.Timedelta(days=1)
        
        # Фильтруем SEO вакансии за последние 24 часа
        recent_vacancies = df[
            (df['date'] >= last_24h) & 
            (df['contains_seo_vacancy'] == True)
        ]
        
        # Сортируем по дате (сначала старые)
        recent_vacancies = recent_vacancies.sort_values('date', ascending=True)
        
        logger.info(f"📊 Найдено {len(recent_vacancies)} SEO вакансий за последние 24 часа")
        
        # Отправляем каждую вакансию
        for index, row in recent_vacancies.iterrows():
            try:
                # Конвертируем строку в словарь и обрабатываем дату
                vacancy_dict = row.to_dict()
                vacancy_dict['date'] = row['date'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Отправляем уведомление
                await send_vacancy_notification(vacancy_dict)
                
                # Делаем паузу между отправками (чтобы не превысить лимиты Telegram)
                await asyncio.sleep(3)
                
                logger.info(f"✅ Отправлена вакансия {index + 1}/{len(recent_vacancies)}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке вакансии {index}: {str(e)}")
                continue
        
        logger.info("🎉 Все вакансии успешно отправлены!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке файла: {str(e)}")

if __name__ == '__main__':
    # Запускаем отправку
    asyncio.run(send_all_vacancies())
