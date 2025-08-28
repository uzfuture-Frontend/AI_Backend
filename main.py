from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import mysql.connector
from datetime import datetime
import os
import uuid
import json
import asyncio

# OpenAI API key setup
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# AI assistants import
from ai.chat_ai import ChatAI
from ai.tarjimon_ai import TarjimonAI
from ai.blockchain_ai import BlockchainAI
from ai.tadqiqot_ai import TadqiqotAI
from ai.smart_energy_ai import SmartEnergyAI
from ai.dasturlash_ai import DasturlashAI
from ai.tibbiy_ai import TibbiyAI
from ai.talim_ai import TalimAI
from ai.biznes_ai import BiznesAI
from ai.huquq_ai import HuquqAI
from ai.psixologik_ai import PsixologikAI
from ai.moliya_ai import MoliyaAI
from ai.sayohat_ai import SayohatAI
from ai.oshpazlik_ai import OshpazlikAI
from ai.ijod_ai import IjodAI
from ai.musiqa_ai import MusiqaAI
from ai.sport_ai import SportAI
from ai.ob_havo_ai import ObHavoAI
from ai.yangiliklar_ai import YangiliklarAI
from ai.matematik_ai import MatematikAI
from ai.fan_ai import FanAI
from ai.ovozli_ai import OvozliAI
from ai.arxitektura_ai import ArxitekturaAI
from ai.ekologiya_ai import EkologiyaAI
from ai.oyin_ai import OyinAI

# FastAPI app
app = FastAPI(title="AI Universe - 25 AI Platform", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173", 
        "http://172.22.224.1:5173",
        "http://192.168.56.1:5173",
        "http://10.5.49.167:5173",
        "https://aibackend-production-f601.up.railway.app",
        "https://www.aiuniverse.uz",
        "http://www.aiuniverse.uz",
        "https://aiuniverse.uz",
        "http://aiuniverse.uz"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# MySQL connection config
DB_CONFIG = {
    'host': 'turntable.proxy.rlwy.net',
    'port': 49805,
    'user': 'root',
    'password': 'XRCcOHObEeRtWRSJzlFzyWZNltFjgjKi',
    'database': 'railway'
}

# MySQL connection pool
def get_db_connection():
    """MySQL connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return None

# Database tables creation
def create_tables():
    """Create database tables if not exist"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                email VARCHAR(255) UNIQUE,
                name VARCHAR(255),
                picture VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255),
                ai_type VARCHAR(100),
                title VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id VARCHAR(255) PRIMARY KEY,
                conversation_id VARCHAR(255),
                user_id VARCHAR(255),
                content TEXT,
                ai_response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255),
                ai_type VARCHAR(100),
                usage_count INT DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user_ai (user_id, ai_type)
            )
        """)
        
        conn.commit()
        print("Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

# Initialize database
create_tables()

# AI assistants mapping
AI_ASSISTANTS = {
    "chat": ChatAI(),
    "tarjimon": TarjimonAI(),
    "blockchain": BlockchainAI(),
    "tadqiqot": TadqiqotAI(),
    "smart_energy": SmartEnergyAI(),
    "dasturlash": DasturlashAI(),
    "tibbiy": TibbiyAI(),
    "talim": TalimAI(),
    "biznes": BiznesAI(),
    "huquq": HuquqAI(),
    "psixologik": PsixologikAI(),
    "moliya": MoliyaAI(),
    "sayohat": SayohatAI(),
    "oshpazlik": OshpazlikAI(),
    "ijod": IjodAI(),
    "musiqa": MusiqaAI(),
    "sport": SportAI(),
    "obhavo": ObHavoAI(),
    "yangiliklar": YangiliklarAI(),
    "matematik": MatematikAI(),
    "fan": FanAI(),
    "ovozli": OvozliAI(),
    "arxitektura": ArxitekturaAI(),
    "ekologiya": EkologiyaAI(),
    "oyun": OyinAI()
}

# AI ID to type mapping
AI_ID_MAPPING = {
    1: 'chat', 2: 'tarjimon', 3: 'blockchain', 4: 'tadqiqot', 5: 'smart_energy',
    6: 'dasturlash', 7: 'tibbiy', 8: 'talim', 9: 'biznes', 10: 'huquq',
    11: 'psixologik', 12: 'moliya', 13: 'sayohat', 14: 'oshpazlik', 15: 'ijod',
    16: 'musiqa', 17: 'sport', 18: 'obhavo', 19: 'yangiliklar', 20: 'matematik',
    21: 'fan', 22: 'ovozli', 23: 'arxitektura', 24: 'ekologiya', 25: 'oyun'
}

# Process AI chat
async def process_ai_chat(ai_type: str, message: str, user_id: str, conversation_id: str = None):
    """Process AI chat with MySQL"""
    try:
        # Get AI assistant
        ai_assistant = AI_ASSISTANTS.get(ai_type)
        if not ai_assistant:
            return f"error|invalid_ai_type|AI type '{ai_type}' not found"
        
        print(f"Processing {ai_type} AI for user {user_id}")
        
        # Get AI response with timeout
        try:
            ai_response = await asyncio.wait_for(
                ai_assistant.get_response(message), 
                timeout=30.0
            )
        except asyncio.TimeoutError:
            ai_response = f"Kechirasiz, {ai_type} AI javobi uchun vaqt tugadi."
        except Exception as e:
            ai_response = f"Kechirasiz, {ai_type} AI da xatolik: {str(e)}"
        
        if not ai_response:
            ai_response = "Kechirasiz, javob olishda xatolik yuz berdi."
        
        # Save to database
        conn = get_db_connection()
        if not conn:
            return f"success|{ai_response}|temp_id"
        
        try:
            cursor = conn.cursor()
            
            # Create conversation if needed
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                title = message[:50] + "..." if len(message) > 50 else message
                
                cursor.execute("""
                    INSERT INTO conversations (id, user_id, ai_type, title) 
                    VALUES (%s, %s, %s, %s)
                """, (conversation_id, user_id, ai_type, title))
                print(f"New conversation created: {conversation_id}")
            
            # Save message
            message_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO messages (id, conversation_id, user_id, content, ai_response) 
                VALUES (%s, %s, %s, %s, %s)
            """, (message_id, conversation_id, user_id, message, ai_response))
            
            # Update stats
            cursor.execute("""
                INSERT INTO user_stats (id, user_id, ai_type, usage_count, last_used) 
                VALUES (%s, %s, %s, 1, NOW()) 
                ON DUPLICATE KEY UPDATE 
                usage_count = usage_count + 1, 
                last_used = NOW()
            """, (str(uuid.uuid4()), user_id, ai_type))
            
            # Update conversation timestamp
            cursor.execute("""
                UPDATE conversations SET updated_at = NOW() WHERE id = %s
            """, (conversation_id,))
            
            conn.commit()
            print(f"AI response saved: {len(ai_response)} chars")
            
            return f"success|{ai_response}|{conversation_id}"
            
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            conn.rollback()
            return f"success|{ai_response}|temp_id"
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"AI processing error: {str(e)}")
        return f"error|processing_failed|{str(e)}"

# MAIN ENDPOINTS

@app.get("/")
async def root():
    return PlainTextResponse("success|AI Universe|25 AI Platform Running")

@app.get("/api/health")
async def health_check():
    conn = get_db_connection()
    if conn:
        conn.close()
        return PlainTextResponse("success|healthy|Server and Database OK")
    return PlainTextResponse("error|db_error|Database connection failed", status_code=500)

# AI Chat by ID - MAIN ENDPOINT
@app.post("/api/ai/{ai_id}")
async def chat_by_ai_id(ai_id: int, request: Request):
    """Main AI chat endpoint"""
    try:
        body = await request.json()
        message = body.get("message", "")
        user_id = str(body.get("user_id", ""))
        conversation_id = body.get("conversation_id")
        
        if not message or not user_id or user_id == "undefined":
            return PlainTextResponse("error|missing_data|Message and user_id required", status_code=400)
        
        # Convert AI ID to type
        ai_type = AI_ID_MAPPING.get(ai_id)
        if not ai_type:
            return PlainTextResponse(f"error|invalid_ai_id|AI ID {ai_id} not found", status_code=404)
        
        print(f"AI Chat Request: ID={ai_id}, Type={ai_type}, User={user_id}")
        
        # Process AI chat
        result = await process_ai_chat(ai_type, message, user_id, conversation_id)
        
        if result.startswith("error"):
            return PlainTextResponse(result, status_code=500)
        
        return PlainTextResponse(result)
        
    except Exception as e:
        print(f"AI chat error: {str(e)}")
        return PlainTextResponse(f"error|chat_failed|{str(e)}", status_code=500)

# Get user chats
@app.get("/api/chats/user/{user_id}")
async def get_user_chats(user_id: int):
    """Get all user conversations"""
    try:
        conn = get_db_connection()
        if not conn:
            return PlainTextResponse("error|db_error|Database connection failed", status_code=500)
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, ai_type, title, created_at, updated_at 
            FROM conversations 
            WHERE user_id = %s 
            ORDER BY updated_at DESC
        """, (str(user_id),))
        
        conversations = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not conversations:
            return PlainTextResponse("success|no_chats|No chats found")
        
        # Format conversations
        chat_data = []
        for conv in conversations:
            chat_data.append(f"{conv[0]}|{conv[1]}|{conv[2]}|{conv[3]}|{conv[4]}")
        
        result = "\n".join(chat_data)
        return PlainTextResponse(f"success|{result}|Chats retrieved")
        
    except Exception as e:
        print(f"Get chats error: {str(e)}")
        return PlainTextResponse(f"error|get_chats_failed|{str(e)}", status_code=500)

# Get user stats
@app.get("/api/stats/user/{user_id}")
async def get_user_stats(user_id: int):
    """Get user statistics"""
    try:
        conn = get_db_connection()
        if not conn:
            return PlainTextResponse("error|db_error|Database connection failed", status_code=500)
        
        cursor = conn.cursor()
        
        # Get total messages
        cursor.execute("""
            SELECT SUM(usage_count) FROM user_stats WHERE user_id = %s
        """, (str(user_id),))
        total_messages = cursor.fetchone()[0] or 0
        
        # Get total conversations
        cursor.execute("""
            SELECT COUNT(*) FROM conversations WHERE user_id = %s
        """, (str(user_id),))
        total_conversations = cursor.fetchone()[0] or 0
        
        # Get AI usage stats
        cursor.execute("""
            SELECT ai_type, usage_count, last_used 
            FROM user_stats 
            WHERE user_id = %s 
            ORDER BY usage_count DESC
        """, (str(user_id),))
        
        stats = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not stats:
            return PlainTextResponse("success|no_stats|No statistics available")
        
        # Format stats
        most_used_ai = stats[0][0] if stats else "None"
        
        stats_data = [
            f"TOTAL_MESSAGES:{total_messages}",
            f"TOTAL_CONVERSATIONS:{total_conversations}",
            f"MOST_USED_AI:{most_used_ai}"
        ]
        
        for stat in stats:
            stats_data.append(f"AI_STAT:{stat[0]}|{stat[1]}|{stat[2]}")
        
        result = "\n".join(stats_data)
        return PlainTextResponse(f"success|{result}|Stats retrieved")
        
    except Exception as e:
        print(f"Get stats error: {str(e)}")
        return PlainTextResponse(f"error|stats_failed|{str(e)}", status_code=500)

# Create new chat
@app.post("/api/chats")
async def create_chat(request: Request):
    """Create new chat"""
    try:
        body = await request.json()
        title = body.get("title", "New Chat")
        user_id = str(body.get("user_id", ""))
        ai_type = body.get("ai_type", "chat")
        
        if not user_id or user_id == "undefined":
            return PlainTextResponse("error|missing_user_id|User ID required", status_code=400)
        
        conn = get_db_connection()
        if not conn:
            return PlainTextResponse("error|db_error|Database connection failed", status_code=500)
        
        chat_id = str(uuid.uuid4())
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (id, user_id, ai_type, title) 
            VALUES (%s, %s, %s, %s)
        """, (chat_id, user_id, ai_type, title))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"New chat created: {chat_id}")
        return PlainTextResponse(f"success|{chat_id}|Chat created")
        
    except Exception as e:
        print(f"Create chat error: {str(e)}")
        return PlainTextResponse(f"error|create_failed|{str(e)}", status_code=500)

# Update chat
@app.put("/api/chats/{chat_id}")
async def update_chat(chat_id: str, request: Request):
    """Update chat"""
    try:
        body = await request.json()
        title = body.get("title", "New Chat")
        user_id = str(body.get("user_id", ""))
        ai_type = body.get("ai_type", "chat")
        
        if not user_id or user_id == "undefined":
            return PlainTextResponse("error|missing_user_id|User ID required", status_code=400)
        
        conn = get_db_connection()
        if not conn:
            return PlainTextResponse("error|db_error|Database connection failed", status_code=500)
        
        cursor = conn.cursor()
        
        # Check if conversation exists
        cursor.execute("SELECT id FROM conversations WHERE id = %s", (chat_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing conversation
            cursor.execute("""
                UPDATE conversations 
                SET title = %s, updated_at = NOW() 
                WHERE id = %s AND user_id = %s
            """, (title, chat_id, user_id))
        else:
            # Create new conversation
            cursor.execute("""
                INSERT INTO conversations (id, user_id, ai_type, title) 
                VALUES (%s, %s, %s, %s)
            """, (chat_id, user_id, ai_type, title))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Chat updated/created: {chat_id}")
        return PlainTextResponse("success|chat_updated|Chat updated successfully")
        
    except Exception as e:
        print(f"Update chat error: {str(e)}")
        return PlainTextResponse(f"error|update_failed|{str(e)}", status_code=500)

# Delete chat
@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str, request: Request):
    """Delete chat"""
    try:
        user_id = request.query_params.get("user_id")
        
        conn = get_db_connection()
        if not conn:
            return PlainTextResponse("error|db_error|Database connection failed", status_code=500)
        
        cursor = conn.cursor()
        
        # Delete messages first
        cursor.execute("DELETE FROM messages WHERE conversation_id = %s", (chat_id,))
        
        # Delete conversation
        if user_id:
            cursor.execute("""
                DELETE FROM conversations 
                WHERE id = %s AND user_id = %s
            """, (chat_id, user_id))
        else:
            cursor.execute("DELETE FROM conversations WHERE id = %s", (chat_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return PlainTextResponse("success|chat_deleted|Chat deleted")
        
    except Exception as e:
        print(f"Delete chat error: {str(e)}")
        return PlainTextResponse(f"error|delete_failed|{str(e)}", status_code=500)

# Google Auth
@app.post("/api/auth/google")
async def google_auth(request: Request):
    """Google authentication"""
    try:
        body = await request.json()
        email = body.get("email")
        name = body.get("name")
        picture = body.get("picture", "")
        
        if not email or not name:
            return PlainTextResponse("error|missing_data|Email and name required", status_code=400)
        
        conn = get_db_connection()
        if not conn:
            return PlainTextResponse("error|db_error|Database connection failed", status_code=500)
        
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, name, picture FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            # Update existing user
            user_id = user[0]
            cursor.execute("""
                UPDATE users SET name = %s, picture = %s WHERE email = %s
            """, (name, picture, email))
        else:
            # Create new user
            user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, email, name, picture) 
                VALUES (%s, %s, %s, %s)
            """, (user_id, email, name, picture))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        user_info = {
            "id": user_id,
            "email": email,
            "name": name,
            "picture": picture
        }
        
        return PlainTextResponse(f"success|{json.dumps(user_info)}|User authenticated")
        
    except Exception as e:
        print(f"Auth error: {str(e)}")
        return PlainTextResponse(f"error|auth_failed|{str(e)}", status_code=500)

# OPTIONS handlers for CORS
@app.options("/api/ai/{ai_id}")
async def options_ai():
    return PlainTextResponse("", status_code=200)

@app.options("/api/chats/user/{user_id}")
async def options_chats():
    return PlainTextResponse("", status_code=200)

@app.options("/api/stats/user/{user_id}")
async def options_stats():
    return PlainTextResponse("", status_code=200)

@app.options("/api/chats")
async def options_create_chat():
    return PlainTextResponse("", status_code=200)

@app.options("/api/chats/{chat_id}")
async def options_update_chat():
    return PlainTextResponse("", status_code=200)

@app.options("/api/auth/google")
async def options_auth():
    return PlainTextResponse("", status_code=200)

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)