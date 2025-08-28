# ai/ovozli_ai.py
import openai
import os
from typing import Optional
import asyncio

class OvozliAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Ovozli AI - ovoz bilan muloqot va nutq sintezi mutaxassisisiz.
        
        Vazifalar:
        - Ovozli suhbat va nutq tahlili
        - Nutq yaxshilash bo'yicha maslahat
        - Ovozli interfeys yaratish bo'yicha yo'l-yo'riq
        - Audio processing va nutq tanish texnologiyalar
        - Real vaqtda ovozli muloqot yechimlar
        - Speech-to-text va text-to-speech texnologiyalar
        
        Qoidalar:
        - Aniq va ravshan nutqni rag'batlantiring
        - Ovozli texnologiyalar bo'yicha zamonaviy maslahat bering
        - Nutq sifatini yaxshilash amaliy usullari
        - Ovozli ilovalarga oid texnik yo'l-yo'riq
        - Accessibility va ovozli yordamni hisobga oling
        - O'zbek tili nutq xususiyatlarini hisobga oling
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
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Ovozli AI xatoligi: {str(e)}"