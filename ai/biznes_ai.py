# ai/biznes_ai.py (to'liq versiya)
import openai
import os
from typing import Optional
import asyncio

class BiznesAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Biznes AI - biznes strategiya maslahatchiisiz.
        
        Vazifalar:
        - Biznes rejalar yaratish
        - Marketing strategiyalari
        - Moliyaviy tahlil
        - Startup qo'llab-quvvatlash
        - O'zbekiston bozori tahlili
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
            return f"Biznes AI xatoligi: {str(e)}"