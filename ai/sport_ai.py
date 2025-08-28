# ai/sport_ai.py
import openai
import os
from typing import Optional
import asyncio

class SportAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
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
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=2200,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Sport AI xatoligi: {str(e)}"