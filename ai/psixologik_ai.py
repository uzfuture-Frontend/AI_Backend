# ai/psixologik_ai.py (to'liq versiya)
import openai
import os
from typing import Optional
import asyncio

class PsixologikAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Psixologik AI - ruhiy salomatlik yordamchisisiz.
        
        Vazifalar:
        - Ruhiy salomatlik maslahatлari
        - Stress va qayg'u bilan kurashish
        - O'z-o'zini rivojlantirish
        - Munosabatlar masalalari
        - Motivatsiya va maqsad belgilash
        
        OGOHLANTIRISH: Psixolog emas, jiddiy muammolarda mutaxassisga yo'naltiring
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
                temperature=0.6
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Psixologik AI xatoligi: {str(e)}"
