# Supabase Database Setup Guide

## 📊 Database Configuration for Telegram Number Checker Bot

### 🚀 Quick Setup Steps:

#### 1. **Open Supabase Dashboard**
- Go to your project: https://qxaenszcuxyleqjfdene.supabase.co
- Navigate to **SQL Editor**

#### 2. **Run Setup Script**
- Copy the entire content from `supabase_setup.sql`
- Paste in SQL Editor
- Click **RUN** ▶️

#### 3. **Verify Tables Created**
Check these tables are created:
- ✅ `users` - User preferences and access
- ✅ `access_requests` - User access requests  
- ✅ `admin_actions` - Admin activity logs
- ✅ `bot_settings` - Bot configuration

---

## 📋 Database Schema Overview

### **Tables Created:**

#### **1. users**
```sql
- id (BIGINT) - Telegram User ID
- username (TEXT) - Telegram Username
- first_name (TEXT) - User's name
- language (TEXT) - Preferred language
- access_status (TEXT) - pending/approved/rejected
- created_at, updated_at
```

#### **2. access_requests**
```sql
- id (SERIAL) - Auto-increment ID
- user_id (BIGINT) - Telegram User ID
- status (TEXT) - Request status
- requested_at - Request timestamp
- expires_at - Expiration (3 hours)
```

#### **3. admin_actions**
```sql
- admin_id (BIGINT) - Admin User ID
- action_type (TEXT) - Action performed
- target_user_id (BIGINT) - Target user
- performed_at - Action timestamp
```

#### **4. bot_settings**
```sql
- key (TEXT) - Setting name
- value (TEXT) - Setting value
- description (TEXT) - Setting description
```

---

## 🛠️ Database Functions

### **Built-in Functions:**
- `get_user_access_status(user_id)` - Check user access
- `check_request_cooldown(user_id)` - Verify request timing
- `cleanup_expired_requests()` - Remove old requests

### **Auto-features:**
- ✅ Automatic timestamp updates
- ✅ Request expiration (3 hours)
- ✅ Performance indexes
- ✅ Data integrity constraints

---

## 🔧 Manual Operations (Optional)

### **View All Users:**
```sql
SELECT * FROM users ORDER BY created_at DESC;
```

### **View Pending Requests:**
```sql
SELECT * FROM access_requests 
WHERE status = 'pending' 
ORDER BY requested_at DESC;
```

### **Approve User Manually:**
```sql
UPDATE users SET access_status = 'approved' WHERE id = USER_ID_HERE;
UPDATE access_requests SET status = 'approved' WHERE user_id = USER_ID_HERE;
```

### **Clean Expired Requests:**
```sql
SELECT cleanup_expired_requests();
```

### **Admin Dashboard View:**
```sql
SELECT * FROM admin_dashboard LIMIT 20;
```

---

## ⚙️ Environment Variables

Make sure these are set in your bot:
```env
SUPABASE_URL=https://qxaenszcuxyleqjfdene.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF4YWVuc3pjdXh5bGVxamZkZW5lIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYxNDg1NDMsImV4cCI6MjA3MTcyNDU0M30.7YQHmClhIq2DEvBkGi3yueTSZ1Q0PTPhBnaHlSENLfg
```

---

## 🎯 After Setup

1. **Bot will automatically connect** to database
2. **User data will be stored** persistently  
3. **Admin system will work** with proper tracking
4. **Language preferences** will be saved
5. **Access requests** will be managed properly

---

## 🐛 Troubleshooting

### **If script fails:**
- Check Supabase connection
- Verify permissions
- Run sections individually

### **If bot can't connect:**
- Verify environment variables
- Check Supabase API key
- Confirm project URL

### **Database not working:**
- Bot will fallback to in-memory storage
- Core features still work
- Admin system uses temporary data

---

**✅ Once you run the SQL script, your bot's database will be fully configured!**
