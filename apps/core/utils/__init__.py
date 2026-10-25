import re
import secrets
import string
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


def get_paginated_response(paginator, queryset, serializer_class, request):
    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        serializer = serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = serializer_class(queryset, many=True)
    return Response(serializer.data)


def generate_unique_id() -> str:
    return str(uuid.uuid4())


def generate_random_string(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_token(length: int = 64) -> str:
    """Generate a secure random token for verification/reset purposes."""
    return secrets.token_urlsafe(length)


def parse_datetime_string(datetime_str: str, formats: List[str] = None) -> Optional[datetime]:
    """
    Parse datetime string with multiple format attempts.
    """
    if formats is None:
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    return None


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    """
    if dt is None:
        return ""
    return dt.strftime(fmt)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing special characters.
    """
    # Remove any path components
    filename = filename.split("/")[-1].split("\\")[-1]
    # Remove special characters except alphanumeric, dots, dashes, and underscores
    filename = re.sub(r"[^\w\.-]", "_", filename)
    # Limit length
    if len(filename) > 100:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = f"{name[:95]}.{ext}" if ext else name[:100]
    return filename


def validate_email_format(email: str) -> bool:
    """
    Basic email format validation.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def truncate_string(value: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to specified length with suffix.
    """
    if len(value) <= max_length:
        return value
    return value[: max_length - len(suffix)] + suffix


def dict_get_nested(nested_dict: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value using dot notation.
    Example: dict_get_nested(data, 'user.profile.name', 'Unknown')
    """
    keys = path.split(".")
    value = nested_dict
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


def calculate_percentage(part: float, whole: float, decimal_places: int = 2) -> float:
    """
    Calculate percentage safely handling division by zero.
    """
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, decimal_places)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def get_client_ip(request) -> str:
    """
    Extract client IP address from request.
    Handles proxy forwarding headers.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip


def days_since(dt: datetime) -> int:
    """
    Calculate number of days since given datetime.
    """
    if dt is None:
        return 0
    now = timezone.now() if timezone.is_aware(dt) else datetime.now()
    delta = now - dt
    return delta.days


def is_expired(dt: datetime, timeout_hours: int = 24) -> bool:
    """
    Check if datetime has expired based on timeout.
    """
    if dt is None:
        return True
    timeout = timedelta(hours=timeout_hours)
    now = timezone.now() if timezone.is_aware(dt) else datetime.now()
    return now > dt + timeout


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class for API responses.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def build_api_response(
    success: bool = True,
    message: str = "",
    data: Any = None,
    errors: Dict[str, Any] = None,
    meta: Dict[str, Any] = None,
    status_code: int = 200,
) -> Dict[str, Any]:
    """
    Build standardized API response structure.
    """
    response = {
        "success": success,
        "message": message,
    }

    if data is not None:
        response["data"] = data

    if errors is not None:
        response["errors"] = errors

    if meta is not None:
        response["meta"] = meta

    return response


def format_file_size(size_bytes: int) -> str:
    """
    Format bytes to human readable file size.
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.2f} {size_names[i]}"


def generate_slug(text: str) -> str:
    """
    Generate URL-friendly slug from text.
    """
    import unicodedata

    text = text.lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text).strip("-")
    return text


def sanitize_html(html: str) -> str:
    """
    Basic HTML sanitization (remove script tags and dangerous attributes).
    """
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'on\w+="[^"]*"', "", html, flags=re.IGNORECASE)
    html = re.sub(r"on\w+=\'[^\']*\'", "", html, flags=re.IGNORECASE)
    return html


def validate_url(url: str) -> bool:
    """
    Basic URL validation.
    """
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return re.match(pattern, url) is not None


def validate_phone_number(phone: str) -> bool:
    """
    Basic phone number validation (international format).
    """
    pattern = r"^\+?[\d\s-]{10,}$"
    return re.match(pattern, phone) is not None


def check_password_strength(password: str) -> dict:
    """
    Check password strength and return score with feedback.
    """
    score = 0
    feedback = []

    if len(password) >= 8:
        score += 1
    else:
        feedback.append("At least 8 characters")

    if re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Uppercase letter")

    if re.search(r"[a-z]", password):
        score += 1
    else:
        feedback.append("Lowercase letter")

    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Number")

    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback.append("Special character")

    strength = {0: "Very Weak", 1: "Weak", 2: "Fair", 3: "Good", 4: "Strong", 5: "Very Strong"}

    return {"score": score, "strength": strength[score], "feedback": feedback if score < 5 else []}


def convert_timezone(dt: datetime, from_tz: str, to_tz: str) -> datetime:
    """
    Convert datetime from one timezone to another.
    """
    from zoneinfo import ZoneInfo

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(from_tz))
    return dt.astimezone(ZoneInfo(to_tz))


def humanize_time_delta(dt: datetime) -> str:
    """
    Convert datetime to human-readable relative time (e.g., "2 hours ago").
    """
    from django.utils import timezone

    now = timezone.now()
    delta = now - dt

    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    if delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    if delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    return "Just now"


def extract_hashtags(text: str) -> list:
    """
    Extract hashtags from text.
    """
    return re.findall(r"#(\w+)", text)


def extract_mentions(text: str) -> list:
    """
    Extract @mentions from text.
    """
    return re.findall(r"@(\w+)", text)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text (collapse multiple spaces).
    """
    return re.sub(r"\s+", " ", text).strip()


def mask_email(email: str) -> str:
    """
    Mask email for privacy (e.g., j***@example.com).
    """
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) > 2:
        masked = local[0] + "*" * (len(local) - 2) + local[-1]
    else:
        masked = "*" * len(local)
    return f"{masked}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number for privacy (e.g., +1 *** *** 1234).
    """
    phone = re.sub(r"[^\d+]", "", phone)
    if len(phone) > 4:
        return phone[:-4] + "*" * 4
    return phone
