from unittest.mock import patch

import pytest
from django.test import override_settings

from apps.core.translation import translate_payload


@pytest.mark.django_db
@override_settings(DEEPL_AUTH_KEY="test-key")
def test_translate_payload_preserves_nested_shape():
    payload = {
        "disease": "Leaf blight",
        "confidence": 0.9,
        "recommendations": ["Remove infected leaves"],
    }

    with patch(
        "apps.core.translation.requests.post",
    ) as post:
        post.return_value.raise_for_status.return_value = None
        post.return_value.json.return_value = {
            "translations": [
                {"text": "फसल रोग"},
                {"text": "संक्रमित पत्तियां हटाएं"},
            ]
        }
        translated = translate_payload(payload, "hi")

    assert translated == {
        "disease": "फसल रोग",
        "confidence": 0.9,
        "recommendations": ["संक्रमित पत्तियां हटाएं"],
    }
    assert post.call_args.kwargs["headers"]["Authorization"] == "DeepL-Auth-Key test-key"
