from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.pool
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid
import structlog
from openai import OpenAI
import jwt
import json
import threading
from contextlib import contextmanager

# Load environment variables
load_dotenv()

print("🔍 DEBUGGING ENVIRONMENT VARIABLES:")
print(f"All env vars count: {len(os.environ)}")

# OPENAI variables tekshirish
openai_vars = {k: v for k, v in os.environ.items() if 'OPENAI' in k}
print(f"OPENAI related vars: {openai_vars}")

# Direct check
api_key = os.getenv("OPENAI_API_KEY")
print(f"OPENAI_API_KEY direct: {'✅ Found' if api_key else '❌ Not found'}")
if api_key:
    print(f"Length: {len(api_key)}")
    print(f"Starts with: {api_key[:10]}...")

# Try OpenAI client
try:
    if api_key:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client created successfully")
    else:
        print("❌ No API key found for OpenAI client")
        client = None
except Exception as e:
    print(f"❌ OpenAI client error: {e}")
    client = None

# Logger
logger = structlog.get_logger()

# Database connection pool
db_pool = None

def init_database():
    """PostgreSQL connection pool yaratish"""
    global db_pool
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL or "postgresql" not in DATABASE_URL:
        print("❌ PostgreSQL DATABASE_URL topilmadi")
        return False
    
    try:
        # URL ni parse qilish
        if DATABASE_URL.startswith("postgresql://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "", 1)
        elif DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "", 1)
        
        # URL formatini bo'lish: user:password@host:port/database
        auth_host_db = DATABASE_URL
        
        if '@' in auth_host_db:
            auth, host_db = auth_host_db.split('@', 1)
            if ':' in auth:
                user, password = auth.split(':', 1)
            else:
                user, password = auth, ""
        else:
            print("❌ DATABASE_URL formatida xatolik")
            return False
        
        if '/' in host_db:
            host_port, database = host_db.split('/', 1)
            # Query parametrlarini olib tashlash
            if '?' in database:
                database = database.split('?')[0]
        else:
            print("❌ DATABASE_URL da database nomi yo'q")
            return False
        
        if ':' in host_port:
            host, port = host_port.split(':', 1)
            port = int(port)
        else:
            host, port = host_port, 5432
        
        # Connection pool yaratish
        db_pool = psycopg2.pool.ThreadedConnectionPool(
            1, 20,  # min va max connections
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode="require"
        )
        
        print(f"✅ PostgreSQL pool yaratildi: {host}:{port}/{database}")
        
        # Test connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                print(f"✅ PostgreSQL version: {version[:50]}...")
        
        # Create tables
        create_tables()
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection error: {e}")
        return False

@contextmanager
def get_db_connection():
    """Database connection olish"""
    if not db_pool:
        raise Exception("Database pool mavjud emas")
    
    conn = None
    try:
        conn = db_pool.getconn()
        conn.autocommit = False
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            db_pool.putconn(conn)

def create_tables():
    """Database jadvallarini yaratish"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Users table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(255) PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        name VARCHAR(255),
                        picture VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Conversations table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255),
                        ai_type VARCHAR(100),
                        title VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Messages table
                cur.execute("""
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
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_stats (
                        id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255),
                        ai_type VARCHAR(100),
                        usage_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Indexlar qo'shish
                cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_user_stats_user_id ON user_stats(user_id)")
                
                conn.commit()
                print("✅ Database jadvallari muvaffaqiyatli yaratildi")
                
    except Exception as e:
        print(f"❌ Jadval yaratishda xato: {str(e)}")

# Database ni initialize qilish
db_initialized = init_database()

# FastAPI app
app = FastAPI(
    title="AI Universe - Professional AI Platform",
    description="25 ta professional AI xizmati bir platformada",
    version="1.0.0"
)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://www.aiuniverse.uz",
    "https://www.aiuniverse.uz",
    "http://aiuniverse.uz", 
    "https://aiuniverse.uz",
    "https://ai-backend-fy7t.onrender.com",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# AI Assistant base class
class DummyAI:
    def __init__(self, ai_type="dummy"):
        self.ai_type = ai_type
        self.client = client if client else None
    
    async def get_response(self, message: str) -> str:
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"Sen {self.ai_type} bo'yicha professional AI yordamchisisiz. O'zbek tilida javob ber."},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI API xatosi: {str(e)}")
                return f"Sizning xabaringiz: '{message}' qabul qilindi. {self.ai_type.title()} AI hozircha ishlamayapti, lekin tez orada faollashadi!"
        else:
            return f"Sizning xabaringiz: '{message}' qabul qilindi. {self.ai_type.title()} AI hozircha ishlamayapti, lekin tez orada faollashadi!"

AI_ASSISTANTS = {}

# AI modules loading
ai_modules = [
    ("chat", "ai.chat_ai", "ChatAI"),
    ("tarjimon", "ai.tarjimon_ai", "TarjimonAI"),
    ("blockchain", "ai.blockchain_ai", "BlockchainAI"),
    ("tadqiqot", "ai.tadqiqot_ai", "TadqiqotAI"),
    ("smart_energy", "ai.smart_energy_ai", "SmartEnergyAI"),
    ("dasturlash", "ai.dasturlash_ai", "DasturlashAI"),
    ("tibbiy", "ai.tibbiy_ai", "TibbiyAI"),
    ("talim", "ai.talim_ai", "TalimAI"),
    ("biznes", "ai.biznes_ai", "BiznesAI"),
    ("huquq", "ai.huquq_ai", "HuquqAI"),
    ("psixologik", "ai.psixologik_ai", "PsixologikAI"),
    ("moliya", "ai.moliya_ai", "MoliyaAI"),
    ("sayohat", "ai.sayohat_ai", "SayohatAI"),
    ("oshpazlik", "ai.oshpazlik_ai", "OshpazlikAI"),
    ("ijod", "ai.ijod_ai", "IjodAI"),
    ("musiqa", "ai.musiqa_ai", "MusiqaAI"),
    ("sport", "ai.sport_ai", "SportAI"),
    ("obhavo", "ai.ob_havo_ai", "ObHavoAI"),
    ("yangiliklar", "ai.yangiliklar_ai", "YangiliklarAI"),
    ("matematik", "ai.matematik_ai", "MatematikAI"),
    ("fan", "ai.fan_ai", "FanAI"),
    ("ovozli", "ai.ovozli_ai", "OvozliAI"),
    ("arxitektura", "ai.arxitektura_ai", "ArxitekturaAI"),
    ("ekologiya", "ai.ekologiya_ai", "EkologiyaAI"),
    ("oyun", "ai.oyin_ai", "OyinAI")
]

for ai_key, module_path, class_name in ai_modules:
    try:
        module = __import__(module_path, fromlist=[class_name])
        ai_class = getattr(module, class_name)
        AI_ASSISTANTS[ai_key] = ai_class()
        print(f"✅ {ai_key} AI module loaded")
    except ImportError as e:
        print(f"⚠️ {ai_key} AI module not found, using dummy with OpenAI fallback")
        AI_ASSISTANTS[ai_key] = DummyAI(ai_key)
    except Exception as e:
        print(f"⚠️ {ai_key} AI module error: {str(e)}, using dummy with OpenAI fallback")
        AI_ASSISTANTS[ai_key] = DummyAI(ai_key)

print(f"Total AI assistants loaded: {len(AI_ASSISTANTS)}")

# Database helper functions
def create_user(email: str, name: str, picture: str = "") -> dict:
    """Yangi foydalanuvchi yaratish"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                user_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO users (id, email, name, picture, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                """, (user_id, email, name, picture, datetime.utcnow()))
                
                user = cur.fetchone()
                conn.commit()
                return dict(user)
    except Exception as e:
        print(f"Create user error: {e}")
        return None

def get_user_by_email(email: str) -> dict:
    """Email bo'yicha foydalanuvchi topish"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                return dict(user) if user else None
    except Exception as e:
        print(f"Get user error: {e}")
        return None

def update_user(email: str, name: str, picture: str = "") -> dict:
    """Foydalanuvchi ma'lumotlarini yangilash"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE users SET name = %s, picture = %s 
                    WHERE email = %s
                    RETURNING *
                """, (name, picture, email))
                
                user = cur.fetchone()
                conn.commit()
                return dict(user) if user else None
    except Exception as e:
        print(f"Update user error: {e}")
        return None

def create_conversation(user_id: str, ai_type: str, title: str) -> str:
    """Yangi suhbat yaratish"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                conversation_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO conversations (id, user_id, ai_type, title, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (conversation_id, user_id, ai_type, title, datetime.utcnow(), datetime.utcnow()))
                
                conn.commit()
                return conversation_id
    except Exception as e:
        print(f"Create conversation error: {e}")
        return None

def save_message(conversation_id: str, user_id: str, content: str, ai_response: str):
    """Xabar saqlash"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                message_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO messages (id, conversation_id, user_id, content, ai_response, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (message_id, conversation_id, user_id, content, ai_response, datetime.utcnow()))
                
                conn.commit()
    except Exception as e:
        print(f"Save message error: {e}")

def update_user_stats(user_id: str, ai_type: str):
    """Foydalanuvchi statistikasini yangilash"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Mavjud statistika bormi tekshirish
                cur.execute("""
                    SELECT id, usage_count FROM user_stats 
                    WHERE user_id = %s AND ai_type = %s
                """, (user_id, ai_type))
                
                stat = cur.fetchone()
                
                if stat:
                    # Mavjud statistikani yangilash
                    cur.execute("""
                        UPDATE user_stats 
                        SET usage_count = usage_count + 1, last_used = %s
                        WHERE user_id = %s AND ai_type = %s
                    """, (datetime.utcnow(), user_id, ai_type))
                else:
                    # Yangi statistika yaratish
                    stat_id = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO user_stats (id, user_id, ai_type, usage_count, last_used)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (stat_id, user_id, ai_type, 1, datetime.utcnow()))
                
                conn.commit()
    except Exception as e:
        print(f"Update stats error: {e}")

def update_conversation_timestamp(conversation_id: str):
    """Suhbat vaqtini yangilash"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE conversations SET updated_at = %s WHERE id = %s
                """, (datetime.utcnow(), conversation_id))
                conn.commit()
    except Exception as e:
        print(f"Update conversation error: {e}")

# Dependency for database check
def get_db():
    """Database mavjudligini tekshirish"""
    if not db_initialized:
        raise HTTPException(status_code=500, detail="Database not available")
    return True

# Root endpoints
@app.get("/")
async def root():
    return PlainTextResponse("success|AI Universe|Welcome to AI Universe Platform")

@app.post("/")
async def root_post():
    return PlainTextResponse("success|AI Universe|Welcome to AI Universe Platform")

@app.head("/")
async def root_head():
    return PlainTextResponse("success|AI Universe|Welcome to AI Universe Platform")

@app.get("/api")
async def api_root():
    return PlainTextResponse("success|AI Universe API|Welcome to AI Universe API")

@app.get("/health")
async def health_check():
    return PlainTextResponse("success|healthy|Server is running")

@app.get("/api/health")
async def api_health_check():
    return PlainTextResponse("success|healthy|Server is running")

# Google Auth endpoint
@app.post("/api/auth/google") 
async def google_auth(request: Request):
    try:
        body = await request.json()
        
        # Ikkala formatni qo'llab-quvvatlash
        if 'token' in body:
            try:
                payload = jwt.decode(body['token'], options={"verify_signature": False})
                email = payload.get('email')
                name = payload.get('name')
                picture = payload.get('picture', '')
                google_id = payload.get('sub')
            except Exception as e:
                logger.error(f"JWT decode error: {str(e)}")
                return PlainTextResponse("error|invalid_token|Invalid JWT token", status_code=400)
        
        elif 'user_data' in body:
            user_data = body['user_data']
            email = user_data.get('email')
            name = user_data.get('name') 
            picture = user_data.get('picture', '')
            google_id = user_data.get('google_id')
        
        else:
            email = body.get("email")
            name = body.get("name")
            picture = body.get("picture", "")
            google_id = body.get("google_id") or body.get("sub")
        
        if not email or not name:
            return PlainTextResponse("error|missing_data|Email and name are required", status_code=400)
        
        if not db_initialized:
            # Database yo'q bo'lsa dummy response
            user_info = {
                "id": str(uuid.uuid4()),
                "email": email,
                "name": name,
                "picture": picture,
                "google_id": google_id
            }
            return PlainTextResponse(f"success|{json.dumps(user_info)}|User authenticated successfully")
        
        # Database bilan ishlash
        try:
            user = get_user_by_email(email)
            
            if not user:
                user = create_user(email, name, picture)
                logger.info(f"New user created: {email}")
            else:
                user = update_user(email, name, picture)
                logger.info(f"Existing user updated: {email}")
                
            if not user:
                return PlainTextResponse("error|database_error|Failed to create/update user", status_code=500)
        
        except Exception as db_error:
            logger.error(f"Database error in auth: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Database operation failed", status_code=500)
        
        user_info = {
            "id": str(user['id']),
            "email": email,
            "name": name,
            "picture": picture,
            "google_id": google_id
        }
        
        return PlainTextResponse(f"success|{json.dumps(user_info)}|User authenticated successfully")
        
    except json.JSONDecodeError:
        return PlainTextResponse("error|invalid_json|Invalid JSON data", status_code=400)
    except Exception as e:
        logger.error("Google auth failed", error=str(e))
        return PlainTextResponse(f"error|auth_failed|{str(e)}", status_code=500)

# Chat processing function
async def process_chat(ai_assistant, message: str, user_id: str, conversation_id: str | None, ai_type: str):
    try:
        if not user_id:
            return PlainTextResponse("error|missing_user_id|User ID is required", status_code=400)
        if not message:
            return PlainTextResponse("error|missing_message|Message is required", status_code=400)
        
        ai_response = await ai_assistant.get_response(message)
        
        if db_initialized:
            try:
                # Yangi suhbat yaratish
                if not conversation_id:
                    title = message[:50] + "..." if len(message) > 50 else message
                    conversation_id = create_conversation(user_id, ai_type, title)
                
                # Xabar saqlash
                if conversation_id:
                    save_message(conversation_id, user_id, message, ai_response)
                    update_user_stats(user_id, ai_type)
                    update_conversation_timestamp(conversation_id)
                
            except Exception as db_error:
                logger.error(f"Database error in chat: {str(db_error)}")
                # Database xatosi bo'lsa ham AI javobini qaytarish
                pass
        
        return PlainTextResponse(f"success|{ai_response}|{conversation_id or 'temp'}")
    except Exception as e:
        logger.error(f"Chat failed for {ai_type}", error=str(e))
        return PlainTextResponse(f"error|chat_failed|{str(e)}", status_code=500)

async def handle_chat_request(request: Request, ai_type: str):
    try:
        body = await request.json()
        message = body.get("message")
        user_id = body.get("user_id")
        conversation_id = body.get("conversation_id")
        
        print(f"Chat request: ai_type={ai_type}, message={message[:50] if message else 'None'}..., user_id={user_id}")
        
        if not AI_ASSISTANTS.get(ai_type):
            return PlainTextResponse(f"error|invalid_ai_type|AI type '{ai_type}' not found", status_code=404)
        
        return await process_chat(AI_ASSISTANTS[ai_type], message, user_id, conversation_id, ai_type)
    except json.JSONDecodeError:
        return PlainTextResponse("error|invalid_json|Invalid JSON data", status_code=400)
    except Exception as e:
        logger.error(f"Handle chat request failed for {ai_type}", error=str(e))
        return PlainTextResponse(f"error|request_failed|{str(e)}", status_code=500)

# AI ID ga asosan routing
@app.post("/api/ai/{ai_id}")
async def api_chat_by_id(ai_id: int, request: Request):
    try:
        ai_type_mapping = {
            1: 'chat', 2: 'tarjimon', 3: 'blockchain', 4: 'tadqiqot', 5: 'smart_energy',
            6: 'dasturlash', 7: 'tibbiy', 8: 'talim', 9: 'biznes', 10: 'huquq',
            11: 'psixologik', 12: 'moliya', 13: 'sayohat', 14: 'oshpazlik', 15: 'ijod',
            16: 'musiqa', 17: 'sport', 18: 'obhavo', 19: 'yangiliklar', 20: 'matematik',
            21: 'fan', 22: 'ovozli', 23: 'arxitektura', 24: 'ekologiya', 25: 'oyun'
        }
        
        ai_type = ai_type_mapping.get(ai_id)
        if not ai_type:
            return PlainTextResponse(f"error|invalid_ai_id|AI ID '{ai_id}' not found", status_code=404)
        
        print(f"Converting AI ID {ai_id} to type '{ai_type}'")
        
        return await handle_chat_request(request, ai_type)
    except Exception as e:
        logger.error(f"API chat by ID failed for {ai_id}", error=str(e))
        return PlainTextResponse(f"error|api_chat_failed|{str(e)}", status_code=500)

# Chat endpoints
chat_endpoints = [
    "chat", "tarjimon", "blockchain", "tadqiqot", "smart_energy", "dasturlash",
    "tibbiy", "talim", "biznes", "huquq", "psixologik", "moliya", "sayohat",
    "oshpazlik", "ijod", "musiqa", "sport", "obhavo", "yangiliklar", "matematik",
    "fan", "ovozli", "arxitektura", "ekologiya", "oyun"
]

# Dynamic endpoint creation
for ai_type in chat_endpoints:
    def create_handler(ai_type_name):
        async def handler(request: Request):
            return await handle_chat_request(request, ai_type_name)
        return handler
    
    handler = create_handler(ai_type)
    app.add_api_route(f"/chat/{ai_type}", handler, methods=["POST"])
    app.add_api_route(f"/api/chat/{ai_type}", handler, methods=["POST"])

# Chat management endpoints (PostgreSQL bilan)
@app.post("/api/chats")
async def create_or_update_chat(request: Request):
    if not db_initialized:
        return PlainTextResponse("error|database_unavailable|Database not available", status_code=503)
    
    try:
        body = await request.json()
        chat_id = body.get("id") or str(uuid.uuid4())
        title = body.get("title", "New Chat")
        user_id = str(body.get("user_id", "")).strip()
        ai_type = body.get("ai_type", "chat")
        
        if not user_id:
            return PlainTextResponse("error|missing_user_id|User ID is required", status_code=400)
        
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Mavjud suhbat bormi tekshirish
                    cur.execute("SELECT * FROM conversations WHERE id = %s", (chat_id,))
                    conversation = cur.fetchone()
                    
                    if not conversation:
                        # Yangi suhbat yaratish
                        cur.execute("""
                            INSERT INTO conversations (id, user_id, ai_type, title, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING *
                        """, (chat_id, user_id, ai_type, title, datetime.utcnow(), datetime.utcnow()))
                        conversation = cur.fetchone()
                    else:
                        
                        # Mavjud suhbatni yangilash
                        cur.execute("""
                            UPDATE conversations 
                            SET title = %s, updated_at = %s
                            WHERE id = %s
                            RETURNING *
                        """, (title, datetime.utcnow(), chat_id))
                        conversation = cur.fetchone()
                    
                    conn.commit()
                    
                    chat_data = {
                        "id": conversation['id'],
                        "ai_type": ai_type,
                        "title": title,
                        "user_id": user_id,
                        "created_at": conversation['created_at'].isoformat(),
                        "updated_at": conversation['updated_at'].isoformat()
                    }
                    
                    return PlainTextResponse(f"success|{json.dumps(chat_data)}|Chat saved successfully")
                    
        except Exception as db_error:
            print(f"Database error in create/update chat: {str(db_error)}")
            return PlainTextResponse("error|database_error|Failed to save chat", status_code=500)
        
    except json.JSONDecodeError:
        return PlainTextResponse("error|invalid_json|Invalid JSON data", status_code=400)
    except Exception as e:
        print(f"Create/update chat error: {str(e)}")
        return PlainTextResponse(f"error|create_failed|{str(e)}", status_code=500)

@app.put("/api/chats/{chat_id}")
async def update_chat(chat_id: str, request: Request):
    if not db_initialized:
        return PlainTextResponse("error|database_unavailable|Database not available", status_code=503)
    
    try:
        body = await request.json()
        title = body.get("title", "New Chat")
        user_id = str(body.get("user_id", "")).strip()
        ai_type = body.get("ai_type", "chat")
        
        if not user_id:
            return PlainTextResponse("error|missing_user_id|User ID is required", status_code=400)
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE conversations 
                        SET title = %s, updated_at = %s
                        WHERE id = %s AND user_id = %s
                    """, (title, datetime.utcnow(), chat_id, user_id))
                    
                    if cur.rowcount == 0:
                        return PlainTextResponse("error|chat_not_found|Chat not found or access denied", status_code=404)
                    
                    conn.commit()
                    return PlainTextResponse("success|chat_updated|Chat updated successfully")
                    
        except Exception as db_error:
            print(f"Database error in update chat: {str(db_error)}")
            return PlainTextResponse("error|database_error|Failed to update chat", status_code=500)
        
    except json.JSONDecodeError:
        return PlainTextResponse("error|invalid_json|Invalid JSON data", status_code=400)
    except Exception as e:
        print(f"Update chat error: {str(e)}")
        return PlainTextResponse(f"error|update_failed|{str(e)}", status_code=500)

@app.get("/api/chats/user/{user_id}")
async def get_user_chats(user_id: str):
    if not db_initialized:
        return PlainTextResponse("error|database_unavailable|Database not available", status_code=503)
    
    try:
        print(f"GET USER CHATS: {user_id}")
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM conversations 
                    WHERE user_id = %s 
                    ORDER BY updated_at DESC
                """, (user_id,))
                
                conversations = cur.fetchall()
        
        if not conversations:
            print(f"No chats found for user {user_id}")
            return PlainTextResponse("success|no_chats|No chats found")
        
        chats_data = []
        for conv in conversations:
            chats_data.append(f"{conv['id']}|{conv['ai_type']}|{conv['title']}|{conv['created_at']}|{conv['updated_at']}")
        
        result = "\n".join(chats_data)
        print(f"Found {len(conversations)} chats for user {user_id}")
        
        return PlainTextResponse(f"success|{result}|Chats retrieved")
        
    except Exception as e:
        print(f"Get chats error: {str(e)}")
        return PlainTextResponse(f"error|get_chats_failed|{str(e)}", status_code=500)

@app.get("/api/chats/{chat_id}")
async def get_chat_details(chat_id: str):
    if not db_initialized:
        return PlainTextResponse("error|database_unavailable|Database not available", status_code=503)
    
    try:
        print(f"GET CHAT DETAILS: {chat_id}")
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Suhbat ma'lumotlari
                cur.execute("SELECT * FROM conversations WHERE id = %s", (chat_id,))
                conversation = cur.fetchone()
                
                if not conversation:
                    return PlainTextResponse("error|chat_not_found|Chat not found", status_code=404)
                
                # Xabarlar
                cur.execute("""
                    SELECT * FROM messages 
                    WHERE conversation_id = %s 
                    ORDER BY timestamp ASC
                """, (chat_id,))
                
                messages = cur.fetchall()
        
        chat_info = f"{conversation['id']}|{conversation['ai_type']}|{conversation['title']}|{conversation['created_at']}|{conversation['updated_at']}"
        
        if messages:
            messages_info = "\n".join([
                f"MSG:{msg['id']}|{msg['content']}|{msg['ai_response']}|{msg['timestamp']}"
                for msg in messages
            ])
            return PlainTextResponse(f"success|{chat_info}|{messages_info}")
        else:
            return PlainTextResponse(f"success|{chat_info}|no_messages")
        
    except Exception as e:
        print(f"Get chat details error: {str(e)}")
        return PlainTextResponse(f"error|get_chat_failed|{str(e)}", status_code=500)

@app.get("/api/chats/{chat_id}/messages")
async def get_chat_messages_api(chat_id: str):
    if not db_initialized:
        return PlainTextResponse("error|database_unavailable|Database not available", status_code=503)
    
    try:
        print(f"GET CHAT MESSAGES: {chat_id}")
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Suhbat mavjudligini tekshirish
                cur.execute("SELECT id FROM conversations WHERE id = %s", (chat_id,))
                if not cur.fetchone():
                    return PlainTextResponse("error|chat_not_found|Chat not found", status_code=404)
                
                # Xabarlar
                cur.execute("""
                    SELECT * FROM messages 
                    WHERE conversation_id = %s 
                    ORDER BY timestamp ASC
                """, (chat_id,))
                
                messages = cur.fetchall()
        
        if not messages:
            print(f"No messages found for chat: {chat_id}")
            return PlainTextResponse("success|no_messages|No messages found")
        
        messages_data = []
        for msg in messages:
            messages_data.append(f"MSG:{msg['id']}|{msg['content']}|{msg['ai_response']}|{msg['timestamp']}")
        
        result = "\n".join(messages_data)
        print(f"Found {len(messages)} messages for chat: {chat_id}")
        
        return PlainTextResponse(f"success|{result}|Messages retrieved")
        
    except Exception as e:
        print(f"Get messages error: {str(e)}")
        return PlainTextResponse(f"error|get_messages_failed|{str(e)}", status_code=500)

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str, request: Request):
    if not db_initialized:
        return PlainTextResponse("error|database_unavailable|Database not available", status_code=503)
    
    try:
        user_id = request.query_params.get("user_id")
        if not user_id:
            try:
                body = await request.json()
                user_id = body.get("user_id")
            except:
                pass
        
        print(f"DELETE CHAT: {chat_id}, user: {user_id}")
        
        if chat_id == "undefined" or not chat_id:
            return PlainTextResponse("error|invalid_chat_id|Chat ID is required", status_code=400)
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Suhbat mavjudligini va egasini tekshirish
                cur.execute("SELECT user_id FROM conversations WHERE id = %s", (chat_id,))
                conversation = cur.fetchone()
                
                if not conversation:
                    return PlainTextResponse("error|chat_not_found|Chat not found", status_code=404)
                
                if user_id and conversation[0] != str(user_id):
                    return PlainTextResponse("error|unauthorized|Unauthorized to delete this chat", status_code=403)
                
                # Xabarlarni o'chirish
                cur.execute("DELETE FROM messages WHERE conversation_id = %s", (chat_id,))
                
                # Suhbatni o'chirish
                cur.execute("DELETE FROM conversations WHERE id = %s", (chat_id,))
                
                conn.commit()
        
        print(f"CHAT DELETED: {chat_id}")
        return PlainTextResponse("success|chat_deleted|Chat deleted successfully")
        
    except Exception as e:
        print(f"Delete chat error: {str(e)}")
        return PlainTextResponse(f"error|delete_failed|{str(e)}", status_code=500)

@app.delete("/api/chats/user/{user_id}/all")
async def delete_all_user_chats(user_id: str):
    if not db_initialized:
        return PlainTextResponse("error|database_unavailable|Database not available", status_code=503)
    
    try:
        print(f"DELETE ALL CHATS FOR USER: {user_id}")
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # User ning barcha suhbatlarini topish
                cur.execute("SELECT id FROM conversations WHERE user_id = %s", (user_id,))
                conversations = cur.fetchall()
                
                if not conversations:
                    return PlainTextResponse("error|no_chats|No chats found to delete", status_code=404)
                
                conversation_ids = [conv[0] for conv in conversations]
                
                # Xabarlarni o'chirish
                for conv_id in conversation_ids:
                    cur.execute("DELETE FROM messages WHERE conversation_id = %s", (conv_id,))
                
                # Suhbatlarni o'chirish
                cur.execute("DELETE FROM conversations WHERE user_id = %s", (user_id,))
                
                conn.commit()
        
        print(f"ALL CHATS DELETED FOR USER: {user_id} ({len(conversations)} chats)")
        return PlainTextResponse(f"success|all_chats_deleted|{len(conversations)} chats deleted successfully")
        
    except Exception as e:
        print(f"Delete all chats error: {str(e)}")
        return PlainTextResponse(f"error|delete_all_failed|{str(e)}", status_code=500)

# Statistics endpoints
@app.get("/api/stats/user/{user_id}")
async def get_user_stats_api(user_id: str):
    if not db_initialized:
        return PlainTextResponse("error|database_unavailable|Database not available", status_code=503)
    
    try:
        print(f"GET USER STATS: {user_id}")
        
        if not user_id or len(user_id.strip()) == 0:
            return PlainTextResponse("error|invalid_user_id|User ID cannot be empty", status_code=422)
        
        user_id = user_id.strip()
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # User mavjudligini tekshirish
                cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cur.fetchone():
                    return PlainTextResponse("success|no_user_found|User not found, no statistics available")
                
                # Statistika
                cur.execute("""
                    SELECT * FROM user_stats 
                    WHERE user_id = %s 
                    ORDER BY usage_count DESC
                """, (user_id,))
                stats = cur.fetchall()
                
                # Suhbatlar soni
                cur.execute("SELECT COUNT(*) FROM conversations WHERE user_id = %s", (user_id,))
                total_conversations = cur.fetchone()[0]
        
        total_messages = sum(stat['usage_count'] for stat in stats) if stats else 0
        most_used_ai = stats[0]['ai_type'] if stats else "None"
        
        if not stats:
            stats_data = [
                "TOTAL_MESSAGES:0",
                "TOTAL_CONVERSATIONS:0",
                "MOST_USED_AI:None"
            ]
            result = "\n".join(stats_data)
            return PlainTextResponse(f"success|{result}|No statistics available yet")
        
        stats_data = [
            f"TOTAL_MESSAGES:{total_messages}",
            f"TOTAL_CONVERSATIONS:{total_conversations}",
            f"MOST_USED_AI:{most_used_ai}"
        ]
        
        for stat in stats:
            stats_data.append(f"AI_STAT:{stat['ai_type']}|{stat['usage_count']}|{stat['last_used']}")
        
        result = "\n".join(stats_data)
        print(f"Stats retrieved for user {user_id}: {total_messages} messages, {total_conversations} chats")
        
        return PlainTextResponse(f"success|{result}|Stats retrieved")
        
    except Exception as e:
        print(f"Get stats error: {str(e)}")
        return PlainTextResponse(f"error|stats_failed|{str(e)}", status_code=500)

@app.get("/api/stats/chart/user/{user_id}")
async def get_user_chart_stats_api(user_id: str):
    if not db_initialized:
        return PlainTextResponse("error|database_unavailable|Database not available", status_code=503)
    
    try:
        print(f"GET USER CHART STATS: {user_id}")
        
        if not user_id or len(user_id.strip()) == 0:
            return PlainTextResponse("error|invalid_user_id|User ID cannot be empty", status_code=422)
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM user_stats 
                    WHERE user_id = %s 
                    ORDER BY usage_count DESC 
                    LIMIT 10
                """, (user_id.strip(),))
                
                stats = cur.fetchall()
        
        if not stats:
            chart_data = "LABELS:\nDATA:"
            return PlainTextResponse(f"success|{chart_data}|No chart data available")
        
        labels = [stat['ai_type'] for stat in stats]
        data = [stat['usage_count'] for stat in stats]
        
        chart_data = f"LABELS:{','.join(labels)}\nDATA:{','.join(map(str, data))}"
        
        return PlainTextResponse(f"success|{chart_data}|Chart data retrieved")
        
    except Exception as e:
        print(f"Get chart stats error: {str(e)}")
        return PlainTextResponse(f"error|chart_failed|{str(e)}", status_code=500)

# Legacy endpoints
@app.get("/conversations")
async def get_conversations_legacy(user_id: str):
    return await get_user_chats(user_id)

@app.get("/api/conversations")
async def api_get_conversations_legacy(user_id: str):
    return await get_user_chats(user_id)

# OPTIONS handlers for CORS
@app.options("/api/chats")
async def options_chats():
    return PlainTextResponse("", status_code=200)

@app.options("/api/chats/{chat_id}")
async def options_chat():
    return PlainTextResponse("", status_code=200)

@app.options("/api/chats/user/{user_id}/all")
async def options_all_chats():
    return PlainTextResponse("", status_code=200)

@app.options("/api/chats/{chat_id}/messages")
async def options_chat_messages():
    return PlainTextResponse("", status_code=200)

@app.options("/api/stats/user/{user_id}")
async def options_user_stats():
    return PlainTextResponse("", status_code=200)

@app.options("/api/stats/chart/user/{user_id}")
async def options_chart_stats():
    return PlainTextResponse("", status_code=200)

@app.options("/auth/google")
async def options_google_auth():
    return PlainTextResponse("", status_code=200)

@app.options("/api/auth/google")
async def options_api_google_auth():
    return PlainTextResponse("", status_code=200)

# Dynamic OPTIONS handlers for chat endpoints
for ai_type in chat_endpoints:
    def create_options_handler():
        async def handler():
            return PlainTextResponse("", status_code=200)
        return handler
    
    options_handler = create_options_handler()
    app.add_api_route(f"/chat/{ai_type}", options_handler, methods=["OPTIONS"])
    app.add_api_route(f"/api/chat/{ai_type}", options_handler, methods=["OPTIONS"])

@app.options("/api/ai/{ai_id}")
async def options_ai_by_id():
    return PlainTextResponse("", status_code=200)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return PlainTextResponse("error|not_found|Endpoint not found", status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error("Internal server error", error=str(exc))
    return PlainTextResponse("error|server_error|Internal server error", status_code=500)

@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    logger.error("Validation error", error=str(exc))
    return PlainTextResponse("error|validation_error|Request validation failed", status_code=422)

# Health check with database
@app.get("/api/health/db")
async def health_check_db():
    if not db_initialized:
        return PlainTextResponse("error|db_unavailable|Database not available", status_code=503)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return PlainTextResponse("success|healthy|Database connection OK")
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return PlainTextResponse(f"error|db_error|Database connection failed: {str(e)}", status_code=500)

# AI modules status
@app.get("/api/ai/status")
async def ai_modules_status():
    try:
        status_data = []
        for ai_type, ai_instance in AI_ASSISTANTS.items():
            is_dummy = isinstance(ai_instance, DummyAI)
            status = "dummy" if is_dummy else "active"
            status_data.append(f"{ai_type}:{status}")
        
        result = "\n".join(status_data)
        active_count = len([ai for ai in AI_ASSISTANTS.values() if not isinstance(ai, DummyAI)])
        dummy_count = len([ai for ai in AI_ASSISTANTS.values() if isinstance(ai, DummyAI)])
        
        summary = f"SUMMARY:active={active_count},dummy={dummy_count},total={len(AI_ASSISTANTS)}"
        
        return PlainTextResponse(f"success|{result}\n{summary}|AI modules status retrieved")
        
    except Exception as e:
        print(f"AI status error: {str(e)}")
        return PlainTextResponse(f"error|status_failed|{str(e)}", status_code=500)

# Development endpoints
if os.getenv("DEBUG", "False").lower() == "true":
    @app.get("/api/debug/tables")
    async def debug_tables():
        if not db_initialized:
            return PlainTextResponse("error|db_unavailable|Database not available", status_code=503)
        
        try:
            tables_info = []
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM users")
                    users_count = cur.fetchone()[0]
                    tables_info.append(f"users:{users_count}")
                    
                    cur.execute("SELECT COUNT(*) FROM conversations")
                    conversations_count = cur.fetchone()[0]
                    tables_info.append(f"conversations:{conversations_count}")
                    
                    cur.execute("SELECT COUNT(*) FROM messages")
                    messages_count = cur.fetchone()[0]
                    tables_info.append(f"messages:{messages_count}")
                    
                    cur.execute("SELECT COUNT(*) FROM user_stats")
                    stats_count = cur.fetchone()[0]
                    tables_info.append(f"user_stats:{stats_count}")
            
            result = "\n".join(tables_info)
            return PlainTextResponse(f"success|{result}|Tables info retrieved")
            
        except Exception as e:
            return PlainTextResponse(f"error|debug_failed|{str(e)}", status_code=500)

    @app.get("/api/debug/env")
    async def debug_env():
        try:
            env_info = []
            
            important_vars = [
                "DATABASE_URL", "OPENAI_API_KEY", "GOOGLE_CLIENT_ID", 
                "JWT_SECRET", "HOST", "PORT", "DEBUG", "CORS_ORIGINS"
            ]
            
            for var in important_vars:
                value = os.getenv(var, "NOT_SET")
                if var in ["DATABASE_URL", "OPENAI_API_KEY", "JWT_SECRET"]:
                    if value and value != "NOT_SET":
                        masked = value[:10] + "***" + value[-5:] if len(value) > 15 else "***"
                        env_info.append(f"{var}:{masked}")
                    else:
                        env_info.append(f"{var}:NOT_SET")
                else:
                    env_info.append(f"{var}:{value}")
            
            result = "\n".join(env_info)
            return PlainTextResponse(f"success|{result}|Environment info retrieved")
            
        except Exception as e:
            return PlainTextResponse(f"error|debug_failed|{str(e)}", status_code=500)

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        response = await call_next(request)
    except Exception as e:
        print(f"❌ MIDDLEWARE ERROR: {request.method} {request.url.path} - {str(e)} - IP: {client_ip}")
        return PlainTextResponse("error|server_error|Internal server error", status_code=500)
    
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    if response.status_code == 422:
        print(f"⚠️ VALIDATION ERROR: {request.method} {request.url.path} - 422 - {process_time:.3f}s - IP: {client_ip}")
        print(f"   Query params: {dict(request.query_params)}")
        print(f"   Path params: {dict(request.path_params)}")
    elif response.status_code >= 400:
        print(f"❌ ERROR: {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s - IP: {client_ip}")
    elif any(path in str(request.url.path) for path in ["/api/", "/chat/", "/auth/"]):
        print(f"✅ {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s - IP: {client_ip}")
    
    return response

# Startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 AI Universe Server starting...")
    print(f"📊 Database initialized: {'Yes' if db_initialized else 'No'}")
    print(f"📊 Total AI assistants loaded: {len(AI_ASSISTANTS)}")
    active_ais = [name for name, ai in AI_ASSISTANTS.items() if not isinstance(ai, DummyAI)]
    dummy_ais = [name for name, ai in AI_ASSISTANTS.items() if isinstance(ai, DummyAI)]
    print(f"✅ Active AI modules: {len(active_ais)}")
    print(f"⚠️ Dummy AI modules: {len(dummy_ais)}")
    print("🌐 Server ready to serve requests!")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 AI Universe Server shutting down...")
    if db_pool:
        db_pool.closeall()
        print("📊 Database connections closed")
    print("👋 Goodbye!")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    print(f"🔧 Starting server on {host}:{port}")
    print(f"🔍 Debug mode: {debug}")
    print(f"📝 Log level: {log_level}")
    
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        log_level=log_level, 
        reload=debug,
        access_log=True
    )