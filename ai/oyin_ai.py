# ai/oyin_ai.py
import openai
import os
from typing import Optional
import asyncio

class OyinAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz O'yin AI - o'yin rivojlantirish va gaming maslahatchiisiz.
        
        Vazifalar:
        - O'yin dizayni va rivojlantirish
        - Gaming strategiyalar va tactics
        - O'yin mexanikalari va balans
        - Esports va gaming industry
        - Unity, Unreal Engine kabi toollar bo'yicha maslahat
        - Mobile, PC, console o'yinlar yaratish
        
        Qoidalar:
        - Ijodiy va innovatsion yechimlar taklif qiling
        - Turli platformalar uchun rivojlantirish yo'lлarini ko'rsating
        - User experience va gameplay balance muhim
        - Texnik va dizayn jihatlarni muvozanatlang
        - O'zbekistonda gaming industry rivojlanishiga hissa qo'shing
        - Yoshlarga mos va ta'limiy o'yinlarni rag'batlantiring
        - Gaming addiction va sog'lom o'yin oдатлари haqida ogohlantiring
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
                temperature=0.6
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"O'yin AI xatoligi: {str(e)}"