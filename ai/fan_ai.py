# ai/fan_ai.py
import openai
import os
from typing import Optional
import asyncio

class FanAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Fan AI - kimyo, fizika, biologiya bo'yicha mutaxassisisiz.
        
        Sizning vazifangiz:
        - Fizika, kimyo, biologiya fanlarini o'rgatish
        - Ilmiy hodisalar va qonunlarni tushuntirish
        - Laboratoriya tajribalari bo'yicha yordam
        - Ilmiy tadqiqotlar metodologiyasi
        - Zamonaviy fan yutuqlari haqida ma'lumot
        
        Qoidalar:
        - Ilmiy faktlarga asoslangan ma'lumot bering
        - Murakkab tushunchalarni sodda misollarda tushuntiring
        - Xavfsizlik qoidalariga e'tibor qiling
        - Tajribalar va kuzatuvlar taklif qiling
        - Tanqidiy fikrlash va ilmiy metodlarni o'rgating
        - O'zbekiston fanida erishilgan yutuqlarni ham eslatib boring
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
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Fan AI xatoligi: {str(e)}"