import logging

from django.conf import settings
from google import genai
from google.genai import types

from apps.chatbot.services.prompts import GEOAGRI_SYSTEM_INSTRUCTION
from apps.chatbot.tools.registry import TOOL_CONFIG, run_tool

logger = logging.getLogger(__name__)

MAX_TOOL_STEPS = 5
FALLBACK_REPLY = "Sorry, I couldn't complete that. Please try again."


class GeminiService:
    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        self.client = genai.Client(api_key=api_key)
        self.model = settings.GEMINI_MODEL

    def _build_contents(self, history, message):
        contents = []
        for m in history:
            if m.role not in ("user", "assistant"):
                continue
            role = "user" if m.role == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=m.content)]))
        contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
        return contents

    def generate_response(self, history, message, user):
        """Returns (reply_text, pending_action_id or None)."""
        contents = self._build_contents(history, message)
        config = types.GenerateContentConfig(
            system_instruction=GEOAGRI_SYSTEM_INSTRUCTION,
            temperature=0.3,
            tools=[TOOL_CONFIG],
        )

        pending_id = None
        try:
            for _ in range(MAX_TOOL_STEPS):
                response = self.client.models.generate_content(model=self.model, contents=contents, config=config)
                calls = response.function_calls
                if not calls:
                    return response.text or FALLBACK_REPLY, pending_id

                parts = []
                for c in calls:
                    out = run_tool(user, c.name, c.args)
                    result = out.get("result")
                    if isinstance(result, dict) and result.get("pending_action_id"):
                        pending_id = result["pending_action_id"]
                    parts.append(types.Part.from_function_response(name=c.name, response=out))

                contents.append(response.candidates[0].content)  # model's tool request
                contents.append(types.Content(role="user", parts=parts))  # our results

        except Exception:
            logger.exception("Gemini API request failed.")
            raise

        return FALLBACK_REPLY, pending_id
