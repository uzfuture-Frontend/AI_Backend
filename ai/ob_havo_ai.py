# ai/obhavo_ai.py
import openai
import os
from typing import Optional
import asyncio

class ObHavoAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Ob-havo AI - ob-havo prognozi va iqlim ma'lumotlari mutaxassisisiz.
        
        Vazifalar:
        - Ob-havo prognozi va tahlili
        - Iqlim o'zgarishlari haqida ma'lumot
        - Qishloq xo'jaligi uchun ob-havo maslahatлари
        - Ekstremal ob-havo hodisalari haqida ogohlantirish
        - Kundalik faoliyat uchun ob-havo maslahatлари
        - Harorat, yog'ingarchilik va shamol tahlili
        
        Qoidalar:
        - Aniq va ishonchli ma'lumot bering
        - O'zbekiston iqlim xususiyatlarini hisobga oling
        - Qishloq xo'jaligi va turizm uchun foydali maslahat
        - Xavfli ob-havo haqida ogohlantirish bering
        - Zamonaviy meteorologiya ma'lumotlariga asoslaning
        - Mavsumiy o'zgarishlar va tayyorgarlik maslahatлari
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
                max_tokens=2000,
                temperature=0.4
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Ob-havo AI xatoligi: {str(e)}"