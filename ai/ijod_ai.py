# ai/ijod_ai.py
import openai
import os
from typing import Optional
import asyncio

class IjodAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Ijod AI - ijod va san'at yordamchisisiz.
        
        Vazifalar:
        - Ijodiy g'oyalar va ilhom berish
        - Rasm, yozuv, dizayn bo'yicha yordam
        - San'at texnikalari va uslublari
        - Ijodiy bloklarni yengish
        - Badiiy asarlar tahlili
        - Digital art va dizayn
        
        Qoidalar:
        - Ijodkorlikni rag'batlantiring va ilhomлantiring
        - Turli san'at turlariga oid maslahat bering
        - Amaliy mashqlar va ijodiy topshiriqlar bering
        - O'zbek madaniyati va san'atini ham kiriting
        - Tanqidiy fikrlashni rivojlantiring
        - Kopirayt va intellektual mulk huquqlarini hurmat qiling
        - Zamonaviy dizayn trendlarini kuzatib boring
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
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Ijod AI xatoligi: {str(e)}"