import os
from datetime import timedelta
from pathlib import Path

import environ
import pymysql

pymysql.install_as_MySQLdb()


env = environ.Env(
    DEBUG=(bool,),
    ALLOWED_HOSTS=(str, "localhost,127.0.0.1"),
)
FASTAPI_URL = os.getenv("FASTAPI_URL")

# Build paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Create logs directory if it doesn't exist
(Path(PROJECT_ROOT) / "logs").mkdir(parents=True, exist_ok=True)

# Load environment variables
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))


SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-key-change-in-production")
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")

INSTALLED_APPS = [
    # "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Third party packages
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # Internal apps
    "apps.core.apps.CoreConfig",
    "apps.users.apps.UsersConfig",
    "apps.farms.apps.FarmsConfig",
    "apps.crops.apps.CropsConfig",
    "apps.ai_insights.apps.AiInsightsConfig",
    "apps.marketplaces.apps.MarketplacesConfig",
    "apps.chatbot.apps.ChatbotConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RequestLoggingMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "apps.core.middleware.ExceptionHandlerMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database - MySQL with PyMySQL
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.mysql"),
        "NAME": env("DB_NAME", default="geoagrilink_db"),
        "USER": env("DB_USER", default="root"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="3306"),
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "charset": "utf8mb4",
            "connect_timeout": 5,
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_MIMETYPES = {
    ".json": "application/json",
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

AUTH_USER_MODEL = "users.User"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "50/minute",
        "user": "100/minute",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default=60))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_TOKEN_EXPIRE_DAYS", default=7))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": env("JWT_ALGORITHM", default="HS256"),
    "SIGNING_KEY": env("JWT_SECRET_KEY", default=SECRET_KEY),
    "VERIFYING_KEY": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in env("CORS_ALLOWED_ORIGINS", default="http://localhost:3000").split(",")
]

CORS_ALLOW_CREDENTIALS = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": env("LOG_LEVEL", default="INFO"),
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": PROJECT_ROOT / "logs" / "django.log",
            "maxBytes": 10485760,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": env("LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": env("LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "AgroLink API",
    "DESCRIPTION": "AgroLink Django REST Framework",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
}

# SECURE_SSL_REDIRECT = not DEBUG
# SESSION_COOKIE_SECURE = not DEBUG
# CSRF_COOKIE_SECURE = not DEBUG
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
# SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
# SECURE_HSTS_PRELOAD = not DEBUG
# SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_HOST = True

CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in env("CSRF_TRUSTED_ORIGINS", default="").split(",") if origin.strip()
]

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "'unsafe-inline'"),
    "style-src": ("'self'", "'unsafe-inline'"),
    "img-src": ("'self'", "data:", "https:"),
    "font-src": ("'self'",),
    "connect-src": ("'self'",),
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

X_FRAME_OPTIONS = "DENY"

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

SILENCED_SYSTEM_CHECKS = []

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = int(env("EMAIL_PORT", default=587))
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env("EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@template.com")
SERVER_EMAIL = env("SERVER_EMAIL", default="info@template.com")

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
EMAIL_TEMPLATES_DIR = BASE_DIR / "templates" / "emails"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "template-cache",
    }
}

JAZZMIN_SETTINGS = {
    "site_title": "Template Admin",
    "site_header": "Template Admin",
    "site_brand": "Template",
    "site_logo": None,
    "welcome_sign": "Welcome to Template Admin Panel",
    "copyright": "Template",
    "search_model": ["users.User"],
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "API Docs", "url": "/api/schema/swagger-ui/", "new_window": True},
        {"model": "users.User"},
    ],
    "usermenu_links": [
        {"model": "users.User"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["users", "auth"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "users.User": "fas fa-user",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "users.user": "collapsible",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
}


SERVICE_ACCOUNT = env("SERVICE_ACCOUNT", default="")
KEY_FILE = env("KEY_FILE", default="")
PROJECT_ID = env("PROJECT_ID", default="")


# CHATBOT
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
