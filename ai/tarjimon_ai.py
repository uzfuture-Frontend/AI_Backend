# Qolgan barcha AI assistant klasslari

# ai/tarjimon_ai.py (to'liq versiya)
import openai
import os
import asyncio

class TarjimonAI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"
        self.system_prompt = """
        Siz professional Tarjimon AI - 100+ tilga tarjima qiluvchisiz.
        
        Vazifalar:
        - Professional va aniq tarjima
        - Kontekst va madaniy jihatlarni hisobga olish
        - Ovozli va matnli tarjima
        - Terminologiya va texnik tarjima
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
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Tarjima xatoligi: {str(e)}"
