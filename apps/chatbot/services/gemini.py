import logging

from django.conf import settings
from google import genai
from google.genai import types

from apps.chatbot.services.prompts import GEOAGRI_SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        api_key = settings.GEMINI_API_KEY

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        self.client = genai.Client(api_key=api_key)
        self.model = settings.GEMINI_MODEL

    def generate_response(self, message):
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=GEOAGRI_SYSTEM_INSTRUCTION,
                    temperature=0.3,
                ),
            )

            return response.text

        except Exception:
            logger.exception("Gemini API request failed.")
            raise
