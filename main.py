from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List
import json
import hashlib
from supabase import create_client, Client

# Supabase setup
SUPABASE_URL = "https://betfplgezeciguwvglgg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJldGZwbGdlemVjaWd1d3ZnbGdnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA0NzIwMDUsImV4cCI6MjA4NjA0ODAwNX0.jzDUdCVmXdGFYiWvzc17MwZMsC6MIY42K9CizB9mjP8"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize Supabase tables if they don't exist"""
    try:
        # Tables will be created via Supabase dashboard or migrations
        # This is just a placeholder for initialization logic
        pass
    except Exception as e:
        print(f"Database initialization error: {e}")

init_db()

# Models
class User(BaseModel):
    id: int = None
    username: str
    email: str

class Message(BaseModel):
    id: int = None
    sender_id: int
    receiver_id: int
    content: str
    timestamp: str = None
    is_read: int = 0

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class FriendRequest(BaseModel):
    id: int = None
    sender_id: int
    receiver_id: int
    status: str = 'pending'
    created_at: str = None
    sender_username: str = None
    sender_email: str = None

class FriendRequestCreate(BaseModel):
    receiver_id: int

class FriendRequestAction(BaseModel):
    request_id: int
    action: str

# FastAPI app
app = FastAPI(title="Chat App API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    async def send_personal_message(self, user_id: int, message: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

# REST endpoints
@app.post("/users/register", response_model=User)
def register_user(user: UserCreate):
    try:
        hashed_password = hash_password(user.password)
        response = supabase.table("users").insert({
            "username": user.username,
            "email": user.email,
            "password": hashed_password
        }).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/users/login", response_model=User)
def login_user(user: UserLogin):
    try:
        hashed_password = hash_password(user.password)
        response = supabase.table("users").select("*").eq("username", user.username).eq("password", hashed_password).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.get("/users", response_model=List[User])
def get_users():
    try:
        response = supabase.table("users").select("id, username, email").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    try:
        response = supabase.table("users").select("id, username, email").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")

@app.get("/messages/{user_id}/{other_user_id}", response_model=List[Message])
def get_messages(user_id: int, other_user_id: int):
    try:
        response = supabase.table("messages").select("*").or_(
            f"and(sender_id.eq.{user_id},receiver_id.eq.{other_user_id}),and(sender_id.eq.{other_user_id},receiver_id.eq.{user_id})"
        ).order("timestamp", desc=False).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/messages", response_model=Message)
def create_message(message: MessageCreate):
    try:
        iso_timestamp = datetime.utcnow().isoformat()
        response = supabase.table("messages").insert({
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "timestamp": iso_timestamp,
            "is_read": 0
        }).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=400, detail="Failed to create message")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Friend Request endpoints
@app.post("/friend-requests/{receiver_id}")
def send_friend_request(receiver_id: int, sender_id: int):
    try:
        response = supabase.table("friend_requests").insert({
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "status": "pending"
        }).execute()
        
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=400, detail="Friend request already exists")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Friend request already exists")

@app.get("/friend-requests/pending/{user_id}", response_model=List[FriendRequest])
def get_pending_requests(user_id: int):
    try:
        response = supabase.table("friend_requests").select(
            "id, sender_id, receiver_id, status, created_at, users!sender_id(username, email)"
        ).or_(f"receiver_id.eq.{user_id},sender_id.eq.{user_id}").eq("status", "pending").order("created_at", desc=True).execute()
        
        result = []
        for req in response.data:
            result.append({
                "id": req["id"],
                "sender_id": req["sender_id"],
                "receiver_id": req["receiver_id"],
                "status": req["status"],
                "created_at": req["created_at"],
                "sender_username": req["users"]["username"] if req["users"] else None,
                "sender_email": req["users"]["email"] if req["users"] else None
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/friends/{user_id}")
def get_friends(user_id: int):
    try:
        # Get all accepted friend requests where user is receiver
        response1 = supabase.table("friend_requests").select(
            "sender_id, receiver_id"
        ).eq("receiver_id", user_id).eq("status", "accepted").execute()
        
        # Get all accepted friend requests where user is sender
        response2 = supabase.table("friend_requests").select(
            "sender_id, receiver_id"
        ).eq("sender_id", user_id).eq("status", "accepted").execute()
        
        friend_ids = set()
        
        # Add sender_ids from requests where user is receiver
        for req in response1.data:
            friend_ids.add(req["sender_id"])
        
        # Add receiver_ids from requests where user is sender
        for req in response2.data:
            friend_ids.add(req["receiver_id"])
        
        # Get user details for all friends
        friends = []
        for friend_id in friend_ids:
            user_response = supabase.table("users").select("id, username, email").eq("id", friend_id).execute()
            if user_response.data:
                friends.append(user_response.data[0])
        
        return friends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/friend-requests/{request_id}/accept")
def accept_friend_request(request_id: int):
    try:
        response = supabase.table("friend_requests").update({"status": "accepted"}).eq("id", request_id).execute()
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=400, detail="Failed to accept request")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/friend-requests/{request_id}/reject")
def reject_friend_request(request_id: int):
    try:
        response = supabase.table("friend_requests").update({"status": "rejected"}).eq("id", request_id).execute()
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=400, detail="Failed to reject request")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/messages/{message_id}/read")
def mark_message_read(message_id: int):
    try:
        response = supabase.table("messages").update({"is_read": 1}).eq("id", message_id).execute()
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=400, detail="Failed to mark message as read")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(user_id: int, websocket: WebSocket):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Save message to database with ISO timestamp
            iso_timestamp = datetime.utcnow().isoformat()
            try:
                supabase.table("messages").insert({
                    "sender_id": message_data["sender_id"],
                    "receiver_id": message_data["receiver_id"],
                    "content": message_data["content"],
                    "timestamp": iso_timestamp,
                    "is_read": 0
                }).execute()
            except Exception as e:
                print(f"Error saving message: {e}")
            
            # Send to receiver if connected
            await manager.send_personal_message(
                message_data["receiver_id"],
                json.dumps({
                    "sender_id": message_data["sender_id"],
                    "content": message_data["content"],
                    "timestamp": iso_timestamp
                })
            )
    except Exception as e:
        manager.disconnect(user_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
