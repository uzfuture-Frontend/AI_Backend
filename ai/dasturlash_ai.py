# ai/dasturlash_ai.py
import openai
import os
from typing import Optional
import asyncio

class DasturlashAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
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
        - Toza va tushunchalي kod yozing
        - Kodga izohlar qo'shing
        - Xavfsizlik jihatlarini hisobga oling
        - Performance optimizatsiya qiling
        - Testing strategiyalarini tavsiya eting
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
                max_tokens=2500,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Dasturlash AI xatoligi: {str(e)}"