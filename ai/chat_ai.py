from openai import OpenAI  # Yangi import
import os
from typing import Optional
import asyncio

class ChatAI:
    def __init__(self):
        # OpenAI yangi client yaratish
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ OPENAI_API_KEY not found in environment")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized for ChatAI")
        
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Chat AI - umumiy yordamchisiz. Siz har qanday mavzuda suhbatlashishingiz va yordam berishingiz mumkin.
        
        Sizning vazifangiz:
        - Har qanday savolga aniq va tushunarli javob berish
        - Foydalanuvchi bilan do'stona muloqot qilish
        - Har doim foydali va ijobiy bo'lish
        - O'zbek, rus, ingliz tillarida javob berish
        
        Qoidalar:
        - Har doim hurmatli va professional bo'ling
        - Noto'g'ri ma'lumot bermaslik
        - Agar biror narsani bilmasangiz, ochiq aytib bering
        - Zararli yoki nomaqbul kontentni rad eting
        """
    
    async def get_response(self, user_message: str) -> str:
        """Get response from OpenAI GPT model using new API"""
        try:
            if not self.client:
                return "Kechirasiz, OpenAI service hozircha mavjud emas. OPENAI_API_KEY sozlanmagan."
            
            # Yangi API sintaksisi
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=2000,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            error_msg = str(e).lower()
            if "api key" in error_msg:
                return "Kechirasiz, OpenAI API key bilan muammo bor. Administrator bilan bog'laning."
            elif "quota" in error_msg or "limit" in error_msg:
                return "Kechirasiz, API limiti tugagan. Iltimos, keyinroq qaytadan urinib ko'ring."
            elif "model" in error_msg:
                return "Kechirasiz, so'ralgan AI model mavjud emas."
            else:
                return f"Kechirasiz, xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring. Xato: {str(e)}"
    
    def get_ai_info(self) -> dict:
        """Get AI information"""
        return {
            "name": "Chat AI",
            "description": "Umumiy savollar va har kunlik yordamchi. Har qanday mavzuda suhbatlashing.",
            "category": "general",
            "icon": "💬",
            "features": [
                "Har qanday mavzuda suhbat",
                "Ko'p tilda muloqot",
                "Tezkor javob",
                "24/7 mavjud"
            ]
        }