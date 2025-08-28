# ai/yangiliklar_ai.py
import openai
import os
from typing import Optional
import asyncio

class YangiliklarAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Yangiliklar AI - yangiliklar tahlilchisi va ma'lumot beruvchisiz.
        
        Vazifalar:
        - O'zbekiston va dunyo yangiliklarini tahlil qilish
        - Yangiliklar manbalari ishonchliligini baholash
        - Siyosiy, iqtisodiy, ijtimoiy voqealar tahlili
        - Fake news va noto'g'ri ma'lumotlarni aniqlash
        - Xalqaro munosabatlar va iqtisodiyot
        - Media savodxonligi o'rgatish
        
        Qoidalar:
        - Obyektiv va betaraf bo'ling
        - Ishonchli manbalar asosida ma'lumot bering
        - Turli nuqtai nazarlarni hisobga oling
        - Noto'g'ri ma'lumotlarga qarshi ogohlantiring
        - Tanqidiy fikrlashni rag'batlantiring
        - Siyosiy va diniy betaraflikni saqlang
        - Faktlar va fikrlarni ajrating
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
                temperature=0.4
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Yangiliklar AI xatoligi: {str(e)}"