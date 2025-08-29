import os
from typing import Optional
import asyncio
from openai import OpenAI  # Yangi import

class MoliyaAI:
    def __init__(self):
        # OpenAI yangi client yaratish
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ OPENAI_API_KEY not found in environment")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized for MoliyaAI")
        
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Moliya AI - moliyaviy maslahatchi va investitsiya yordamchisiz.
        
        Vazifalar:
        - Pul boshqaruvi
        - Investitsiya strategiyalari
        - Byudjet rejalashtirish
        - Tejamkorlik usullari
        - O'zbekiston moliya bozori
        
        OGOHLANTIRISH: Bu moliyaviy maslahat emas, faqat ta'limiy ma'lumot
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
                temperature=0.4,
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
                return f"Moliya AI xatoligi: {str(e)}"