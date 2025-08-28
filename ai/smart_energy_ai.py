# ai/smart_energy_ai.py (to'liq versiya)
import openai
import os
from typing import Optional
import asyncio

class SmartEnergyAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Smart Energy AI - aqlli energiya mutaxassisisiz.
        
        Vazifalar:
        - Qayta tiklanadigan energiya
        - Smart grid texnologiyalari
        - Energiya samaradorligi
        - Yashil texnologiyalar
        - Solar va shamol energiyasi
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
                temperature=0.4
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Smart Energy AI xatoligi: {str(e)}"