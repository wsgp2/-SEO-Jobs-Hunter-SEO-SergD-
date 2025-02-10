<div align="center">

# 🔍 SEO Jobs Hunter

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT-green.svg)](https://platform.openai.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

### Smart SEO Job Parser from Telegram with GPT Analysis

English | [Русский](README.md)

</div>

## 👨‍💻 Author

**SergD (Sergei Dyshkant)**
- Telegram: [@sergei_dyshkant](https://t.me/sergei_dyshkant)
- GitHub: [github.com/SergD](https://github.com/SergD)

## 🌟 About

SEO Jobs Hunter is a smart tool for monitoring and analyzing SEO job vacancies in Telegram channels. It uses GPT to determine the relevance of vacancies and automatically sends notifications about new job offers.

### ✨ Features
- 🤖 **AI-Powered Analysis** - Uses GPT to evaluate job relevance
- 🔄 **Real-time Updates** - Instant notifications about new vacancies
- 📊 **Smart Filtering** - Automatic salary and requirements detection
- 💾 **Excel Export** - Save all vacancies in a convenient format
- 🔍 **Smart Search** - Recognition of various 'SEO' spelling variants

## 💻 Project Files

📄 `new_vacancies_parser_channels.py`
- Main monitoring script
- Tracks new messages
- Launches analysis and notification sending

📄 `parse_channels.py`
- Channel parsing module
- Contains message analysis logic
- Extracts contacts and salaries

📄 `seo_channels.py`
- List of monitored channels
- Add new channels here

📄 `send_existing_vacancies.py`
- Send existing vacancies
- Useful for first launch

📄 `telegram_notifier.py`
- Send notifications to Telegram
- Message formatting

📄 `stop_words.py`
- Words for filtering
- Helps filter out irrelevant messages

## 🔑 API Keys Setup

1. **Telegram API**
   - Go to https://my.telegram.org
   - Create an application
   - Get `API_ID` and `API_HASH`

2. **OpenAI API**
   - Register at https://platform.openai.com
   - Create API key

3. **Create `.env` file:**
```env
API_ID="your_api_id"
API_HASH="your_api_hash"
PHONE="your_phone"
OPENAI_API_KEY="your_openai_api_key"
BOT_TOKEN="your_bot_token"
SEO_FILE="seo_vacancies.xlsx"
```

## 💻 Installation

1. Clone the repository:
```bash
git clone https://github.com/SergD/seo-jobs-hunter.git
cd seo-jobs-hunter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure `.env` as described above

4. Start monitoring:
```bash
python new_vacancies_parser_channels.py
```

## 💾 Results

All found vacancies:
- Saved to `seo_vacancies.xlsx`
- Sent to your Telegram channel

## 🔄 How It Works

1. 📱 Connects to specified Telegram channels
2. 🔍 Searches for messages with keywords (SEO)
3. 🤖 Analyzes text through GPT
4. 📊 Extracts important information
5. 📬 Sends notification if a vacancy is found
6. 💾 Saves to Excel for history

## ⚙️ Configuration

All settings are stored in three files:
- `.env` - API keys and main settings
- `seo_channels.py` - list of channels to monitor
- `stop_words.py` - words for filtering

## 🔒 Security

- Never publish your `.env` file
- Follow Telegram API limitations
- Use reasonable delays between requests

## 📝 License

MIT License © 2024 [SergD (Sergei Dyshkant)](https://t.me/sergei_dyshkant)

## 👏 Acknowledgments

Developed by [SergD (Sergei Dyshkant)](https://t.me/sergei_dyshkant)

If you have any questions or suggestions, contact me on Telegram!
