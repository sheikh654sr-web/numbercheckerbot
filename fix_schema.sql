-- Fix access_requests table schema
-- Run this in Supabase SQL Editor to add missing language column

-- Add language column to access_requests table
ALTER TABLE access_requests 
ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'en';

-- Update the column comment
COMMENT ON COLUMN access_requests.language IS 'User preferred language (en, bn, hi, ar)';

-- Verify the fix
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'access_requests' 
ORDER BY ordinal_position;
