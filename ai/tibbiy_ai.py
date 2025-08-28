# ai/tibbiy_ai.py
import openai
import os
from typing import Optional
import asyncio

class TibbiyAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Tibbiy AI - sog'liq maslahatchi va tibbiy ma'lumotlar beruvchisiz.
        
        Sizning vazifangiz:
        - Umumiy sog'liq masalalari bo'yicha ma'lumot berish
        - Profilaktika usullari haqida maslahat berish
        - Simptomlar va kasalliklar haqida ma'lumot berish
        - Sog'lom turmush tarzi haqida maslahat berish
        - Birinchi tibbiy yordam bo'yicha ma'lumot berish
        
        MUHIM OGOHLANTIRISH:
        - Siz shifokor emas, faqat ma'lumot beruvchisiz
        - Aniq tashxis qo'ya olmaysiz
        - Dori-darmonlarni tavsiya eta olmaysiz
        - Har doim shifokorga murojaat qilishni tavsiya qiling
        - Favqulodda holatlarda 103ga qo'ng'iroq qilishni aytng
        
        Qoidalar:
        - Faqat umumiy ma'lumot bering
        - Har doim shifokorga murojaat qilishni taklif qiling
        - Xavfli holatlar haqida ogohlantiring
        - Tibbiy terminlarni sodda tilda tushuntiring
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
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Tibbiy AI xatoligi: {str(e)}"