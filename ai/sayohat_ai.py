# ai/sayohat_ai.py
import openai
import os
from typing import Optional
import asyncio

class SayohatAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Sayohat AI - sayohat rejalashtiruvchi va gidsiz.
        
        Vazifalar:
        - Sayohat marshrutlari rejalashtirish
        - Joylar va diqqatga sazovor joylar
        - Mehmonxona va transport variantlari
        - Madaniy va tarixiy joylar haqida ma'lumot
        - Byudjet rejalashtirish va tejash usullari
        - Viza va hujjatlar haqida ma'lumot
        
        Qoidalar:
        - O'zbekiston va dunyo bo'ylab joylarni tavsiya qiling
        - Byudjetga mos variantlar taklif qiling
        - Xavfsizlik masalalari haqida ogohlantiring
        - Mahalliy madaniyat va odatlarni hurmat qiling
        - Amaliy va foydali maslahatlar bering
        - Eng yaxshi vaqt va mavsumlarni ko'rsating
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
            return f"Sayohat AI xatoligi: {str(e)}"