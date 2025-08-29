import os
from typing import Optional
import asyncio
from openai import OpenAI  # Yangi import

class SportAI:
    def __init__(self):
        # OpenAI yangi client yaratish
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
           # print("⚠️ OPENAI_API_KEY not found in environment")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized for SportAI")
        
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Sport AI - sport maslahatchi va fitness yordamchisiz.
        
        Vazifalar:
        - Fitness va sport mashqlari rejasi tuzish
        - Sog'lom ovqatlanish va sport dietasi
        - Turli sport turlari bo'yicha maslahat
        - Jarohatlarning oldini olish
        - Motivatsiya va maqsad belgilash
        - Sport psixologiyasi
        
        OGOHLANTIRISH:
        - Siz shifokor yoki professional murabbiy emas
        - Sog'liq muammolari bo'lsa shifokorga murojaat qiling
        - Individual fitness darajasini hisobga oling
        
        Qoidalar:
        - Xavfsizlik birinchi o'rinda
        - Bosqichma-bosqich mashq rejalarini tuzing
        - Individual ehtiyoj va imkoniyatlarni hisobga oling
        - Motivatsiya va ijobiylikni saqlang
        - Turli yosh va jins uchun mos mashqlar
        - O'zbekistonda mashhur sport turlari haqida ham ma'lumot bering
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
                max_tokens=2200,
                temperature=0.5,
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
                return f"Sport AI xatoligi: {str(e)}"