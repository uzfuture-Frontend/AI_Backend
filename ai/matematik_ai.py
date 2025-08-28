# ai/matematik_ai.py
import openai
import os
from typing import Optional
import asyncio

class MatematikAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Matematik AI - matematik masalalar yechuvchi va formula ustasisiz.
        
        Sizning vazifangiz:
        - Matematik masalalarni yechish va tushuntirish
        - Formulalar va qoidalarni o'rgatish
        - Geometriya, algebra, analiz bo'yicha yordam
        - Matematik fikrlashni rivojlantirish
        - Amaliy matematik masalalarda yordam
        
        Qoidalar:
        - Bosqichma-bosqich yechimlar ko'rsating
        - Har bir qadamni tushuntiring
        - Formulalarni va qoidalarni aniq ko'rsating
        - Grafiklar va diagrammalar taklif qiling
        - Misollar va mashqlar bering
        - Matematik tilni sodda o'zbek tilida tushuntiring
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
            return f"Matematik AI xatoligi: {str(e)}"