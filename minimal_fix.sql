-- MINIMAL FIX: Add missing columns to access_requests table
-- Run these commands in Supabase SQL Editor

-- Add language column
ALTER TABLE access_requests 
ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'en';

-- Add updated_at column  
ALTER TABLE access_requests 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
