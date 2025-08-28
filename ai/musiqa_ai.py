# ai/musiqa_ai.py
import openai
import os
from typing import Optional
import asyncio

class MusiqaAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Musiqa AI - musiqa yaratish va tahlil mutaxassisisiz.
        
        Vazifalar:
        - Musiqa nazariyasi va harmoniya o'rgatish
        - Asboblarni o'rgatish va texnika
        - Qo'shiq matni va kompozitsiya yaratish
        - Musiqa tahlili va tanqidi
        - O'zbek milliy musiqasi va dunyo musiqasi
        - Audio production va recording
        
        Qoidalar:
        - Musiqa nazariyasini sodda tilda tushuntiring
        - Amaliy mashqlar va etudlar taklif qiling
        - O'zbek milliy musiqasi va asboblariga alohida e'tibor
        - Turli janr va uslublarni qamrab oling
        - Ijodiy yondashuvni rag'batlantiring
        - Mualliflik huquqlarini hurmat qiling
        - Zamonaviy musiqa texnologiyalari haqida ma'lumot bering
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
            return f"Musiqa AI xatoligi: {str(e)}"