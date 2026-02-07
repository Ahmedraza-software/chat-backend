from supabase import create_client, Client
import sys

SUPABASE_URL = "https://betfplgezeciguwvglgg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJldGZwbGdlemVjaWd1d3ZnbGdnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA0NzIwMDUsImV4cCI6MjA4NjA0ODAwNX0.jzDUdCVmXdGFYiWvzc17MwZMsC6MIY42K9CizB9mjP8"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL to create tables
sql_queries = [
    """
    CREATE TABLE IF NOT EXISTS users (
      id BIGSERIAL PRIMARY KEY,
      username TEXT NOT NULL,
      email TEXT NOT NULL,
      password TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS friend_requests (
      id BIGSERIAL PRIMARY KEY,
      sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      receiver_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      status TEXT DEFAULT 'pending',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(sender_id, receiver_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
      id BIGSERIAL PRIMARY KEY,
      sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      receiver_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      content TEXT NOT NULL,
      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      is_read INTEGER DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_messages_sender_receiver ON messages(sender_id, receiver_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_friend_requests_status ON friend_requests(status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
    """
]

print("Creating tables in Supabase...")

try:
    # Test connection first
    response = supabase.table("users").select("count", count="exact").execute()
    print("✓ Connected to Supabase successfully!")
    print(f"  Current users count: {response.count}")
    
    # Check if tables exist by trying to query them
    try:
        supabase.table("users").select("*").limit(1).execute()
        print("✓ Users table already exists")
    except:
        print("✗ Users table doesn't exist yet")
    
    try:
        supabase.table("friend_requests").select("*").limit(1).execute()
        print("✓ Friend requests table already exists")
    except:
        print("✗ Friend requests table doesn't exist yet")
    
    try:
        supabase.table("messages").select("*").limit(1).execute()
        print("✓ Messages table already exists")
    except:
        print("✗ Messages table doesn't exist yet")
    
    print("\nNote: To create tables, please:")
    print("1. Go to https://app.supabase.com")
    print("2. Select your project")
    print("3. Click SQL Editor")
    print("4. Click New Query")
    print("5. Copy and paste the SQL from setup_supabase.sql")
    print("6. Click Run")
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)
