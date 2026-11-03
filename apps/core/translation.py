from collections.abc import Mapping

import requests
from django.conf import settings

LANGUAGE_CODES = {
    "en": "EN",
    "hi": "HI",
    "ne": "NE",
}


class TranslationError(RuntimeError):
    pass


def normalize_language(language):
    language = (language or "en").lower()
    if language not in LANGUAGE_CODES:
        raise TranslationError("Unsupported language. Use one of: en, hi, ne.")
    return language


def _translate_strings(value, translations):
    if isinstance(value, str):
        translations.append(value)
    elif isinstance(value, Mapping):
        for item in value.values():
            _translate_strings(item, translations)
    elif isinstance(value, list):
        for item in value:
            _translate_strings(item, translations)


def _replace_strings(value, translated, position):
    if isinstance(value, str):
        replacement = translated[position[0]]
        position[0] += 1
        return replacement
    if isinstance(value, dict):
        return {key: _replace_strings(item, translated, position) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_strings(item, translated, position) for item in value]
    return value


def translate_payload(payload, language):
    language = normalize_language(language)
    if language == "en":
        return payload

    texts = []
    _translate_strings(payload, texts)
    if not texts:
        return payload

    auth_key = getattr(settings, "DEEPL_AUTH_KEY", "")
    if not auth_key:
        raise TranslationError("DeepL API key is not configured.")

    try:
        result = requests.post(
            getattr(settings, "DEEPL_TRANSLATE_URL", "https://api-free.deepl.com/v2/translate"),
            headers={"Authorization": f"DeepL-Auth-Key {auth_key}"},
            data=[("text", text) for text in texts] + [("target_lang", LANGUAGE_CODES[language])],
            timeout=30,
        )
        result.raise_for_status()
        translated = result.json()["translations"]
        translated_texts = [item["text"] for item in translated]
    except requests.Timeout as exc:
        raise TranslationError("DeepL translation timed out.") from exc
    except requests.HTTPError as exc:
        raise TranslationError("DeepL rejected the translation request.") from exc
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        raise TranslationError("Unable to translate the response with DeepL.") from exc

    if len(translated_texts) != len(texts):
        raise TranslationError("DeepL returned an incomplete translation.")
    return _replace_strings(payload, translated_texts, [0])
