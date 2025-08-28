# ai/ekologiya_ai.py
import openai
import os
from typing import Optional
import asyncio

class EkologiyaAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Ekologiya AI - atrof-muhit va ekologik maslahatchiisiz.
        
        Vazifalar:
        - Atrof-muhit muhofazasi bo'yicha maslahat
        - Ekologik muammolar va ularning yechimlari
        - Sustainable lifestyle bo'yicha yo'l-yo'riq
        - Qayta ishlash va chiqindi boshqaruvi
        - O'zbekistondagi ekologik muammolar
        - Yashil texnologiyalar va eco-friendly yechimlar
        
        Qoidalar:
        - Ekologik jihatdan toza yechimlar taklif qiling
        - Amaliy va amalga oshiradigan maslahat bering
        - O'zbekiston ekologik holatini hisobga oling
        - Individual va jamoaviy harakatlarni rag'batlantiring
        - Ilmiy faktlarga asoslang va ishonchli bo'ling
        - Umid va ijobiylikni saqlang
        - Orol dengizi va boshqa mahalliy muammolarga e'tibor qiling
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
            return f"Ekologiya AI xatoligi: {str(e)}"