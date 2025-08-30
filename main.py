from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid
import structlog
from openai import OpenAI
import jwt
import json
import asyncpg  # PostgreSQL uchun async driver
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

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

# Database setup - PostgreSQL (Render.com) - FIXED
DATABASE_URL = os.getenv("DATABASE_URL")

# Render.com PostgreSQL URL format ni tekshirish
if DATABASE_URL:
    print(f"Database URL configured: {DATABASE_URL.split('@')[0]}@***")
    
    # PostgreSQL URL format ni to'g'rilash
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
else:
    # Fallback konfiguratsiya
    db_user = os.getenv("PGUSER", "ai_universe_db_user")
    db_password = os.getenv("PGPASSWORD", "")
    db_host = os.getenv("PGHOST", "localhost")
    db_port = os.getenv("PGPORT", "5432")
    db_name = os.getenv("PGDATABASE", "ai_universe_db")
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# FIXED: Initialize Base BEFORE using it
Base = declarative_base()
engine = None
SessionLocal = None

# FIXED: PostgreSQL ulanish muammosini hal qilish
try:
    # psycopg2-binary o'rniga asyncpg ishlatish yoki SQLite fallback
    try:
        # PostgreSQL ulanishni sinash
        import psycopg2
        
        # FIXED: Pool va ulanish sozlamalari yaxshilangan
        engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=5,
            max_overflow=10,
            echo=False,
            # FIXED: PostgreSQL uchun to'g'ri connect_args
            connect_args={
                "sslmode": "require" if "localhost" not in DATABASE_URL else "prefer",
                "application_name": "ai_universe_app",
                "connect_timeout": 30,
                "options": "-c timezone=utc"
            }
        )
        
        # Ulanishni sinash
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("✅ PostgreSQL database engine yaratildi va sinovdan o'tdi")
        
    except ImportError:
        print("⚠️ psycopg2 mavjud emas, asyncpg yoki SQLite ishlatiladi")
        raise Exception("psycopg2 not available")
        
    except Exception as psycopg_error:
        print(f"⚠️ PostgreSQL ulanish xatosi: {str(psycopg_error)}")
        print("🔄 SQLite fallback ga o'tilmoqda...")
        raise Exception("PostgreSQL connection failed")
        
except Exception as e:
    # FIXED: SQLite fallback - mahalliy rivojlantirish uchun
    print(f"PostgreSQL ulanish xatosi: {str(e)}")
    print("🔄 SQLite fallback ishga tushirilmoqda...")
    
    try:
        # SQLite fallback
        sqlite_path = os.getenv("SQLITE_DB_PATH", "ai_universe.db")
        engine = create_engine(
            f"sqlite:///{sqlite_path}",
            pool_pre_ping=True,
            echo=False
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print(f"✅ SQLite fallback database yaratildi: {sqlite_path}")
        
    except Exception as sqlite_error:
        logger.error(f"SQLite fallback ham muvaffaqiyatsiz: {str(sqlite_error)}")
        print(f"❌ SQLite fallback xatosi: {str(sqlite_error)}")
        
        # FIXED: Dummy session - crash bo'lmaslik uchun
        class DummySession:
            def query(self, *args, **kwargs):
                return self
            def filter(self, *args, **kwargs):
                return self
            def first(self):
                return None
            def all(self):
                return []
            def count(self):
                return 0
            def add(self, obj):
                pass
            def delete(self, obj):
                pass
            def commit(self):
                pass
            def rollback(self):
                pass
            def close(self):
                pass
            def refresh(self, obj):
                pass
            def execute(self, *args, **kwargs):
                class Result:
                    def fetchone(self):
                        return (1,)
                return Result()
        
        def DummySessionLocal():
            return DummySession()
        
        SessionLocal = DummySessionLocal
        engine = None
        print("⚠️ Dummy database session ishga tushirildi")

# Models - NOW Base is defined
class User(Base):
    __tablename__ = "users"
    id = Column(String(255), primary_key=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    picture = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String(255), primary_key=True)
    user_id = Column(String(255))
    ai_type = Column(String(100))
    title = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String(255), primary_key=True)
    conversation_id = Column(String(255))
    user_id = Column(String(255))
    content = Column(Text)
    ai_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserStats(Base):
    __tablename__ = "user_stats"
    id = Column(String(255), primary_key=True)
    user_id = Column(String(255))
    ai_type = Column(String(100))
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, default=datetime.utcnow)

# Create tables - FIXED
try:
    if engine:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables setup completed")
        print("✅ Database jadvallari muvaffaqiyatli yaratildi")
    else:
        print("⚠️ Database engine not available, skipping table creation")
except Exception as e:
    logger.error("Database setup failed", error=str(e))
    print(f"⚠️ Jadval yaratishda xato: {str(e)}")

# FastAPI app
app = FastAPI(
    title="AI Universe - Professional AI Platform",
    description="25 ta professional AI xizmati bir platformada",
    version="1.0.0"
)

# FIXED: CORS middleware - to'liq sozlamalar
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
    "*"  # Development uchun
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# FIXED: AI assistants import - xatolarni handle qilish
class DummyAI:
    """AI modullari mavjud bo'lmaganda ishlatish uchun"""
    def __init__(self, ai_type="dummy"):
        self.ai_type = ai_type
        # FIXED: OpenAI client ni to'g'ri ishlatish
        self.client = client if client else None
    
    async def get_response(self, message: str) -> str:
        if self.client:
            try:
                # FIXED: OpenAI API ni to'g'ri chaqirish
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

# AI modules loading - FIXED
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

# Database dependency
def get_db():
    if SessionLocal:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        # Dummy session agar database mavjud bo'lmasa
        class DummySession:
            def query(self, *args, **kwargs): return self
            def filter(self, *args, **kwargs): return self
            def first(self): return None
            def all(self): return []
            def count(self): return 0
            def add(self, obj): pass
            def delete(self, obj): pass
            def commit(self): pass
            def rollback(self): pass
            def close(self): pass
            def refresh(self, obj): pass
            def execute(self, *args, **kwargs):
                class Result:
                    def fetchone(self): return (1,)
                return Result()
        yield DummySession()

# FIXED: Root endpoints - GET va POST qo'llab-quvvatlash
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

# FIXED: Google Auth - Exception handling yaxshilangan
@app.post("/api/auth/google") 
async def google_auth(request: Request, db: Session = Depends(get_db)):
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
        
        # Bazadan foydalanuvchini qidirish
        try:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                user = User(
                    id=str(uuid.uuid4()),
                    email=email,
                    name=name,
                    picture=picture,
                    created_at=datetime.utcnow()
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"New user created: {email}")
            else:
                user.name = name
                user.picture = picture
                db.commit()
                logger.info(f"Existing user updated: {email}")
        except Exception as db_error:
            try:
                db.rollback()
            except:
                pass
            logger.error(f"Database error in auth: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Database operation failed", status_code=500)
        
        user_info = {
            "id": str(user.id) if hasattr(user, 'id') else str(uuid.uuid4()),
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

# FIXED: Chat processing with better error handling
async def process_chat(ai_assistant, message: str, user_id: str, conversation_id: str | None, ai_type: str, db: Session):
    try:
        if not user_id:
            return PlainTextResponse("error|missing_user_id|User ID is required", status_code=400)
        if not message:
            return PlainTextResponse("error|missing_message|Message is required", status_code=400)
        
        ai_response = await ai_assistant.get_response(message)
        
        try:
            # Yangi suhbat yaratish
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                conversation = Conversation(
                    id=conversation_id,
                    user_id=str(user_id),
                    ai_type=ai_type,
                    title=message[:50] + "..." if len(message) > 50 else message
                )
                db.add(conversation)
            
            # Xabarni saqlash
            message_entry = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                user_id=str(user_id),
                content=message,
                ai_response=ai_response
            )
            db.add(message_entry)
            
            # Statistikani yangilash
            stats = db.query(UserStats).filter(
                UserStats.user_id == str(user_id),
                UserStats.ai_type == ai_type
            ).first()
            
            if not stats:
                stats = UserStats(
                    id=str(uuid.uuid4()),
                    user_id=str(user_id),
                    ai_type=ai_type,
                    usage_count=1
                )
                db.add(stats)
            else:
                stats.usage_count += 1
                stats.last_used = datetime.utcnow()
            
            # Suhbat vaqtini yangilash
            if conversation_id:
                conversation = db.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()
                if conversation:
                    conversation.updated_at = datetime.utcnow()
            
            db.commit()
            
        except Exception as db_error:
            try:
                db.rollback()
            except:
                pass
            logger.error(f"Database error in chat: {str(db_error)}")
            # Database xatosi bo'lsa ham AI javobini qaytarish
            return PlainTextResponse(f"success|{ai_response}|{conversation_id or 'temp'}")
        
        return PlainTextResponse(f"success|{ai_response}|{conversation_id}")
    except Exception as e:
        logger.error(f"Chat failed for {ai_type}", error=str(e))
        return PlainTextResponse(f"error|chat_failed|{str(e)}", status_code=500)

async def handle_chat_request(request: Request, ai_type: str, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        message = body.get("message")
        user_id = body.get("user_id")
        conversation_id = body.get("conversation_id")
        
        print(f"Chat request: ai_type={ai_type}, message={message[:50] if message else 'None'}..., user_id={user_id}")
        
        if not AI_ASSISTANTS.get(ai_type):
            return PlainTextResponse(f"error|invalid_ai_type|AI type '{ai_type}' not found", status_code=404)
        
        return await process_chat(
            AI_ASSISTANTS[ai_type], 
            message, 
            user_id, 
            conversation_id, 
            ai_type, 
            db
        )
    except json.JSONDecodeError:
        return PlainTextResponse("error|invalid_json|Invalid JSON data", status_code=400)
    except Exception as e:
        logger.error(f"Handle chat request failed for {ai_type}", error=str(e))
        return PlainTextResponse(f"error|request_failed|{str(e)}", status_code=500)

# AI ID ga asosan routing
@app.post("/api/ai/{ai_id}")
async def api_chat_by_id(ai_id: int, request: Request, db: Session = Depends(get_db)):
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
        
        return await handle_chat_request(request, ai_type, db)
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
        async def handler(request: Request, db: Session = Depends(get_db)):
            return await handle_chat_request(request, ai_type_name, db)
        return handler
    
    handler = create_handler(ai_type)
    app.add_api_route(f"/chat/{ai_type}", handler, methods=["POST"])
    app.add_api_route(f"/api/chat/{ai_type}", handler, methods=["POST"])

# FIXED: Chat management with better database error handling
@app.post("/api/chats")
async def create_or_update_chat(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        chat_id = body.get("id") or str(uuid.uuid4())
        title = body.get("title", "New Chat")
        user_id = str(body.get("user_id", "")).strip()
        ai_type = body.get("ai_type", "chat")
        
        # User ID tekshirish
        if not user_id or user_id == "":
            print(f"⚠️ WARNING: Empty user_id for chat creation")
            auth_header = request.headers.get("authorization", "")
            if auth_header:
                try:
                    token = auth_header.replace("Bearer ", "")
                    payload = jwt.decode(token, options={"verify_signature": False})
                    user_id = payload.get("sub", payload.get("user_id", ""))
                    print(f"🔍 User ID from token: {user_id}")
                except Exception as e:
                    print(f"❌ Token decode error: {str(e)}")
        
        print(f"CREATE/UPDATE CHAT: {chat_id}, user: {user_id or 'EMPTY'}, type: {ai_type}")
        
        try:
            conversation = db.query(Conversation).filter(Conversation.id == chat_id).first()
            
            if not conversation:
                conversation = Conversation(
                    id=chat_id,
                    user_id=user_id or "anonymous",
                    ai_type=ai_type,
                    title=title,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(conversation)
                print(f"NEW CHAT CREATED: {chat_id} for user: {user_id or 'anonymous'}")
            else:
                conversation.title = title
                conversation.updated_at = datetime.utcnow()
                if user_id:
                    conversation.user_id = user_id
                print(f"CHAT UPDATED: {chat_id} for user: {conversation.user_id}")
            
            db.commit()
            db.refresh(conversation)
            
        except Exception as db_error:
            try:
                db.rollback()
            except:
                pass
            logger.error(f"Database error in create chat: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to save chat", status_code=500)
        
        chat_data = {
            "id": conversation.id if hasattr(conversation, 'id') else chat_id,
            "ai_type": ai_type,
            "title": title,
            "user_id": user_id or "anonymous",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return PlainTextResponse(f"success|{json.dumps(chat_data)}|Chat saved successfully")
        
    except json.JSONDecodeError:
        return PlainTextResponse("error|invalid_json|Invalid JSON data", status_code=400)
    except Exception as e:
        print(f"❌ CREATE CHAT ERROR: {str(e)}")
        return PlainTextResponse(f"error|create_failed|{str(e)}", status_code=500)


@app.put("/api/chats/{chat_id}")
async def update_chat(chat_id: str, request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        title = body.get("title", "New Chat")
        user_id = str(body.get("user_id", "")).strip()
        ai_type = body.get("ai_type", "chat")
        
        # User ID tekshirish
        if not user_id or user_id == "":
            print(f"⚠️ WARNING: Empty user_id for chat {chat_id}")
            auth_header = request.headers.get("authorization", "")
            if auth_header:
                try:
                    token = auth_header.replace("Bearer ", "")
                    payload = jwt.decode(token, options={"verify_signature": False})
                    user_id = payload.get("sub", payload.get("user_id", ""))
                    print(f"🔍 User ID from token: {user_id}")
                except Exception as e:
                    print(f"❌ Token decode error: {str(e)}")
        
        print(f"UPDATE CHAT: {chat_id}, user: {user_id or 'EMPTY'}, type: {ai_type}")
        
        try:
            conversation = db.query(Conversation).filter(Conversation.id == chat_id).first()
            
            if not conversation:
                conversation = Conversation(
                    id=chat_id,
                    user_id=user_id or "anonymous",
                    ai_type=ai_type,
                    title=title,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(conversation)
                print(f"NEW CHAT CREATED: {chat_id} for user: {user_id or 'anonymous'}")
            else:
                conversation.title = title
                conversation.updated_at = datetime.utcnow()
                if user_id:
                    conversation.user_id = user_id
                print(f"CHAT UPDATED: {chat_id} for user: {conversation.user_id}")
            
            db.commit()
            
        except Exception as db_error:
            try:
                db.rollback()
            except:
                pass
            logger.error(f"Database error in update chat: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to update chat", status_code=500)
        
        return PlainTextResponse("success|chat_saved|Chat saved successfully")
        
    except json.JSONDecodeError:
        return PlainTextResponse("error|invalid_json|Invalid JSON data", status_code=400)
    except Exception as e:
        print(f"❌ UPDATE CHAT ERROR: {str(e)}")
        return PlainTextResponse(f"error|update_failed|{str(e)}", status_code=500)

@app.get("/api/chats/user/{user_id}")
async def get_user_chats(user_id: str, db: Session = Depends(get_db)):
    try:
        print(f"GET USER CHATS: {user_id}")
        
        try:
            conversations = db.query(Conversation).filter(
                Conversation.user_id == str(user_id)
            ).order_by(Conversation.updated_at.desc()).all()
        except Exception as db_error:
            logger.error(f"Database error in get chats: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to retrieve chats", status_code=500)
        
        if not conversations:
            print(f"No chats found for user {user_id}")
            return PlainTextResponse("success|no_chats|No chats found")
        
        chats_data = []
        for conv in conversations:
            chats_data.append(f"{conv.id}|{conv.ai_type}|{conv.title}|{conv.created_at}|{conv.updated_at}")
        
        result = "\n".join(chats_data)
        print(f"Found {len(conversations)} chats for user {user_id}")
        
        return PlainTextResponse(f"success|{result}|Chats retrieved")
        
    except Exception as e:
        print(f"GET CHATS ERROR: {str(e)}")
        return PlainTextResponse(f"error|get_chats_failed|{str(e)}", status_code=500)

@app.get("/api/chats/{chat_id}")
async def get_chat_details(chat_id: str, db: Session = Depends(get_db)):
    try:
        print(f"GET CHAT DETAILS: {chat_id}")
        
        try:
            conversation = db.query(Conversation).filter(Conversation.id == chat_id).first()
        except Exception as db_error:
            logger.error(f"Database error in get chat details: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to retrieve chat details", status_code=500)
        
        if not conversation:
            return PlainTextResponse("error|chat_not_found|Chat not found", status_code=404)
        
        try:
            messages = db.query(Message).filter(
                Message.conversation_id == chat_id
            ).order_by(Message.timestamp.asc()).all()
        except Exception as db_error:
            logger.error(f"Database error in get messages: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to retrieve messages", status_code=500)
        
        chat_info = f"{conversation.id}|{conversation.ai_type}|{conversation.title}|{conversation.created_at}|{conversation.updated_at}"
        
        if messages:
            messages_info = "\n".join([
                f"MSG:{msg.id}|{msg.content}|{msg.ai_response}|{msg.timestamp}"
                for msg in messages
            ])
            return PlainTextResponse(f"success|{chat_info}|{messages_info}")
        else:
            return PlainTextResponse(f"success|{chat_info}|no_messages")
        
    except Exception as e:
        print(f"GET CHAT DETAILS ERROR: {str(e)}")
        return PlainTextResponse(f"error|get_chat_failed|{str(e)}", status_code=500)

@app.get("/api/chats/{chat_id}/messages")
async def get_chat_messages_api(chat_id: str, db: Session = Depends(get_db)):
    try:
        print(f"GET CHAT MESSAGES: {chat_id}")
        
        try:
            conversation = db.query(Conversation).filter(Conversation.id == chat_id).first()
        except Exception as db_error:
            logger.error(f"Database error in get chat messages: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to retrieve chat", status_code=500)
        
        if not conversation:
            print(f"Chat not found: {chat_id}")
            return PlainTextResponse("error|chat_not_found|Chat not found", status_code=404)
        
        try:
            messages = db.query(Message).filter(
                Message.conversation_id == chat_id
            ).order_by(Message.timestamp.asc()).all()
        except Exception as db_error:
            logger.error(f"Database error in get messages: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to retrieve messages", status_code=500)
        
        if not messages:
            print(f"No messages found for chat: {chat_id}")
            return PlainTextResponse("success|no_messages|No messages found")
        
        messages_data = []
        for msg in messages:
            messages_data.append(f"MSG:{msg.id}|{msg.content}|{msg.ai_response}|{msg.timestamp}")
        
        result = "\n".join(messages_data)
        print(f"Found {len(messages)} messages for chat: {chat_id}")
        
        return PlainTextResponse(f"success|{result}|Messages retrieved")
        
    except Exception as e:
        print(f"GET MESSAGES ERROR: {str(e)}")
        return PlainTextResponse(f"error|get_messages_failed|{str(e)}", status_code=500)

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str, request: Request, db: Session = Depends(get_db)):
    """Bitta chatni o'chirish"""
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
        
        try:
            conversation = db.query(Conversation).filter(Conversation.id == chat_id).first()
        except Exception as db_error:
            logger.error(f"Database error in delete chat: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to access chat", status_code=500)
        
        if not conversation:
            return PlainTextResponse("error|chat_not_found|Chat not found", status_code=404)
        
        if user_id and conversation.user_id != str(user_id):
            return PlainTextResponse("error|unauthorized|Unauthorized to delete this chat", status_code=403)
        
        try:
            db.query(Message).filter(Message.conversation_id == chat_id).delete()
            db.delete(conversation)
            db.commit()
        except Exception as db_error:
            try:
                db.rollback()
            except:
                pass
            logger.error(f"Database error in delete chat: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to delete chat", status_code=500)
        
        print(f"CHAT DELETED: {chat_id}")
        return PlainTextResponse("success|chat_deleted|Chat deleted successfully")
        
    except Exception as e:
        print(f"DELETE CHAT ERROR: {str(e)}")
        return PlainTextResponse(f"error|delete_failed|{str(e)}", status_code=500)

@app.delete("/api/chats/user/{user_id}/all")
async def delete_all_user_chats(user_id: str, db: Session = Depends(get_db)):
    """User ning barcha chatlarini o'chirish"""
    try:
        print(f"DELETE ALL CHATS FOR USER: {user_id}")
        
        try:
            conversations = db.query(Conversation).filter(
                Conversation.user_id == str(user_id)
            ).all()
        except Exception as db_error:
            logger.error(f"Database error in delete all chats: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to access chats", status_code=500)
        
        if not conversations:
            print(f"No chats found for user {user_id}")
            return PlainTextResponse("error|no_chats|No chats found to delete", status_code=404)
        
        conversation_ids = [conv.id for conv in conversations]
        
        try:
            for conv_id in conversation_ids:
                db.query(Message).filter(Message.conversation_id == conv_id).delete()
            
            db.query(Conversation).filter(
                Conversation.user_id == str(user_id)
            ).delete()
            
            db.commit()
        except Exception as db_error:
            try:
                db.rollback()
            except:
                pass
            logger.error(f"Database error in delete all chats: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to delete chats", status_code=500)
        
        print(f"ALL CHATS DELETED FOR USER: {user_id} ({len(conversations)} chats)")
        return PlainTextResponse(f"success|all_chats_deleted|{len(conversations)} chats deleted successfully")
        
    except Exception as e:
        print(f"DELETE ALL CHATS ERROR: {str(e)}")
        return PlainTextResponse(f"error|delete_all_failed|{str(e)}", status_code=500)

# FIXED: Stats endpoints with better error handling
@app.get("/api/stats/user/{user_id}")
async def get_user_stats_api(user_id: str, db: Session = Depends(get_db)):
    """User statistikalari - 422 xatosini hal qilish"""
    try:
        print(f"GET USER STATS: {user_id}")
        
        # User ID formatini tekshirish
        if not user_id or len(user_id.strip()) == 0:
            print(f"WARNING: Empty user_id provided")
            return PlainTextResponse("error|invalid_user_id|User ID cannot be empty", status_code=422)
        
        # UUID formatini tekshirish
        user_id = user_id.strip()
        if len(user_id) < 10:
            print(f"WARNING: Too short user_id: {user_id}")
            return PlainTextResponse("error|invalid_user_id|User ID format invalid", status_code=422)
        
        try:
            # User mavjudligini tekshirish
            user_exists = db.query(User).filter(User.id == user_id).first()
            if not user_exists:
                print(f"User not found in database: {user_id}")
                return PlainTextResponse("success|no_user_found|User not found, no statistics available")
            
            stats = db.query(UserStats).filter(
                UserStats.user_id == str(user_id)
            ).order_by(UserStats.usage_count.desc()).all()
            
            total_conversations = db.query(Conversation).filter(
                Conversation.user_id == str(user_id)
            ).count()
            
        except Exception as db_error:
            logger.error(f"Database error in get stats: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to retrieve statistics", status_code=500)
        
        total_messages = sum(stat.usage_count for stat in stats) if stats else 0
        most_used_ai = stats[0].ai_type if stats else "None"
        
        if not stats:
            print(f"No stats found for user {user_id}")
            stats_data = []
            stats_data.append("TOTAL_MESSAGES:0")
            stats_data.append("TOTAL_CONVERSATIONS:0")  
            stats_data.append("MOST_USED_AI:None")
            result = "\n".join(stats_data)
            return PlainTextResponse(f"success|{result}|No statistics available yet")
        
        stats_data = []
        stats_data.append(f"TOTAL_MESSAGES:{total_messages}")
        stats_data.append(f"TOTAL_CONVERSATIONS:{total_conversations}")  
        stats_data.append(f"MOST_USED_AI:{most_used_ai}")
        
        for stat in stats:
            stats_data.append(f"AI_STAT:{stat.ai_type}|{stat.usage_count}|{stat.last_used}")
        
        result = "\n".join(stats_data)
        print(f"Stats retrieved for user {user_id}: {total_messages} messages, {total_conversations} chats")
        
        return PlainTextResponse(f"success|{result}|Stats retrieved")
        
    except Exception as e:
        print(f"GET STATS ERROR: {str(e)}")
        return PlainTextResponse(f"error|stats_failed|Unable to retrieve statistics: {str(e)}", status_code=500)

@app.get("/api/stats/chart/user/{user_id}")
async def get_user_chart_stats_api(user_id: str, db: Session = Depends(get_db)):
    """User chart statistikalari"""
    try:
        print(f"GET USER CHART STATS: {user_id}")
        
        # User ID tekshirish
        if not user_id or len(user_id.strip()) == 0:
            return PlainTextResponse("error|invalid_user_id|User ID cannot be empty", status_code=422)
        
        user_id = user_id.strip()
        
        try:
            stats = db.query(UserStats).filter(
                UserStats.user_id == str(user_id)
            ).order_by(UserStats.usage_count.desc()).limit(10).all()
        except Exception as db_error:
            logger.error(f"Database error in get chart stats: {str(db_error)}")
            return PlainTextResponse(f"error|database_error|Failed to retrieve chart statistics", status_code=500)
        
        if not stats:
            chart_data = "LABELS:\nDATA:"
            return PlainTextResponse(f"success|{chart_data}|No chart data available")
        
        labels = [stat.ai_type for stat in stats]
        data = [stat.usage_count for stat in stats]
        
        chart_data = f"LABELS:{','.join(labels)}\nDATA:{','.join(map(str, data))}"
        
        return PlainTextResponse(f"success|{chart_data}|Chart data retrieved")
        
    except Exception as e:
        print(f"GET CHART STATS ERROR: {str(e)}")
        return PlainTextResponse(f"error|chart_failed|{str(e)}", status_code=500)

# Legacy endpoints - backward compatibility uchun
@app.get("/conversations")
async def get_conversations_legacy(user_id: str, db: Session = Depends(get_db)):
    """Legacy endpoint - conversations"""
    return await get_user_chats(user_id, db)

@app.get("/api/conversations")
async def api_get_conversations_legacy(user_id: str, db: Session = Depends(get_db)):
    """Legacy API endpoint - conversations"""
    return await get_user_chats(user_id, db)

# OPTIONS handlers - CORS uchun
@app.options("/api/chats")
async def options_chats():
    """CORS OPTIONS handler for /api/chats"""
    return PlainTextResponse("", status_code=200)

@app.options("/api/chats/{chat_id}")
async def options_chat():
    """CORS OPTIONS handler for chat operations"""
    return PlainTextResponse("", status_code=200)

@app.options("/api/chats/user/{user_id}/all")
async def options_all_chats():
    """CORS OPTIONS handler for delete all chats"""
    return PlainTextResponse("", status_code=200)

@app.options("/api/chats/{chat_id}/messages")
async def options_chat_messages():
    """CORS OPTIONS handler for chat messages"""
    return PlainTextResponse("", status_code=200)

@app.options("/api/stats/user/{user_id}")
async def options_user_stats():
    """CORS OPTIONS handler for user stats"""
    return PlainTextResponse("", status_code=200)

@app.options("/api/stats/chart/user/{user_id}")
async def options_chart_stats():
    """CORS OPTIONS handler for chart stats"""
    return PlainTextResponse("", status_code=200)

@app.options("/auth/google")
async def options_google_auth():
    """CORS OPTIONS handler for Google auth"""
    return PlainTextResponse("", status_code=200)

@app.options("/api/auth/google")
async def options_api_google_auth():
    """CORS OPTIONS handler for API Google auth"""
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

# AI ID endpoints uchun OPTIONS
@app.options("/api/ai/{ai_id}")
async def options_ai_by_id():
    """CORS OPTIONS handler for AI by ID"""
    return PlainTextResponse("", status_code=200)

# FIXED: Error handlers
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

# FIXED: Health check with database - proper text() usage
@app.get("/api/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    """Database bilan birga health check"""
    try:
        # FIXED: Use text() for raw SQL
        result = db.execute(text("SELECT 1")).fetchone()
        return PlainTextResponse("success|healthy|Database connection OK")
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return PlainTextResponse(f"error|db_error|Database connection failed: {str(e)}", status_code=500)

# AI modules status
@app.get("/api/ai/status")
async def ai_modules_status():
    """AI modullarining holati"""
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
        print(f"AI STATUS ERROR: {str(e)}")
        return PlainTextResponse(f"error|status_failed|{str(e)}", status_code=500)

# Development endpoints (faqat DEBUG mode da)
if os.getenv("DEBUG", "False").lower() == "true":
    @app.get("/api/debug/tables")
    async def debug_tables(db: Session = Depends(get_db)):
        """Debug: Database tables info"""
        try:
            tables_info = []
            
            users_count = db.query(User).count()
            tables_info.append(f"users:{users_count}")
            
            conversations_count = db.query(Conversation).count()
            tables_info.append(f"conversations:{conversations_count}")
            
            messages_count = db.query(Message).count()
            tables_info.append(f"messages:{messages_count}")
            
            stats_count = db.query(UserStats).count()
            tables_info.append(f"user_stats:{stats_count}")
            
            result = "\n".join(tables_info)
            return PlainTextResponse(f"success|{result}|Tables info retrieved")
            
        except Exception as e:
            return PlainTextResponse(f"error|debug_failed|{str(e)}", status_code=500)

    @app.get("/api/debug/env")
    async def debug_env():
        """Debug: Environment variables (maskirovka qilingan)"""
        try:
            env_info = []
            
            important_vars = [
                "DATABASE_URL", "DB_HOST", "DB_USER", "DB_NAME", "DB_PORT",
                "OPENAI_API_KEY", "GOOGLE_CLIENT_ID", "JWT_SECRET", 
                "HOST", "PORT", "DEBUG", "CORS_ORIGINS"
            ]
            
            for var in important_vars:
                value = os.getenv(var, "NOT_SET")
                if var in ["DATABASE_URL", "OPENAI_API_KEY", "JWT_SECRET", "DB_PASSWORD", "GOOGLE_CLIENT_SECRET"]:
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

# FIXED: Logging middleware - proper error handling
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Request logging middleware - 422 xatolarini batafsil log qilish"""
    start_time = datetime.utcnow()
    
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        response = await call_next(request)
    except Exception as e:
        print(f"❌ MIDDLEWARE ERROR: {request.method} {request.url.path} - {str(e)} - IP: {client_ip}")
        return PlainTextResponse("error|server_error|Internal server error", status_code=500)
    
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    # 422 xatolarini alohida log qilish
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
    """Server ishga tushganda"""
    print("🚀 AI Universe Server starting...")
    print(f"📊 Total AI assistants loaded: {len(AI_ASSISTANTS)}")
    active_ais = [name for name, ai in AI_ASSISTANTS.items() if not isinstance(ai, DummyAI)]
    dummy_ais = [name for name, ai in AI_ASSISTANTS.items() if isinstance(ai, DummyAI)]
    print(f"✅ Active AI modules: {len(active_ais)} - {', '.join(active_ais[:5])}{'...' if len(active_ais) > 5 else ''}")
    print(f"⚠️ Dummy AI modules: {len(dummy_ais)} - {', '.join(dummy_ais[:5])}{'...' if len(dummy_ais) > 5 else ''}")
    print("🌐 Server ready to serve requests!")
    
    # Database connection test
    try:
        if SessionLocal:
            db = SessionLocal()
            # FIXED: Use text() for raw SQL
            db.execute(text("SELECT 1"))
            db.close()
            print("✅ Database connection test passed")
        else:
            print("⚠️ Database not available - using fallback mode")
    except Exception as e:
        print(f"❌ Database connection test failed: {str(e)}")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Server to'xtashda"""
    print("🛑 AI Universe Server shutting down...")
    print("👋 Goodbye!")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))  # FIXED: Default port 8080
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