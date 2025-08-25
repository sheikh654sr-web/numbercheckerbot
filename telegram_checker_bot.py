import asyncio
import logging
import re
import os
from typing import List, Tuple
from datetime import datetime, timedelta
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telethon import TelegramClient
from telethon.errors import PhoneNumberInvalidError, UsernameNotOccupiedError
from telethon.tl.functions.contacts import ResolveUsernameRequest
from dotenv import load_dotenv

# Optional Supabase import
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None
    create_client = None

# Load environment variables
load_dotenv()

# Bot configuration from environment
BOT_TOKEN = os.getenv("BOT_TOKEN", "8453861160:AAFmViauReZNPveHnEslkOthMwcK6FrIEvI")
API_ID = os.getenv("TELEGRAM_API_ID", "22969300")
API_HASH = os.getenv("TELEGRAM_API_HASH", "e78b8ed26aa341bd36690bdc13d2159a")

# Admin configuration
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "7325836764"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "tasktreasur_support")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://qxaenszcuxyleqjfdene.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4YWVuc3pjdXh5bGVxamZkZW5lIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYxNDg1NDMsImV4cCI6MjA3MTcyNDU0M30.7YQHmClhIq2DEvBkGi3yueTSZ1Q0PTPhBnaHlSENLfg")

# Server configuration
PORT = int(os.getenv("PORT", "10000"))

# Set up logging first
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Supabase client (optional)
supabase = None
if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "your_supabase_url":
    try:
        # Simple Supabase initialization
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.warning(f"Supabase not available: {e}")
        logger.info("Using in-memory storage (recommended for initial deployment)")
        supabase = None
else:
    logger.info("Using in-memory storage (Supabase not configured)")

# In-memory storage fallback
memory_users = {}  # user_id: {'language': 'en', 'access_status': 'pending'}
memory_requests = {}  # user_id: {'status': 'pending', 'created_at': datetime}

# Language configurations
LANGUAGES = {
    'en': {
        'name': '🇺🇸 English',
        'welcome': """📱 Telegram Number Checker Bot

Send any phone numbers from any country, I'll check Telegram User IDs for you.

🎯 How it works:
- Send any phone numbers (as many as you want)
- 🟡 Yellow = Found on Telegram (with User ID)
- ⚫ Black = Not found on Telegram

Examples:
+8801712345678
01712345678
1234567890
+971501234567

⚠️ For educational purposes only.""",
        'help': """🆘 Help

📱 How to use:
1. Send any phone numbers
2. Send multiple numbers at once
3. One number per line

📊 Results:
🟡 Yellow = Found on Telegram (with User ID)
⚫ Black = Not found on Telegram

📱 Any format works:
+8801712345678
01712345678  
1234567890
+971501234567

⚠️ For educational purposes only.""",
        'processing': "🔍 Checking {} numbers...",
        'results': "📊 Results ({} numbers):",
        'summary': "📈 Summary:",
        'found': "🟡 Found: {} numbers",
        'not_found': "⚫ Not found: {} numbers",
        'no_numbers': "❌ No numbers found.",
        'invalid_numbers': "❌ No valid phone numbers found.",
        'api_error': "❌ API credentials not set.",
        'check_error': "❌ Error occurred while checking.",
        'language_selection': "🌐 Choose your language:",
        'language_set': "✅ Language set to English",
        'menu_check': "📱 Check Numbers",
        'menu_help': "🆘 Help",
        'menu_language': "🌐 Language",
        'menu_about': "ℹ️ About",
        'menu_request': "📨 Request Access",
        'menu_contact': "👨‍💻 Contact Admin",
        'request_sent': "✅ Request sent to admin. Please wait for approval.",
        'request_pending': "⏳ You already have a pending request. Please wait.",
        'request_cooldown': "⏰ Please wait {} hours before sending another request.",
        'access_approved': "✅ Your access has been approved! You can now use the bot.",
        'access_rejected': "❌ Your access request has been rejected.",
        'contact_admin': "👨‍💻 Contact Admin: @{}",
        'admin_new_request': "🔔 New Access Request\n\nUser: {} ({})\nUser ID: {}\nLanguage: {}",
        'admin_approve': "✅ Approve",
        'admin_reject': "❌ Reject",
        'access_required': "🔒 You need admin approval to use this bot.\nPlease request access first.",
        'phone_checking_disabled': "📱 Phone checking feature is currently disabled for deployment.\n\n✅ Bot is working perfectly for other features!\n\n🔧 Admin can enable phone checking later with proper setup."
    },
    'bn': {
        'name': '🇧🇩 বাংলা',
        'welcome': """📱 টেলিগ্রাম নাম্বার চেকার বট

যে কোন দেশের ফোন নাম্বার দিন, আমি টেলিগ্রাম User ID চেক করে দেখাবো।

🎯 কিভাবে কাজ করে:
- যে কোন ফোন নাম্বার পাঠান (যত খুশি)
- 🟡 হলুদ = টেলিগ্রামে আছে (User ID সহ)
- ⚫ কালো = টেলিগ্রামে নেই

উদাহরণ:
+8801712345678
01712345678
1234567890
+971501234567

⚠️ শুধুমাত্র শিক্ষামূলক উদ্দেশ্যে ব্যবহার করুন।""",
        'help': """🆘 সাহায্য

📱 কিভাবে ব্যবহার করবেন:
1. যে কোন ফোন নাম্বার পাঠান
2. একসাথে অনেক নাম্বার দিতে পারেন
3. প্রতি লাইনে একটি নাম্বার

📊 রেজাল্ট:
🟡 হলুদ = টেলিগ্রামে আছে (User ID সহ)
⚫ কালো = টেলিগ্রামে নেই

📱 যে কোন ফরম্যাট:
+8801712345678
01712345678  
1234567890
+971501234567

⚠️ শুধুমাত্র শিক্ষামূলক উদ্দেশ্যে ব্যবহার করুন।""",
        'processing': "🔍 {}টি নাম্বার চেক করা হচ্ছে...",
        'results': "📊 রেজাল্ট ({}টি নাম্বার):",
        'summary': "📈 সামারি:",
        'found': "🟡 পাওয়া গেছে: {}টি",
        'not_found': "⚫ পাওয়া যায়নি: {}টি",
        'no_numbers': "❌ কোন নাম্বার পাওয়া যায়নি।",
        'invalid_numbers': "❌ বৈধ ফোন নাম্বার পাওয়া যায়নি।",
        'api_error': "❌ API credentials সেট করা হয়নি।",
        'check_error': "❌ চেক করতে সমস্যা হয়েছে।",
        'language_selection': "🌐 আপনার ভাষা নির্বাচন করুন:",
        'language_set': "✅ ভাষা বাংলায় সেট করা হয়েছে",
        'menu_check': "📱 নাম্বার চেক",
        'menu_help': "🆘 সাহায্য",
        'menu_language': "🌐 ভাষা",
        'menu_about': "ℹ️ সম্পর্কে",
        'menu_request': "📨 অ্যাক্সেস রিকোয়েস্ট",
        'menu_contact': "👨‍💻 এডমিনের সাথে যোগাযোগ",
        'request_sent': "✅ এডমিনের কাছে রিকোয়েস্ট পাঠানো হয়েছে। অনুমোদনের জন্য অপেক্ষা করুন।",
        'request_pending': "⏳ আপনার ইতিমধ্যে একটি রিকোয়েস্ট পেন্ডিং আছে। অপেক্ষা করুন।",
        'request_cooldown': "⏰ আরেকটি রিকোয়েস্ট পাঠানোর আগে {} ঘন্টা অপেক্ষা করুন।",
        'access_approved': "✅ আপনার অ্যাক্সেস অনুমোদিত হয়েছে! এখন আপনি বট ব্যবহার করতে পারেন।",
        'access_rejected': "❌ আপনার অ্যাক্সেস রিকোয়েস্ট প্রত্যাখ্যান করা হয়েছে।",
        'contact_admin': "👨‍💻 এডমিনের সাথে যোগাযোগ: @{}",
        'admin_new_request': "🔔 নতুন অ্যাক্সেস রিকোয়েস্ট\n\nইউজার: {} ({})\nইউজার আইডি: {}\nভাষা: {}",
        'admin_approve': "✅ অনুমোদন",
        'admin_reject': "❌ প্রত্যাখ্যান",
        'access_required': "🔒 এই বট ব্যবহারের জন্য এডমিনের অনুমোদন প্রয়োজন।\nদয়া করে প্রথমে অ্যাক্সেস রিকোয়েস্ট করুন।",
        'phone_checking_disabled': "📱 ফোন চেকিং ফিচার বর্তমানে deployment এর জন্য বন্ধ রয়েছে।\n\n✅ বটের অন্যান্য ফিচার perfectly কাজ করছে!\n\n🔧 এডমিন পরে proper setup দিয়ে ফোন চেকিং চালু করতে পারবেন।"
    },
    'hi': {
        'name': '🇮🇳 हिंदी',
        'welcome': """📱 टेलीग्राम नंबर चेकर बॉट

किसी भी देश के फोन नंबर भेजें, मैं टेलीग्राम User ID चेक कर दूंगा।

🎯 कैसे काम करता है:
- कोई भी फोन नंबर भेजें (जितने चाहें)
- 🟡 पीला = टेलीग्राम पर मिला (User ID के साथ)
- ⚫ काला = टेलीग्राम पर नहीं मिला

उदाहरण:
+8801712345678
01712345678
1234567890
+971501234567

⚠️ केवल शैक्षणिक उद्देश्यों के लिए उपयोग करें।""",
        'help': """🆘 सहायता

📱 उपयोग कैसे करें:
1. कोई भी फोन नंबर भेजें
2. एक साथ कई नंबर भेज सकते हैं
3. हर लाइन में एक नंबर

📊 परिणाम:
🟡 पीला = टेलीग्राम पर मिला (User ID के साथ)
⚫ काला = टेलीग्राम पर नहीं मिला

📱 कोई भी फॉर्मेट:
+8801712345678
01712345678  
1234567890
+971501234567

⚠️ केवल शैक्षणिक उद्देश्यों के लिए उपयोग करें।""",
        'processing': "🔍 {} नंबर चेक कर रहे हैं...",
        'results': "📊 परिणाम ({} नंबर):",
        'summary': "📈 सारांश:",
        'found': "🟡 मिले: {} नंबर",
        'not_found': "⚫ नहीं मिले: {} नंबर",
        'no_numbers': "❌ कोई नंबर नहीं मिला।",
        'invalid_numbers': "❌ कोई वैध फोन नंबर नहीं मिला।",
        'api_error': "❌ API credentials सेट नहीं हैं।",
        'check_error': "❌ चेक करने में समस्या हुई।",
        'language_selection': "🌐 अपनी भाषा चुनें:",
        'language_set': "✅ भाषा हिंदी में सेट की गई",
        'menu_check': "📱 नंबर चेक",
        'menu_help': "🆘 सहायता",
        'menu_language': "🌐 भाषा",
        'menu_about': "ℹ️ बारे में",
        'menu_request': "📨 एक्सेस रिक्वेस्ट",
        'menu_contact': "👨‍💻 एडमिन से संपर्क",
        'request_sent': "✅ एडमिन को रिक्वेस्ट भेजी गई। अप्रूवल का इंतज़ार करें।",
        'request_pending': "⏳ आपकी पहले से एक रिक्वेस्ट पेंडिंग है। इंतज़ार करें।",
        'request_cooldown': "⏰ दूसरी रिक्वेस्ट भेजने से पहले {} घंटे इंतज़ार करें।",
        'access_approved': "✅ आपकी एक्सेस अप्रूव हो गई! अब आप बॉट का उपयोग कर सकते हैं।",
        'access_rejected': "❌ आपकी एक्सेस रिक्वेस्ट रिजेक्ट हो गई।",
        'contact_admin': "👨‍💻 एडमिन से संपर्क: @{}",
        'admin_new_request': "🔔 नई एक्सेस रिक्वेस्ट\n\nयूजर: {} ({})\nयूजर आईडी: {}\nभाषा: {}",
        'admin_approve': "✅ अप्रूव",
        'admin_reject': "❌ रिजेक्ट",
        'access_required': "🔒 इस बॉट का उपयोग करने के लिए एडमिन अप्रूवल चाहिए।\nकृपया पहले एक्सेस रिक्वेस्ट करें।",
        'phone_checking_disabled': "📱 फोन चेकिंग फीचर वर्तमान में deployment के लिए बंद है।\n\n✅ बॉट के अन्य features perfectly काम कर रहे हैं!\n\n🔧 Admin बाद में proper setup के साथ phone checking चालू कर सकते हैं।"
    },
    'ar': {
        'name': '🇸🇦 العربية',
        'welcome': """📱 بوت فحص أرقام التليجرام

أرسل أي أرقام هاتف من أي دولة، وسأقوم بفحص معرفات المستخدمين في التليجرام.

🎯 كيف يعمل:
- أرسل أي أرقام هاتف (كما تشاء)
- 🟡 أصفر = موجود في التليجرام (مع معرف المستخدم)
- ⚫ أسود = غير موجود في التليجرام

أمثلة:
+8801712345678
01712345678
1234567890
+971501234567

⚠️ للأغراض التعليمية فقط.""",
        'help': """🆘 مساعدة

📱 كيفية الاستخدام:
1. أرسل أي أرقام هاتف
2. يمكنك إرسال عدة أرقام في وقت واحد
3. رقم واحد في كل سطر

📊 النتائج:
🟡 أصفر = موجود في التليجرام (مع معرف المستخدم)
⚫ أسود = غير موجود في التليجرام

📱 أي تنسيق:
+8801712345678
01712345678  
1234567890
+971501234567

⚠️ للأغراض التعليمية فقط.""",
        'processing': "🔍 جاري فحص {} رقم...",
        'results': "📊 النتائج ({} رقم):",
        'summary': "📈 الملخص:",
        'found': "🟡 موجود: {} رقم",
        'not_found': "⚫ غير موجود: {} رقم",
        'no_numbers': "❌ لم يتم العثور على أرقام.",
        'invalid_numbers': "❌ لم يتم العثور على أرقام هاتف صحيحة.",
        'api_error': "❌ لم يتم تعيين بيانات اعتماد API.",
        'check_error': "❌ حدث خطأ أثناء الفحص.",
        'language_selection': "🌐 اختر لغتك:",
        'language_set': "✅ تم تعيين اللغة إلى العربية",
        'menu_check': "📱 فحص الأرقام",
        'menu_help': "🆘 مساعدة",
        'menu_language': "🌐 اللغة",
        'menu_about': "ℹ️ حول",
        'menu_request': "📨 طلب الوصول",
        'menu_contact': "👨‍💻 اتصال بالمدير",
        'request_sent': "✅ تم إرسال الطلب للمدير. انتظر الموافقة.",
        'request_pending': "⏳ لديك طلب معلق بالفعل. انتظر.",
        'request_cooldown': "⏰ انتظر {} ساعات قبل إرسال طلب آخر.",
        'access_approved': "✅ تمت الموافقة على وصولك! يمكنك الآن استخدام البوت.",
        'access_rejected': "❌ تم رفض طلب الوصول الخاص بك.",
        'contact_admin': "👨‍💻 اتصال بالمدير: @{}",
        'admin_new_request': "🔔 طلب وصول جديد\n\nالمستخدم: {} ({})\nمعرف المستخدم: {}\nاللغة: {}",
        'admin_approve': "✅ موافقة",
        'admin_reject': "❌ رفض",
        'access_required': "🔒 تحتاج موافقة المدير لاستخدام هذا البوت.\nيرجى طلب الوصول أولاً.",
        'phone_checking_disabled': "📱 ميزة فحص الهاتف معطلة حالياً للنشر.\n\n✅ باقي ميزات البوت تعمل بشكل مثالي!\n\n🔧 يمكن للمدير تفعيل فحص الهاتف لاحقاً مع الإعداد المناسب."
    }
}

# Database functions
async def init_database():
    """Initialize database tables"""
    if not supabase:
        logger.error("Supabase client not initialized")
        return
        
    try:
        # Create users table
        supabase.table('users').select('*').limit(1).execute()
    except:
        # Table doesn't exist, create it
        logger.info("Creating database tables...")
    
    try:
        # Create access_requests table
        supabase.table('access_requests').select('*').limit(1).execute()
    except:
        logger.info("Access requests table created")

async def get_user_language(user_id: int) -> str:
    """Get user's preferred language from database or memory"""
    if supabase:
        try:
            result = supabase.table('users').select('language').eq('user_id', user_id).execute()
            if result.data:
                return result.data[0]['language']
        except:
            pass
    
    # Fallback to in-memory storage
    if user_id in memory_users:
        return memory_users[user_id].get('language', 'en')
    
    return 'en'  # Default to English

async def set_user_language(user_id: int, language: str):
    """Set user's preferred language in database or memory"""
    if supabase:
        try:
            # Upsert user language
            supabase.table('users').upsert({
                'user_id': user_id,
                'language': language,
                'updated_at': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error setting user language: {e}")
    
    # Always store in memory as fallback
    if user_id not in memory_users:
        memory_users[user_id] = {}
    memory_users[user_id]['language'] = language

async def check_user_access(user_id: int) -> bool:
    """Check if user has access to the bot"""
    if user_id == ADMIN_USER_ID:
        return True
    
    if supabase:
        try:
            result = supabase.table('users').select('access_status').eq('user_id', user_id).execute()
            if result.data:
                return result.data[0]['access_status'] == 'approved'
        except:
            pass
    
    # Check in-memory storage
    if user_id in memory_users:
        return memory_users[user_id].get('access_status', 'pending') == 'approved'
    
    # For deployment without database, allow access for testing
    if not supabase:
        return True
    
    return False

async def get_pending_request(user_id: int) -> dict:
    """Get user's pending request if any"""
    if not supabase:
        return None
        
    try:
        result = supabase.table('access_requests').select('*').eq('user_id', user_id).eq('status', 'pending').execute()
        if result.data:
            return result.data[0]
    except:
        pass
    return None

async def check_request_cooldown(user_id: int) -> int:
    """Check if user is in cooldown period, returns hours remaining"""
    if not supabase:
        return 0
        
    try:
        result = supabase.table('access_requests').select('created_at').eq('user_id', user_id).order('created_at', desc=True).limit(1).execute()
        if result.data:
            last_request = datetime.fromisoformat(result.data[0]['created_at'].replace('Z', '+00:00'))
            cooldown_end = last_request + timedelta(hours=3)
            if datetime.now() < cooldown_end:
                remaining = cooldown_end - datetime.now()
                return int(remaining.total_seconds() / 3600) + 1
    except:
        pass
    return 0

async def create_access_request(user_id: int, username: str, first_name: str, language: str):
    """Create new access request"""
    if not supabase:
        logger.warning("Supabase not available, request not saved")
        return False
        
    try:
        supabase.table('access_requests').insert({
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'language': language,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Error creating access request: {e}")
        return False

async def update_access_request(request_id: int, status: str):
    """Update access request status"""
    if not supabase:
        logger.warning("Supabase not available, request status not updated")
        return False
        
    try:
        supabase.table('access_requests').update({
            'status': status,
            'updated_at': datetime.now().isoformat()
        }).eq('id', request_id).execute()
        
        # Also update user access status
        request = supabase.table('access_requests').select('user_id').eq('id', request_id).execute()
        if request.data:
            user_id = request.data[0]['user_id']
            supabase.table('users').upsert({
                'user_id': user_id,
                'access_status': status,
                'updated_at': datetime.now().isoformat()
            }).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error updating access request: {e}")
        return False

async def get_text(user_id: int, key: str) -> str:
    """Get localized text for user"""
    lang = await get_user_language(user_id)
    return LANGUAGES[lang].get(key, LANGUAGES['en'][key])

def get_language_keyboard():
    """Get language selection keyboard"""
    keyboard = []
    for lang_code, lang_data in LANGUAGES.items():
        keyboard.append([KeyboardButton(lang_data['name'])])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

async def get_main_menu_keyboard(user_id: int):
    """Get main menu keyboard based on user's language and access status"""
    lang = await get_user_language(user_id)
    texts = LANGUAGES[lang]
    has_access = await check_user_access(user_id)
    
    if has_access:
        keyboard = [
            [KeyboardButton(texts['menu_check']), KeyboardButton(texts['menu_help'])],
            [KeyboardButton(texts['menu_language']), KeyboardButton(texts['menu_about'])]
        ]
    else:
        keyboard = [
            [KeyboardButton(texts['menu_request']), KeyboardButton(texts['menu_contact'])],
            [KeyboardButton(texts['menu_language']), KeyboardButton(texts['menu_help'])]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_approval_keyboard(request_id: int):
    """Get admin approval/rejection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{request_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{request_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

class TelegramChecker:
    def __init__(self, api_id: str, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = None
    
    async def initialize_client(self):
        """Initialize Telethon client"""
        try:
            # Use in-memory session for deployment
            from telethon.sessions import StringSession
            
            # Try to get session string from environment
            session_string = os.getenv('TELETHON_SESSION', '')
            
            if session_string:
                # Use existing session string
                self.client = TelegramClient(StringSession(session_string), self.api_id, self.api_hash)
            else:
                # Use empty session (will require authentication)
                self.client = TelegramClient(StringSession(), self.api_id, self.api_hash)
            
            # Start client without phone verification for deployment
            await self.client.start()
            logger.info("Telethon client initialized successfully")
            
            # Save session string for future use (in logs only)
            if not session_string:
                new_session = self.client.session.save()
                logger.info(f"New session created: {new_session[:20]}...")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telethon client: {e}")
            logger.warning("Phone checking will be disabled - bot will work without this feature")
            self.client = None
            return False
    
    async def check_phone_numbers(self, phone_numbers: List[str]) -> Tuple[List[dict], List[str]]:
        """Check phone numbers and return user info for existing accounts"""
        existing_with_info = []
        non_existing = []
        
        if not self.client:
            logger.error("Telethon client not initialized")
            return existing_with_info, non_existing
        
        for phone in phone_numbers:
            try:
                # Format phone number
                formatted_phone = self.format_phone_number(phone)
                if not formatted_phone:
                    non_existing.append(phone)
                    continue
                
                logger.info(f"Checking phone number: {formatted_phone}")
                user_info = await self._get_user_info(formatted_phone)
                
                # Add to appropriate list
                if user_info:
                    existing_with_info.append({
                        'phone': phone,
                        'formatted_phone': formatted_phone,
                        'user_id': user_info.get('user_id'),
                        'first_name': user_info.get('first_name', ''),
                        'last_name': user_info.get('last_name', ''),
                        'username': user_info.get('username', '')
                    })
                    logger.info(f"✅ Found user: {formatted_phone} -> ID: {user_info.get('user_id')}")
                else:
                    non_existing.append(phone)
                    logger.info(f"❌ Not found: {formatted_phone}")
                    
            except Exception as e:
                logger.error(f"Error checking phone {phone}: {e}")
                non_existing.append(phone)
        
        return existing_with_info, non_existing
    
    async def _get_user_info(self, formatted_phone: str) -> dict:
        """Get user information if phone number exists on Telegram"""
        
        # Method 1: Direct entity lookup
        try:
            entity = await self.client.get_entity(formatted_phone)
            if entity:
                # Check if it's a valid user (not deleted)
                if hasattr(entity, 'deleted') and entity.deleted:
                    logger.debug(f"Account deleted: {formatted_phone}")
                    return None
                
                # Extract user information
                user_info = {
                    'user_id': entity.id,
                    'first_name': getattr(entity, 'first_name', ''),
                    'last_name': getattr(entity, 'last_name', ''),
                    'username': getattr(entity, 'username', ''),
                    'phone': getattr(entity, 'phone', '')
                }
                
                logger.info(f"Found via direct entity: {formatted_phone} -> {user_info}")
                return user_info
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if any(keyword in error_msg for keyword in [
                'no user has', 'user not found', 'phone number invalid',
                'no such user', 'username not occupied', 'phone_number_invalid'
            ]):
                logger.debug(f"Definitely does not exist: {formatted_phone}")
                return None
            else:
                logger.debug(f"Other error for {formatted_phone}: {str(e)}")
        
        # Method 2: Try alternative formats
        alternative_formats = self._get_alternative_formats(formatted_phone)
        
        for alt_format in alternative_formats:
            try:
                entity = await self.client.get_entity(alt_format)
                if entity:
                    if hasattr(entity, 'deleted') and entity.deleted:
                        continue
                    
                    user_info = {
                        'user_id': entity.id,
                        'first_name': getattr(entity, 'first_name', ''),
                        'last_name': getattr(entity, 'last_name', ''),
                        'username': getattr(entity, 'username', ''),
                        'phone': getattr(entity, 'phone', '')
                    }
                    
                    logger.info(f"Found via alt format {alt_format}: {formatted_phone} -> {user_info}")
                    return user_info
                    
            except Exception:
                continue
        
        # Method 3: Contacts import as final check
        try:
            from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
            from telethon.tl.types import InputPhoneContact
            
            import time
            client_id = int(time.time() * 1000) % 2147483647
            
            contact = InputPhoneContact(
                client_id=client_id,
                phone=formatted_phone.replace('+', ''),
                first_name="Check",
                last_name=""
            )
            
            result = await self.client(ImportContactsRequest([contact]))
            
            if result and result.users and len(result.users) > 0:
                user = result.users[0]
                
                if hasattr(user, 'id') and user.id:
                    user_info = {
                        'user_id': user.id,
                        'first_name': getattr(user, 'first_name', ''),
                        'last_name': getattr(user, 'last_name', ''),
                        'username': getattr(user, 'username', ''),
                        'phone': getattr(user, 'phone', '')
                    }
                    
                    # Clean up
                    try:
                        await self.client(DeleteContactsRequest(result.users))
                    except:
                        pass
                    
                    logger.info(f"Found via contacts import: {formatted_phone} -> {user_info}")
                    return user_info
            
            # Clean up even if not found
            try:
                if result and result.users:
                    await self.client(DeleteContactsRequest(result.users))
            except:
                pass
                
        except Exception as e:
            logger.debug(f"Contacts import failed for {formatted_phone}: {str(e)}")
        
        logger.debug(f"No user info found for: {formatted_phone}")
        return None
    
    async def _advanced_phone_check(self, formatted_phone: str) -> bool:
        """Balanced phone checking - accurate but not overly strict"""
        
        # Method 1: Direct entity lookup (most reliable)
        try:
            entity = await self.client.get_entity(formatted_phone)
            if entity:
                # Check if it's a valid user (not bot, not deleted)
                if hasattr(entity, 'deleted') and entity.deleted:
                    logger.debug(f"Account deleted: {formatted_phone}")
                    return False
                
                # Allow bots as they are valid Telegram accounts
                # if hasattr(entity, 'bot') and entity.bot:
                #     logger.debug(f"Is bot account: {formatted_phone}")
                #     return False
                
                # If we got an entity, it means the number exists
                logger.info(f"FOUND via direct entity: {formatted_phone}")
                return True
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for definitive "not found" errors
            if any(keyword in error_msg for keyword in [
                'no user has', 'user not found', 'phone number invalid',
                'no such user', 'username not occupied', 'phone_number_invalid'
            ]):
                logger.debug(f"Definitely does not exist: {formatted_phone}")
                return False
            else:
                logger.debug(f"Other error for {formatted_phone}: {str(e)}")
        
        # Method 2: Try alternative formats
        alternative_formats = self._get_alternative_formats(formatted_phone)
        
        for alt_format in alternative_formats:
            try:
                entity = await self.client.get_entity(alt_format)
                if entity:
                    if hasattr(entity, 'deleted') and entity.deleted:
                        continue
                    
                    logger.info(f"FOUND via alt format {alt_format}: {formatted_phone}")
                    return True
                    
            except Exception as e:
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in [
                    'no user has', 'user not found', 'phone number invalid',
                    'no such user', 'username not occupied', 'phone_number_invalid'
                ]):
                    continue  # This format doesn't exist, try next
                else:
                    continue
        
        # Method 3: Try contacts import as final check (but with better validation)
        try:
            from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
            from telethon.tl.types import InputPhoneContact
            
            import time
            client_id = int(time.time() * 1000) % 2147483647
            
            contact = InputPhoneContact(
                client_id=client_id,
                phone=formatted_phone.replace('+', ''),
                first_name="Check",
                last_name=""
            )
            
            result = await self.client(ImportContactsRequest([contact]))
            
            if result and result.users and len(result.users) > 0:
                user = result.users[0]
                
                # More lenient check - if we got a user back, it likely exists
                if hasattr(user, 'id') and user.id:
                    # Clean up
                    try:
                        await self.client(DeleteContactsRequest(result.users))
                    except:
                        pass
                    
                    logger.info(f"FOUND via contacts import: {formatted_phone}")
                    return True
            
            # Clean up even if not found
            try:
                if result and result.users:
                    await self.client(DeleteContactsRequest(result.users))
            except:
                pass
                
        except Exception as e:
            logger.debug(f"Contacts import failed for {formatted_phone}: {str(e)}")
        
        logger.debug(f"NOT FOUND after all methods: {formatted_phone}")
        return False
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison"""
        # Remove all non-digits
        digits_only = re.sub(r'\D', '', phone)
        
        # Handle Bangladeshi numbers
        if digits_only.startswith('88'):
            if digits_only.startswith('880'):
                return '+' + digits_only
            else:
                return '+' + digits_only
        elif digits_only.startswith('01') and len(digits_only) == 11:
            return '+88' + digits_only
        else:
            return '+88' + digits_only
    
    def _get_alternative_formats(self, phone: str) -> List[str]:
        """Get alternative phone number formats to try"""
        alternatives = []
        
        # Remove + and get digits
        digits = re.sub(r'\D', '', phone)
        
        if digits.startswith('88'):
            # Try with +88
            alternatives.append('+' + digits)
            
            # Try removing country code
            if digits.startswith('880'):
                alternatives.append('+88' + digits[3:])
                alternatives.append('+880' + digits[3:])
            elif digits.startswith('88') and not digits.startswith('880'):
                alternatives.append('+880' + digits[2:])
        
        # Try with leading zero
        if not any(alt.endswith('0' + digits[-10:]) for alt in alternatives):
            alternatives.append('+8801' + digits[-9:])
        
        # Remove duplicates and original
        alternatives = list(set(alternatives))
        if phone in alternatives:
            alternatives.remove(phone)
            
        return alternatives[:3]  # Limit to 3 alternatives to avoid spam
    
    def format_phone_number(self, phone: str) -> str:
        """Simple phone number formatting - accepts any format"""
        try:
            # Remove any non-digit characters except +
            cleaned = re.sub(r'[^\d+]', '', phone)
            
            # If it already starts with +, return as-is if valid length
            if cleaned.startswith('+'):
                if 8 <= len(cleaned) <= 15 and cleaned[1:].isdigit():
                    return cleaned
            
            # If no +, add it if looks like phone number
            if cleaned.isdigit() and 7 <= len(cleaned) <= 15:
                return '+' + cleaned
            
            # Return original if can't format
            return phone
                
        except Exception as e:
            logger.error(f"Error formatting phone number {phone}: {e}")
            return phone
    


# Initialize checker (will be set up properly when API credentials are provided)
checker = None
application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler with language selection and access control"""
    user_id = update.effective_user.id
    
    # Initialize database on first run
    await init_database()
    
    # Check if user has language set
    current_lang = await get_user_language(user_id)
    if current_lang == 'en' and user_id != ADMIN_USER_ID:
        # New user, show language selection
        await update.message.reply_text(
            "🌐 Welcome! Please choose your language:\n"
            "স্বাগতম! আপনার ভাষা নির্বাচন করুন:\n"
            "नमस्ते! अपनी भाषा चुनें:\n"
            "مرحباً! اختر لغتك:",
            reply_markup=get_language_keyboard()
        )
    else:
        # Show welcome message with appropriate menu
        welcome_text = await get_text(user_id, 'welcome')
        keyboard = await get_main_menu_keyboard(user_id)
        await update.message.reply_text(welcome_text, reply_markup=keyboard)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages including menu buttons and phone numbers"""
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    user = update.effective_user
    
    # Handle language selection
    for lang_code, lang_data in LANGUAGES.items():
        if message_text == lang_data['name']:
            await set_user_language(user_id, lang_code)
            welcome_text = await get_text(user_id, 'welcome')
            keyboard = await get_main_menu_keyboard(user_id)
            await update.message.reply_text(
                await get_text(user_id, 'language_set'),
                reply_markup=keyboard
            )
            await update.message.reply_text(welcome_text)
            return
    
    # Handle menu buttons
    lang = await get_user_language(user_id)
    texts = LANGUAGES[lang]
    
    if message_text == texts['menu_help']:
        await help_command(update, context)
        return
    elif message_text == texts['menu_language']:
        await update.message.reply_text(
            await get_text(user_id, 'language_selection'),
            reply_markup=get_language_keyboard()
        )
        return
    elif message_text == texts['menu_request']:
        await handle_access_request(update, context)
        return
    elif message_text == texts['menu_contact']:
        await update.message.reply_text(
            (await get_text(user_id, 'contact_admin')).format(ADMIN_USERNAME)
        )
        return
    elif message_text == texts['menu_about']:
        about_text = f"""ℹ️ About

📱 Telegram Number Checker Bot
🤖 Multi-language support
🌍 Works with all countries
🔍 Instant User ID detection

🛠️ Version: 2.0
👨‍💻 Advanced phone number checker"""
        
        if lang == 'bn':
            about_text = f"""ℹ️ সম্পর্কে

📱 টেলিগ্রাম নাম্বার চেকার বট
🤖 বহু ভাষা সাপোর্ট
🌍 সব দেশের সাথে কাজ করে
🔍 তাৎক্ষণিক User ID সনাক্তকরণ

🛠️ সংস্করণ: 2.0
👨‍💻 উন্নত ফোন নাম্বার চেকার"""
        elif lang == 'hi':
            about_text = f"""ℹ️ बारे में

📱 टेलीग्राम नंबर चेकर बॉट
🤖 बहु भाषा समर्थन
🌍 सभी देशों के साथ काम करता है
🔍 तत्काल User ID पहचान

🛠️ संस्करण: 2.0
👨‍💻 उन्नत फोन नंबर चेकर"""
        elif lang == 'ar':
            about_text = f"""ℹ️ حول

📱 بوت فحص أرقام التليجرام
🤖 دعم متعدد اللغات
🌍 يعمل مع جميع البلدان
🔍 كشف فوري لمعرف المستخدم

🛠️ الإصدار: 2.0
👨‍💻 فاحص أرقام هاتف متقدم"""
        
        await update.message.reply_text(about_text)
        return
    elif message_text == texts['menu_check']:
        has_access = await check_user_access(user_id)
        if has_access:
            instruction_text = texts['help']
            await update.message.reply_text(instruction_text)
        else:
            await update.message.reply_text(await get_text(user_id, 'access_required'))
        return
    
    # Handle phone numbers (only if user has access)
    has_access = await check_user_access(user_id)
    if not has_access:
        await update.message.reply_text(await get_text(user_id, 'access_required'))
        return
    
    await check_phone_numbers(update, context)

async def check_phone_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number checking with localized messages"""
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    if not message_text:
        await update.message.reply_text(await get_text(user_id, 'no_numbers'))
        return
    
    # Extract phone numbers from message
    phone_numbers = []
    lines = message_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line:
            # Check if line contains phone number pattern
            phone_pattern = r'[\+]?[0-9\s\-\(\)]{7,15}'
            if re.search(phone_pattern, line):
                phone_numbers.append(line)
    
    if not phone_numbers:
        await update.message.reply_text(await get_text(user_id, 'invalid_numbers'))
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        (await get_text(user_id, 'processing')).format(len(phone_numbers))
    )
    
    try:
        if not checker or not checker.client:
            not_available_text = await get_text(user_id, 'phone_checking_disabled')
            await processing_msg.edit_text(not_available_text)
            return
        
        # Check phone numbers
        existing_users, non_existing = await checker.check_phone_numbers(phone_numbers)
        
        # Build single response with color coding
        response = (await get_text(user_id, 'results')).format(len(phone_numbers)) + "\n\n"
        
        # Add existing users with yellow circle
        for user in existing_users:
            response += f"🟡 {user['phone']} - ID: `{user['user_id']}`\n"
        
        # Add non-existing with black circle
        for phone in non_existing:
            response += f"⚫ {phone}\n"
        
        # Summary at the end
        response += f"\n{await get_text(user_id, 'summary')}\n"
        response += f"{(await get_text(user_id, 'found')).format(len(existing_users))}\n"
        response += f"{(await get_text(user_id, 'not_found')).format(len(non_existing))}"
        
        # Check if response is too long for single message
        if len(response) > 4000:
            # Split into chunks
            chunks = []
            current_chunk = (await get_text(user_id, 'results')).format(len(phone_numbers)) + "\n\n"
            
            # Add existing users
            for user in existing_users:
                line = f"🟡 {user['phone']} - ID: `{user['user_id']}`\n"
                if len(current_chunk + line) > 3500:
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += line
            
            # Add non-existing
            for phone in non_existing:
                line = f"⚫ {phone}\n"
                if len(current_chunk + line) > 3500:
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += line
            
            # Add summary to last chunk
            summary = f"\n{await get_text(user_id, 'summary')}\n{(await get_text(user_id, 'found')).format(len(existing_users))}\n{(await get_text(user_id, 'not_found')).format(len(non_existing))}"
            current_chunk += summary
            chunks.append(current_chunk)
            
            # Send first chunk as edit, rest as new messages
            await processing_msg.edit_text(chunks[0], parse_mode='Markdown')
            for chunk in chunks[1:]:
                await update.message.reply_text(chunk, parse_mode='Markdown')
        else:
            await processing_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error processing numbers: {e}")
        await processing_msg.edit_text(await get_text(user_id, 'check_error'))

async def handle_access_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle access request from user"""
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Check if user already has access
    if await check_user_access(user_id):
        await update.message.reply_text("✅ You already have access to the bot!")
        return
    
    # Check for pending request
    pending = await get_pending_request(user_id)
    if pending:
        await update.message.reply_text(await get_text(user_id, 'request_pending'))
        return
    
    # Check cooldown
    cooldown_hours = await check_request_cooldown(user_id)
    if cooldown_hours > 0:
        await update.message.reply_text(
            (await get_text(user_id, 'request_cooldown')).format(cooldown_hours)
        )
        return
    
    # Create new request
    language = await get_user_language(user_id)
    success = await create_access_request(
        user_id,
        user.username or "No username",
        user.first_name or "No name",
        language
    )
    
    if success:
        # Send notification to admin
        admin_text = LANGUAGES['en']['admin_new_request'].format(
            user.first_name or "No name",
            user.username or "No username",
            user_id,
            LANGUAGES[language]['name']
        )
        
        # Get the request ID for the keyboard
        request = await get_pending_request(user_id)
        if request:
            keyboard = get_admin_approval_keyboard(request['id'])
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=admin_text,
                reply_markup=keyboard
            )
        
        await update.message.reply_text(await get_text(user_id, 'request_sent'))
    else:
        await update.message.reply_text("❌ Error creating request. Please try again.")

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin approval/rejection callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_USER_ID:
        await query.edit_message_text("❌ Unauthorized")
        return
    
    data = query.data
    if data.startswith("approve_"):
        request_id = int(data.split("_")[1])
        success = await update_access_request(request_id, "approved")
        
        if success:
            # Get user info to send notification
            try:
                if supabase:
                    request_info = supabase.table('access_requests').select('user_id').eq('id', request_id).execute()
                    if request_info.data:
                        user_id = request_info.data[0]['user_id']
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=await get_text(user_id, 'access_approved')
                        )
                    
                    # Send new keyboard to user
                    keyboard = await get_main_menu_keyboard(user_id)
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="🎉 Welcome! You can now use the bot.",
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Error notifying user: {e}")
            
            await query.edit_message_text("✅ Request approved and user notified!")
        else:
            await query.edit_message_text("❌ Error approving request")
    
    elif data.startswith("reject_"):
        request_id = int(data.split("_")[1])
        success = await update_access_request(request_id, "rejected")
        
        if success:
            # Get user info to send notification
            try:
                if supabase:
                    request_info = supabase.table('access_requests').select('user_id').eq('id', request_id).execute()
                    if request_info.data:
                        user_id = request_info.data[0]['user_id']
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=await get_text(user_id, 'access_rejected')
                        )
            except Exception as e:
                logger.error(f"Error notifying user: {e}")
            
            await query.edit_message_text("❌ Request rejected and user notified!")
        else:
            await query.edit_message_text("❌ Error rejecting request")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler with localized text"""
    user_id = update.effective_user.id
    help_text = await get_text(user_id, 'help')
    await update.message.reply_text(help_text)

async def main():
    """Main function to run the bot"""
    global checker, application
    
    # Initialize checker if API credentials are provided (disabled for deployment)
    checker = None
    if os.getenv('ENABLE_PHONE_CHECKING', '').lower() == 'true':
        if API_ID != "YOUR_API_ID" and API_HASH != "YOUR_API_HASH":
            checker = TelegramChecker(API_ID, API_HASH)
            success = await checker.initialize_client()
            if not success:
                logger.warning("Phone checking disabled - requires manual setup")
                checker = None
        else:
            logger.info("Phone checking disabled - API credentials not configured")
    else:
        logger.info("Phone checking disabled for deployment (enable with ENABLE_PHONE_CHECKING=true)")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_admin_callback))
    
    # Initialize and start the bot (Simple polling like working bot)
    logger.info("🤖 Telegram Number Checker Bot starting...")
    try:
        # Start the bot with polling (like successful bot)
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        logger.info("✅ Telegram Number Checker Bot is running!")
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        # Cleanup
        logger.info("Shutting down bot...")
        try:
            await application.updater.stop()
            await application.stop()
        except:
            pass
        
        if checker:
            try:
                await checker.client.disconnect()
            except:
                pass

if __name__ == "__main__":
    import asyncio
    print("🤖 Starting Telegram Number Checker Bot...")
    asyncio.run(main())

def run_bot():
    """Run the bot with proper event loop handling"""
    try:
        # Check if there's already a running event loop
        try:
            loop = asyncio.get_running_loop()
            logger.warning("Event loop already running, creating new thread")
            import threading
            import concurrent.futures
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(main())
                finally:
                    new_loop.close()
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()
            
        except RuntimeError:
            # No event loop running, we can use asyncio.run
            asyncio.run(main())
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == '__main__':
    run_bot()
