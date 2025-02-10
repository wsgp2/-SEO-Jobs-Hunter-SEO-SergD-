<div align="center">

# 🔍 SEO Jobs Hunter

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT-green.svg)](https://platform.openai.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

### Умный парсер SEO вакансий из Telegram с GPT анализом

[English](README_EN.md) | Русский

</div>

## 👨‍💻 Автор

**SergD (Sergei Dyshkant)**
- Telegram: [@sergei_dyshkant](https://t.me/sergei_dyshkant)
- GitHub: [github.com/SergD](https://github.com/SergD)

## 🌟 О проекте

SEO Jobs Hunter - это умный инструмент для мониторинга и анализа SEO вакансий в Telegram каналах. Использует GPT для определения релевантности вакансий и автоматически отправляет уведомления о новых предложениях работы.

### ✨ Особенности
- 🤖 **AI-Powered анализ** - Использует GPT для оценки релевантности вакансий
- 🔄 **Реальное время** - Мгновенные уведомления о новых вакансиях
- 📊 **Умная фильтрация** - Автоматическое определение зарплаты и требований
- 💾 **Excel экспорт** - Сохранение всех вакансий в удобном формате
- 🔍 **Умный поиск** - Распознавание различных вариантов написания 'SEO'

## 💻 Файлы проекта

📄 `new_vacancies_parser_channels.py`
- Основной скрипт мониторинга
- Отслеживает новые сообщения
- Запускает анализ и отправку уведомлений

📄 `parse_channels.py`
- Модуль парсинга каналов
- Содержит логику анализа сообщений
- Извлекает контакты и зарплаты

📄 `seo_channels.py`
- Список мониторируемых каналов
- Здесь можно добавить новые каналы

📄 `send_existing_vacancies.py`
- Отправка существующих вакансий
- Полезно для первого запуска

📄 `telegram_notifier.py`
- Отправка уведомлений в Telegram
- Форматирование сообщений

📄 `stop_words.py`
- Слова для фильтрации
- Помогает отсеять нерелевантные сообщения

## 🔑 Настройка API ключей

1. **Telegram API**
   - Зайдите на https://my.telegram.org
   - Создайте приложение
   - Получите `API_ID` и `API_HASH`

2. **OpenAI API**
   - Зарегистрируйтесь на https://platform.openai.com
   - Создайте API ключ

3. **Создайте файл `.env`:**
```env
API_ID="your_api_id"
API_HASH="your_api_hash"
PHONE="your_phone"
OPENAI_API_KEY="your_openai_api_key"
BOT_TOKEN="your_bot_token"
SEO_FILE="seo_vacancies.xlsx"
```

## 💻 Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/SergD/seo-jobs-hunter.git
cd seo-jobs-hunter
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте `.env` как описано выше

4. Запустите мониторинг:
```bash
python new_vacancies_parser_channels.py
```

## 💾 Результаты

Все найденные вакансии:
- Сохраняются в `seo_vacancies.xlsx`
- Отправляются в ваш Telegram канал

## 🔄 Как это работает

1. 📱 Подключается к указанным Telegram каналам
2. 🔍 Ищет сообщения с ключевыми словами (SEO, СЕО)
3. 🤖 Анализирует текст через GPT
4. 📊 Извлекает важную информацию
5. 📬 Отправляет уведомление, если находит вакансию
6. 💾 Сохраняет в Excel для истории

## ⚙️ Настройка

Все настройки хранятся в трех файлах:
- `.env` - API ключи и основные настройки
- `seo_channels.py` - список каналов для мониторинга
- `stop_words.py` - слова для фильтрации

## 🔒 Безопасность

- Никогда не публикуйте файл `.env`
- Соблюдайте ограничения Telegram API
- Используйте разумные задержки между запросами

## 📝 Лицензия

MIT License © 2024 [SergD (Sergei Dyshkant)](https://t.me/sergei_dyshkant)

## 👏 Благодарности

Разработано [SergD (Sergei Dyshkant)](https://t.me/sergei_dyshkant)

Если у вас есть вопросы или предложения, пишите мне в Telegram!
