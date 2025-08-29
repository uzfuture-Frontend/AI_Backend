from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid
import structlog
import openai
import jwt
import json

# Load environment variables
load_dotenv()

# OpenAI global config
openai.api_key = os.getenv("OPENAI_API_KEY")
api_key = os.getenv("OPENAI_API_KEY")
print(f"DEBUG: API Key mavjud: {api_key is not None}")
print(f"DEBUG: API Key uzunligi: {len(api_key) if api_key else 0}")
print(f"DEBUG: API Key boshlanishi: {api_key[:15] if api_key else 'None'}...")

if api_key:
    openai.api_key = api_key
    print("✅ OpenAI API key o'rnatildi")
else:
    print("❌ OPENAI_API_KEY environment variable topilmadi!")

# Logger
logger = structlog.get_logger()

# Database setup - MySQL uchun tuzatilgan
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Railway MySQL URL - Environment variables'dan qurish
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "XRCcOHObEeRtWRSJzlFzyWZNltFjgjKi")
    db_host = os.getenv("DB_HOST", "turntable.proxy.rlwy.net")
    db_port = os.getenv("DB_PORT", "49805")
    db_name = os.getenv("DB_NAME", "railway")
    DATABASE_URL = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    print("DATABASE_URL environment variable yo'q, default MySQL ishlatilmoqda")

# MySQL uchun SQLAlchemy URL ni to'g'rilash
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://")

print(f"Database URL configured: {DATABASE_URL.split('@')[0]}@***")

try:
    engine = create_engine(
        DATABASE_URL, 
        pool_pre_ping=True,
        pool_recycle=3600,  # MySQL connection timeout uchun
        echo=False,
        connect_args={"charset": "utf8mb4"}  # UTF-8 uchun
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    print("Database engine yaratildi")
    
except Exception as e:
    logger.error(f"MySQL database setup failed: {str(e)}")
    print(f"MySQL ulanish xatosi: {str(e)}")

# Models
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

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables setup completed")
    print("MySQL jadvallari muvaffaqiyatli yaratildi")
except Exception as e:
    logger.error("Database setup failed", error=str(e))
    print(f"Jadval yaratishda xato: {str(e)}")

# FastAPI app
app = FastAPI(
    title="AI Universe - Professional AI Platform",
    description="25 ta professional AI xizmati bir platformada",
    version="1.0.0"
)

# CORS middleware - Environment variables'dan olish
cors_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://www.aiuniverse.uz",
    "https://www.aiuniverse.uz",
    "http://aiuniverse.uz", 
    "https://aiuniverse.uz",
    "https://*.railway.app",
    "https://aiuniverse-production.up.railway.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI assistants import - Xatolikdan himoyalanish
class DummyAI:
    """AI modullari mavjud bo'lmaganda ishlatish uchun"""
    async def get_response(self, message: str) -> str:
        return f"Sizning xabaringiz: '{message}' qabul qilindi. AI moduli hozircha ishlamayapti, lekin tez orada faollashadi!"

AI_ASSISTANTS = {}

# AI modulllarini xavfsiz import qilish
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
        print(f"⚠️ {ai_key} AI module not found, using dummy")
        AI_ASSISTANTS[ai_key] = DummyAI()
    except Exception as e:
        print(f"⚠️ {ai_key} AI module error: {str(e)}, using dummy")
        AI_ASSISTANTS[ai_key] = DummyAI()

print(f"Total AI assistants loaded: {len(AI_ASSISTANTS)}")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Root endpoints
@app.get("/")
async def root():
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

# Auth endpoints
@app.post("/auth/google")
async def google_auth(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        
        # Ikkala formatni qo'llab-quvvatlash
        if 'token' in body:
            # JWT tokenni decode qilish
            try:
                # JWT tokenni verify qilmasdan decode qilish (faqat payload olish uchun)
                payload = jwt.decode(body['token'], options={"verify_signature": False})
                
                email = payload.get('email')
                name = payload.get('name')
                picture = payload.get('picture', '')
                google_id = payload.get('sub')
            except Exception as e:
                logger.error(f"JWT decode error: {str(e)}")
                return PlainTextResponse("error|invalid_token|Invalid JWT token", status_code=400)
        
        elif 'user_data' in body:
            # Direct user data format
            user_data = body['user_data']
            email = user_data.get('email')
            name = user_data.get('name') 
            picture = user_data.get('picture', '')
            google_id = user_data.get('google_id')
        
        else:
            # Simple format
            email = body.get("email")
            name = body.get("name")
            picture = body.get("picture", "")
            google_id = body.get("google_id") or body.get("sub")
        
        if not email or not name:
            return PlainTextResponse("error|missing_data|Email and name are required", status_code=400)
        
        # Bazadan foydalanuvchini qidirish
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Yangi foydalanuvchi yaratish
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                name=name,
                picture=picture,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            logger.info(f"New user created: {email}")
        else:
            # Mavjud foydalanuvchi ma'lumotlarini yangilash
            user.name = name
            user.picture = picture
            db.commit()
            logger.info(f"Existing user updated: {email}")
        
        # Response format: success|user_info_json|message
        user_info = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "google_id": google_id
        }
        
        return PlainTextResponse(f"success|{json.dumps(user_info)}|User authenticated successfully")
        
    except Exception as e:
        logger.error("Google auth failed", error=str(e))
        return PlainTextResponse(f"error|auth_failed|{str(e)}", status_code=500)

@app.post("/api/auth/google") 
async def api_google_auth(request: Request, db: Session = Depends(get_db)):
    return await google_auth(request, db)

# Chat processing functions
async def process_chat(ai_assistant, message: str, user_id: str, conversation_id: str | None, ai_type: str, db: Session):
    try:
        if not user_id:
            return PlainTextResponse("error|missing_user_id|User ID is required", status_code=400)
        if not message:
            return PlainTextResponse("error|missing_message|Message is required", status_code=400)
        
        ai_response = await ai_assistant.get_response(message)
        
        # Yangi suhbat yaratish
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                ai_type=ai_type,
                title=message[:50] + "..." if len(message) > 50 else message
            )
            db.add(conversation)
        
        # Xabarni saqlash
        message_entry = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=user_id,
            content=message,
            ai_response=ai_response
        )
        db.add(message_entry)
        
        # Statistikani yangilash
        stats = db.query(UserStats).filter(
            UserStats.user_id == user_id,
            UserStats.ai_type == ai_type
        ).first()
        
        if not stats:
            stats = UserStats(
                id=str(uuid.uuid4()),
                user_id=user_id,
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
    except Exception as e:
        logger.error(f"Handle chat request failed for {ai_type}", error=str(e))
        return PlainTextResponse(f"error|request_failed|{str(e)}", status_code=500)

# AI ID ga asosan routing
@app.post("/api/ai/{ai_id}")
async def api_chat_by_id(ai_id: int, request: Request, db: Session = Depends(get_db)):
    """Frontend /api/ai/1 formatidagi so'rovlar uchun"""
    try:
        # AI ID ni AI type ga o'girish
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

# Chat endpoints for all AI types - DUPLIKATLAR O'CHIRILDI
chat_endpoints = [
    "chat", "tarjimon", "blockchain", "tadqiqot", "smart_energy", "dasturlash",
    "tibbiy", "talim", "biznes", "huquq", "psixologik", "moliya", "sayohat",
    "oshpazlik", "ijod", "musiqa", "sport", "obhavo", "yangiliklar", "matematik",
    "fan", "ovozli", "arxitektura", "ekologiya", "oyun"
]

# Dynamic endpoint creation - Bir martalik
for ai_type in chat_endpoints:
    # Closure yaratish uchun default parameter ishlatamiz
    def create_handler(ai_type_name):
        async def handler(request: Request, db: Session = Depends(get_db)):
            return await handle_chat_request(request, ai_type_name, db)
        return handler
    
    # Har bir AI type uchun endpoint yaratish
    handler = create_handler(ai_type)
    app.add_api_route(f"/chat/{ai_type}", handler, methods=["POST"])
    app.add_api_route(f"/api/chat/{ai_type}", handler, methods=["POST"])

# Chat management endpoints
@app.post("/api/chats")
async def create_or_update_chat(request: Request, db: Session = Depends(get_db)):
    """Chat yaratish yoki yangilash"""
    try:
        body = await request.json()
        chat_id = body.get("id") or str(uuid.uuid4())
        title = body.get("title", "New Chat")
        user_id = str(body.get("user_id", ""))
        ai_type = body.get("ai_type", "chat")
        
        print(f"CREATE/UPDATE CHAT: {chat_id}, user: {user_id}, type: {ai_type}")
        
        conversation = db.query(Conversation).filter(Conversation.id == chat_id).first()
        
        if not conversation:
            conversation = Conversation(
                id=chat_id,
                user_id=user_id,
                ai_type=ai_type,
                title=title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(conversation)
            print(f"NEW CHAT CREATED: {chat_id}")
        else:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            print(f"CHAT UPDATED: {chat_id}")
        
        db.commit()
        
        # Chat ma'lumotlarini qaytarish
        chat_data = {
            "id": conversation.id,
            "ai_type": conversation.ai_type,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat()
        }
        
        return PlainTextResponse(f"success|{json.dumps(chat_data)}|Chat saved successfully")
        
    except Exception as e:
        print(f"CREATE CHAT ERROR: {str(e)}")
        return PlainTextResponse(f"error|create_failed|{str(e)}", status_code=500)

@app.put("/api/chats/{chat_id}")
async def update_chat(chat_id: str, request: Request, db: Session = Depends(get_db)):
    """Chat yangilash"""
    try:
        body = await request.json()
        title = body.get("title", "New Chat")
        user_id = str(body.get("user_id", ""))
        ai_type = body.get("ai_type", "chat")
        
        print(f"UPDATE CHAT: {chat_id}, user: {user_id}, type: {ai_type}")
        
        conversation = db.query(Conversation).filter(Conversation.id == chat_id).first()
        
        if not conversation:
            conversation = Conversation(
                id=chat_id,
                user_id=user_id,
                ai_type=ai_type,
                title=title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(conversation)
            print(f"NEW CHAT CREATED: {chat_id}")
        else:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            print(f"CHAT UPDATED: {chat_id}")
        
        db.commit()
        return PlainTextResponse("success|chat_saved|Chat saved successfully")
        
    except Exception as e:
        print(f"UPDATE CHAT ERROR: {str(e)}")
        return PlainTextResponse(f"error|update_failed|{str(e)}", status_code=500)

@app.get("/api/chats/user/{user_id}")
async def get_user_chats(user_id: str, db: Session = Depends(get_db)):
    """User ning barcha chatlari"""
    try:
        print(f"GET USER CHATS: {user_id}")
        
        conversations = db.query(Conversation).filter(
            Conversation.user_id == str(user_id)
        ).order_by(Conversation.updated_at.desc()).all()
        
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
    """Chat tafsilotlari va xabarlar"""
    try:
        print(f"GET CHAT DETAILS: {chat_id}")
        
        conversation = db.query(Conversation).filter(Conversation.id == chat_id).first()
        
        if not conversation:
            return PlainTextResponse("error|chat_not_found|Chat not found", status_code=404)
        
        messages = db.query(Message).filter(
            Message.conversation_id == chat_id
        ).order_by(Message.timestamp.asc()).all()
        
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
    """Chat xabarlarini olish"""
    try:
        print(f"GET CHAT MESSAGES: {chat_id}")
        
        conversation = db.query(Conversation).filter(Conversation.id == chat_id).first()
        
        if not conversation:
            print(f"Chat not found: {chat_id}")
            return PlainTextResponse("error|chat_not_found|Chat not found", status_code=404)
        
        messages = db.query(Message).filter(
            Message.conversation_id == chat_id
        ).order_by(Message.timestamp.asc()).all()
        
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
        
        conversation = db.query(Conversation).filter(Conversation.id == chat_id).first()
        
        if not conversation:
            return PlainTextResponse("error|chat_not_found|Chat not found", status_code=404)
        
        if user_id and conversation.user_id != str(user_id):
            return PlainTextResponse("error|unauthorized|Unauthorized to delete this chat", status_code=403)
        
        db.query(Message).filter(Message.conversation_id == chat_id).delete()
        db.delete(conversation)
        db.commit()
        
        print(f"CHAT DELETED: {chat_id}")
        return PlainTextResponse("success|chat_deleted|Chat deleted successfully")
        
    except Exception as e:
        print(f"DELETE CHAT ERROR: {str(e)}")
        return PlainTextResponse(f"error|delete_failed|{str(e)}", status_code=500)

@app.delete("/api/chats/user/{user_id}/all")
async def delete_all_user_chats(user_id: int, db: Session = Depends(get_db)):
    """User ning barcha chatlarini o'chirish"""
    try:
        print(f"DELETE ALL CHATS FOR USER: {user_id}")
        
        conversations = db.query(Conversation).filter(
            Conversation.user_id == str(user_id)
        ).all()
        
        if not conversations:
            print(f"No chats found for user {user_id}")
            return PlainTextResponse("error|no_chats|No chats found to delete", status_code=404)
        
        conversation_ids = [conv.id for conv in conversations]
        
        for conv_id in conversation_ids:
            db.query(Message).filter(Message.conversation_id == conv_id).delete()
        
        db.query(Conversation).filter(
            Conversation.user_id == str(user_id)
        ).delete()
        
        db.commit()
        
        print(f"ALL CHATS DELETED FOR USER: {user_id} ({len(conversations)} chats)")
        return PlainTextResponse(f"success|all_chats_deleted|{len(conversations)} chats deleted successfully")
        
    except Exception as e:
        print(f"DELETE ALL CHATS ERROR: {str(e)}")
        return PlainTextResponse(f"error|delete_all_failed|{str(e)}", status_code=500)

# Stats endpoints
@app.get("/api/stats/user/{user_id}")
async def get_user_stats_api(user_id: int, db: Session = Depends(get_db)):
    """User statistikalari"""
    try:
        print(f"GET USER STATS: {user_id}")
        
        stats = db.query(UserStats).filter(
            UserStats.user_id == str(user_id)
        ).order_by(UserStats.usage_count.desc()).all()
        
        total_messages = sum(stat.usage_count for stat in stats)
        total_conversations = db.query(Conversation).filter(
            Conversation.user_id == str(user_id)
        ).count()
        
        most_used_ai = stats[0].ai_type if stats else "None"
        
        if not stats:
            print(f"No stats found for user {user_id}")
            return PlainTextResponse("success|no_stats|No statistics available yet")
        
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
        return PlainTextResponse(f"error|stats_failed|{str(e)}", status_code=500)

@app.get("/api/stats/chart/user/{user_id}")
async def get_user_chart_stats_api(user_id: int, db: Session = Depends(get_db)):
    """User chart statistikalari"""
    try:
        print(f"GET USER CHART STATS: {user_id}")
        
        stats = db.query(UserStats).filter(
            UserStats.user_id == str(user_id)
        ).order_by(UserStats.usage_count.desc()).limit(10).all()
        
        if not stats:
            return PlainTextResponse("success|no_chart_data|No chart data available")
        
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
    
    # OPTIONS handlers yaratish
    options_handler = create_options_handler()
    app.add_api_route(f"/chat/{ai_type}", options_handler, methods=["OPTIONS"])
    app.add_api_route(f"/api/chat/{ai_type}", options_handler, methods=["OPTIONS"])

# AI ID endpoints uchun OPTIONS
@app.options("/api/ai/{ai_id}")
async def options_ai_by_id():
    """CORS OPTIONS handler for AI by ID"""
    return PlainTextResponse("", status_code=200)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return PlainTextResponse("error|not_found|Endpoint not found", status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error("Internal server error", error=str(exc))
    return PlainTextResponse("error|server_error|Internal server error", status_code=500)

# Health check with database
@app.get("/api/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    """Database bilan birga health check"""
    try:
        # Simple query to test DB connection
        result = db.execute("SELECT 1").fetchone()
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
            
            # Users table
            users_count = db.query(User).count()
            tables_info.append(f"users:{users_count}")
            
            # Conversations table  
            conversations_count = db.query(Conversation).count()
            tables_info.append(f"conversations:{conversations_count}")
            
            # Messages table
            messages_count = db.query(Message).count()
            tables_info.append(f"messages:{messages_count}")
            
            # UserStats table
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
            
            # Muhim environment variables
            important_vars = [
                "DATABASE_URL", "DB_HOST", "DB_USER", "DB_NAME", "DB_PORT",
                "OPENAI_API_KEY", "GOOGLE_CLIENT_ID", "JWT_SECRET", 
                "HOST", "PORT", "DEBUG", "CORS_ORIGINS"
            ]
            
            for var in important_vars:
                value = os.getenv(var, "NOT_SET")
                if var in ["DATABASE_URL", "OPENAI_API_KEY", "JWT_SECRET", "DB_PASSWORD", "GOOGLE_CLIENT_SECRET"]:
                    # Sensitive ma'lumotlarni mask qilish
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

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Server to'xtashda"""
    print("🛑 AI Universe Server shutting down...")
    print("👋 Goodbye!")

if __name__ == "__main__":
    import uvicorn
    
    # Environment variables'dan server config olish
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
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
        reload=debug,  # Faqat debug mode da reload
        access_log=True
    )