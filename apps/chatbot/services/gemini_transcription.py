from django.conf import settings
from google import genai
from google.genai import types


class TranscriptionError(RuntimeError):
    pass


def transcribe_audio(audio_file):
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        raise TranscriptionError("GEMINI_API_KEY is not configured.")

    try:
        audio_file.seek(0)
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash"),
            contents=[
                types.Part.from_bytes(
                    data=audio_file.read(),
                    mime_type=audio_file.content_type or "application/octet-stream",
                ),
                types.Part.from_text(
                    text=(
                        "Transcribe this audio exactly in the language spoken. "
                        "Do not translate, summarize, or add commentary. Return only the transcript."
                    )
                ),
            ],
            config=types.GenerateContentConfig(temperature=0),
        )
        transcript = response.text
    except genai.errors.APIError as exc:
        message = str(exc)
        if "billing" in message.lower() or "free tier" in message.lower():
            raise TranscriptionError(
                "Gemini API access requires billing for this project. Enable billing or use an API key from a billed project."
            ) from exc
        raise TranscriptionError("Gemini audio transcription failed.") from exc
    except (AttributeError, TypeError, ValueError) as exc:
        raise TranscriptionError("Gemini returned an invalid transcript.") from exc

    if not isinstance(transcript, str) or not transcript.strip():
        raise TranscriptionError("Gemini returned an empty transcript.")
    return transcript.strip()
