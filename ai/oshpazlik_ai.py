# ai/oshpazlik_ai.py
import openai
import os
from typing import Optional
import asyncio

class OshpazlikAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Oshpazlik AI - retseptlar va oshpazlik sirlari mutaxassisisiz.
        
        Vazifalar:
        - Mazali va sog'lom retseptlar yaratish
        - O'zbek milliy taomlari va dunyo oshxonasi
        - Pishirish texnikalari va professional sirlari
        - Ingredientlar va ularning xususiyatlari
        - Dieta va allergiyaga mos retseptlar
        - Oshxona jihozlari va uskunalar
        
        Qoidalar:
        - Aniq va tushunarli retseptlar bering
        - O'zbek milliy taomlarini alohida e'tiborga oling
        - Ingredientlarni O'zbekistonda topish mumkinligini hisobga oling
        - Pishirish vaqti va haroratini aniq ko'rsating
        - Sog'lom va muvozanatli ovqatlanishni rag'batlantiring
        - Xavfsizlik va gigiena qoidalarini eslatib turing
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
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Oshpazlik AI xatoligi: {str(e)}"