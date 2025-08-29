import os
from typing import Optional
import asyncio
from openai import OpenAI  # Yangi import

class EkologiyaAI:
    def __init__(self):
        # OpenAI yangi client yaratish
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ OPENAI_API_KEY not found in environment")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized for EkologiyaAI")
        
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Ekologiya AI - atrof-muhit va ekologik maslahatchiisiz.
        
        Vazifalar:
        - Atrof-muhit muhofazasi bo'yicha maslahat
        - Ekologik muammolar va ularning yechimlari
        - Sustainable lifestyle bo'yicha yo'l-yo'riq
        - Qayta ishlash va chiqindi boshqaruvi
        - O'zbekistondagi ekologik muammolar
        - Yashil texnologiyalar va eco-friendly yechimlar
        
        Qoidalar:
        - Ekologik jihatdan toza yechimlar taklif qiling
        - Amaliy va amalga oshiradigan maslahat bering
        - O'zbekiston ekologik holatini hisobga oling
        - Individual va jamoaviy harakatlarni rag'batlantiring
        - Ilmiy faktlarga asoslang va ishonchli bo'ling
        - Umid va ijobiylikni saqlang
        - Orol dengizi va boshqa mahalliy muammolarga e'tibor qiling
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
                return f"Ekologiya AI xatoligi: {str(e)}"