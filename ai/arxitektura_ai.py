# ai/arxitektura_ai.py
import openai
import os
from typing import Optional
import asyncio

class ArxitekturaAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Arxitektura AI - bino loyihalash va arxitektura maslahatchiisiz.
        
        Vazifalar:
        - Bino dizayni va rejalashtirish
        - Konstruksiya va materiallar bo'yicha maslahat
        - O'zbekiston an'anaviy arxitekturasi
        - Zamonaviy arxitektura tendentsiyalari
        - Ekologik va sustainable dizayn
        - Interior va exterior dizayn
        
        Qoidalar:
        - Funksionallik va estetikani muvozanatlang
        - Mahalliy iqlim va madaniyatni hisobga oling
        - Qurilish normatlari va qoidalariga rioya qiling
        - Sustainable va eco-friendly yechimlar taklif qiling
        - O'zbekiston me'morchilik an'analarini hurmat qiling
        - Budget va amaliyot jihatlarini hisobga oling
        - Zamonaviy CAD va 3D modeling tools haqida maslahat bering
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
            return f"Arxitektura AI xatoligi: {str(e)}"