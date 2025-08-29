import os
from typing import Optional
import asyncio
from openai import OpenAI  # Yangi import

class MatematikAI:
    def __init__(self):
        # OpenAI yangi client yaratish
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
           # print("⚠️ OPENAI_API_KEY not found in environment")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized for MatematikAI")
        
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Matematik AI - matematik masalalar yechuvchi va formula ustasisiz.
        
        Sizning vazifangiz:
        - Matematik masalalarni yechish va tushuntirish
        - Formulalar va qoidalarni o'rgatish
        - Geometriya, algebra, analiz bo'yicha yordam
        - Matematik fikrlashni rivojlantirish
        - Amaliy matematik masalalarda yordam
        
        Qoidalar:
        - Bosqichma-bosqich yechimlar ko'rsating
        - Har bir qadamni tushuntiring
        - Formulalarni va qoidalarni aniq ko'rsating
        - Grafiklar va diagrammalar taklif qiling
        - Misollar va mashqlar bering
        - Matematik tilni sodda o'zbek tilida tushuntiring
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
                return f"Matematik AI xatoligi: {str(e)}"