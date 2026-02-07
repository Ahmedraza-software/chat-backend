#!/usr/bin/env python3
"""
Initialize Supabase database tables.
Run this once to set up the database schema.
"""

import os
import sys

# Instructions for manual setup
print("""
╔════════════════════════════════════════════════════════════════╗
║           SUPABASE DATABASE SETUP INSTRUCTIONS                 ║
╚════════════════════════════════════════════════════════════════╝

To create the required tables, follow these steps:

1. Go to: https://app.supabase.com
2. Select your project: betfplgezeciguwvglgg
3. Click "SQL Editor" in the left sidebar
4. Click "New Query" button
5. Copy and paste the SQL below:

""")

sql = """
-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  username TEXT NOT NULL,
  email TEXT NOT NULL,
  password TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create friend_requests table
CREATE TABLE IF NOT EXISTS friend_requests (
  id BIGSERIAL PRIMARY KEY,
  sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  receiver_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(sender_id, receiver_id)
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
  id BIGSERIAL PRIMARY KEY,
  sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  receiver_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_read INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_messages_sender_receiver ON messages(sender_id, receiver_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_friend_requests_status ON friend_requests(status);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
"""

print(sql)

print("""
6. Click the "Run" button
7. Wait for the query to complete
8. You should see "Success" message

Once the tables are created, you can start the backend:
    python main.py

The app will then connect to Supabase!
""")
