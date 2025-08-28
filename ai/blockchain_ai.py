# ai/blockchain_ai.py (to'liq versiya)
import openai
import os
from typing import Optional
import asyncio

class BlockchainAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz Blockchain AI - blockchain va kripto mutaxassisisiz.
        
        Vazifalar:
        - Blockchain texnologiyalari
        - Kripto valyutalar tahlili
        - Smart kontraktlar
        - DeFi va NFT
        - Web3 rivojlanish
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
            return f"Blockchain AI xatoligi: {str(e)}"
