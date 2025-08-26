-- Telegram Number Checker Bot - Supabase Database Setup
-- Run this script in Supabase SQL Editor to create required tables

-- 1. Create users table for storing user preferences and access status
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,                    -- Telegram User ID
    username TEXT,                            -- Telegram Username (optional)
    first_name TEXT,                          -- User's first name
    last_name TEXT,                           -- User's last name (optional)
    language TEXT DEFAULT 'en',              -- User's preferred language (en, bn, hi, ar)
    access_status TEXT DEFAULT 'pending',    -- Access status: pending, approved, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create access_requests table for managing user access requests
CREATE TABLE IF NOT EXISTS access_requests (
    id SERIAL PRIMARY KEY,                    -- Auto-increment ID
    user_id BIGINT NOT NULL,                  -- Telegram User ID
    username TEXT,                            -- Telegram Username
    first_name TEXT,                          -- User's first name
    language TEXT DEFAULT 'en',              -- User's preferred language
    request_message TEXT,                     -- Optional request message
    status TEXT DEFAULT 'pending',           -- Request status: pending, approved, rejected
    admin_response TEXT,                      -- Admin's response message (optional)
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,   -- When admin processed the request
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Last update timestamp
    expires_at TIMESTAMP WITH TIME ZONE,     -- Request expiration (3 hours from creation)
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Create admin_actions table for logging admin activities
CREATE TABLE IF NOT EXISTS admin_actions (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL,                 -- Admin's Telegram User ID
    action_type TEXT NOT NULL,                -- Action type: approve, reject, etc.
    target_user_id BIGINT NOT NULL,           -- Target user's Telegram ID
    details JSONB,                            -- Additional action details
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create bot_settings table for storing bot configuration
CREATE TABLE IF NOT EXISTS bot_settings (
    key TEXT PRIMARY KEY,                     -- Setting key
    value TEXT NOT NULL,                      -- Setting value
    description TEXT,                         -- Setting description
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Insert default bot settings
INSERT INTO bot_settings (key, value, description) VALUES
('admin_user_id', '7325836764', 'Primary admin user ID'),
('admin_username', '@tasktreasur_support', 'Primary admin username'),
('max_phone_numbers', '200', 'Maximum phone numbers per request'),
('request_cooldown_hours', '3', 'Hours between access requests'),
('bot_version', '2.0', 'Current bot version')
ON CONFLICT (key) DO NOTHING;

-- 6. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_access_status ON users(access_status);
CREATE INDEX IF NOT EXISTS idx_access_requests_user_id ON access_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_access_requests_status ON access_requests(status);
CREATE INDEX IF NOT EXISTS idx_access_requests_expires_at ON access_requests(expires_at);
CREATE INDEX IF NOT EXISTS idx_admin_actions_admin_id ON admin_actions(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_actions_target_user_id ON admin_actions(target_user_id);

-- 7. Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 8. Create triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bot_settings_updated_at 
    BEFORE UPDATE ON bot_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 9. Create function to cleanup expired requests (run this periodically)
CREATE OR REPLACE FUNCTION cleanup_expired_requests()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM access_requests 
    WHERE status = 'pending' 
    AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 10. Create function to get user access status
CREATE OR REPLACE FUNCTION get_user_access_status(user_telegram_id BIGINT)
RETURNS TEXT AS $$
DECLARE
    user_status TEXT;
BEGIN
    SELECT access_status INTO user_status 
    FROM users 
    WHERE id = user_telegram_id;
    
    IF user_status IS NULL THEN
        RETURN 'new_user';
    ELSE
        RETURN user_status;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 11. Create function to check request cooldown
CREATE OR REPLACE FUNCTION check_request_cooldown(user_telegram_id BIGINT)
RETURNS BOOLEAN AS $$
DECLARE
    last_request_time TIMESTAMP WITH TIME ZONE;
    cooldown_hours INTEGER;
BEGIN
    -- Get cooldown setting
    SELECT value::INTEGER INTO cooldown_hours 
    FROM bot_settings 
    WHERE key = 'request_cooldown_hours';
    
    IF cooldown_hours IS NULL THEN
        cooldown_hours := 3; -- Default 3 hours
    END IF;
    
    -- Get last request time
    SELECT MAX(requested_at) INTO last_request_time
    FROM access_requests 
    WHERE user_id = user_telegram_id;
    
    -- Check if enough time has passed
    IF last_request_time IS NULL THEN
        RETURN TRUE; -- No previous request
    ELSE
        RETURN (NOW() - last_request_time) > (cooldown_hours || ' hours')::INTERVAL;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 12. Enable Row Level Security (optional, for better security)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE access_requests ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE admin_actions ENABLE ROW LEVEL SECURITY;

-- 13. Create view for admin dashboard (optional)
CREATE OR REPLACE VIEW admin_dashboard AS
SELECT 
    u.id as user_id,
    u.username,
    u.first_name,
    u.language,
    u.access_status,
    u.created_at as user_joined,
    ar.id as request_id,
    ar.status as request_status,
    ar.requested_at,
    ar.expires_at,
    CASE 
        WHEN ar.expires_at < NOW() AND ar.status = 'pending' THEN 'expired'
        ELSE ar.status 
    END as effective_status
FROM users u
LEFT JOIN access_requests ar ON u.id = ar.user_id
ORDER BY ar.requested_at DESC NULLS LAST;

-- Success message
SELECT 'Database setup completed successfully! All tables and functions created.' as result;
