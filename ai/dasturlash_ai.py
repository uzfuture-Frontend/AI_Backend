import os
from typing import Optional
import asyncio
from openai import OpenAI  # Yangi import

class DasturlashAI:
    def __init__(self):
        # OpenAI yangi client yaratish
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ OPENAI_API_KEY not found in environment")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized for DasturlashAI")
        
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Dasturlash AI - dasturlash yordamchisi va kod yozuvchisiz.
        
        Sizning vazifangiz:
        - Har qanday dasturlash tilida yordam berish
        - Kod yozish va debug qilish
        - Algoritmlar va ma'lumotlar strukturasi bo'yicha yordam
        - Best practices va clean code yozish
        - Web, mobile, desktop ilovalar yaratish
        
        Qoidalar:
        - Toza va tushunchali kod yozing
        - Kodga izohlar qo'shing
        - Xavfsizlik jihatlarini hisobga oling
        - Performance optimizatsiya qiling
        - Testing strategiyalarini tavsiya eting
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
                max_tokens=2500,
                temperature=0.2,
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
                return f"Dasturlash AI xatoligi: {str(e)}"