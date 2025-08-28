# ai/huquq_ai.py (to'liq versiya)  
import openai
import os
from typing import Optional
import asyncio

class HuquqAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Huquq AI - huquqiy maslahatchi va qonunchilik yordamchisisiz.
        
        Vazifalar:
        - O'zbekiston qonunlari haqida ma'lumot
        - Huquqiy hujjatlar tayyorlash
        - Fuqarolik huquqlari
        - Yuridik jarayonlar tushuntirish
        
        OGOHLANTIRISH: Professional yurist emas, faqat ma'lumot beruvchi
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
            return f"Huquq AI xatoligi: {str(e)}"
