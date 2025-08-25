# 📱 Telegram Number Checker Bot

A multi-language Telegram bot that checks if phone numbers are registered on Telegram and returns their User IDs.

## 🌟 Features

- **🌍 Multi-language Support**: English, Bengali, Hindi, Arabic
- **🔒 Admin Approval System**: Users need admin approval to use the bot
- **📱 Global Phone Support**: Works with phone numbers from all countries (+1 to +998)
- **🎯 Instant Results**: Color-coded results (🟡 found, ⚫ not found)
- **⏰ Request Cooldown**: 3-hour cooldown between access requests
- **💾 Database Integration**: Persistent data storage with Supabase
- **🚀 24/7 Deployment**: Ready for Render deployment

## 🛠️ Setup

### Prerequisites

- Python 3.12+
- Telegram Bot Token
- Telegram API ID & Hash
- Supabase Account

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sheikh654sr-web/numbercheckerbot.git
cd numbercheckerbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your credentials
```

4. Run locally:
```bash
python telegram_checker_bot.py
```

## 🌐 Deployment

### Render Deployment

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set environment variables from `render.yaml`
4. Deploy!

The bot will be available at: https://numbercheckerbot.onrender.com

### Environment Variables

```
BOT_TOKEN=your_bot_token
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
ADMIN_USER_ID=admin_user_id
ADMIN_USERNAME=admin_username
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
PORT=10000
```

## 🎯 Usage

### For Users

1. Start the bot: `/start`
2. Choose your language
3. Request access from admin
4. Once approved, send phone numbers to check

### For Admin

- Receive notifications for new access requests
- Approve/reject requests with inline buttons
- Users get automatic notifications of approval status

## 🔧 Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    language TEXT DEFAULT 'en',
    access_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Access Requests Table
```sql
CREATE TABLE access_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT,
    first_name TEXT,
    language TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🎨 Supported Languages

- 🇺🇸 **English** (Default)
- 🇧🇩 **বাংলা** (Bengali)
- 🇮🇳 **हिंदी** (Hindi)
- 🇸🇦 **العربية** (Arabic)

## 📊 Features Overview

### Access Control
- Admin approval required for new users
- 3-hour cooldown between requests
- Persistent approval status

### Phone Number Checking
- Global phone number support
- Bulk checking (multiple numbers at once)
- Color-coded results
- User ID extraction for existing accounts

### User Experience
- Intuitive reply keyboards
- Language preference memory
- Real-time notifications
- Error handling in user's language

## 🔒 Security

- Environment variables for sensitive data
- Admin-only approval system
- User access validation
- Request rate limiting

## 📈 Version 2.0

This is a major update with:
- Complete multi-language support
- Admin approval system
- Database integration
- 24/7 deployment ready
- Enhanced user experience

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is for educational purposes only.

## 👨‍💻 Support

For support, contact: @tasktreasur_support

---

**🌟 Star this repository if you find it useful!**
