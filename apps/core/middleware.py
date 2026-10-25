import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        logger.info(
            f"Incoming {request.method} request to {request.path}",
            extra={
                "method": request.method,
                "path": request.path,
                "remote_addr": self.get_client_ip(request),
                "user": request.user if request.user.is_authenticated else "Anonymous",
            },
        )
        return None

    def process_response(self, request, response):
        logger.info(
            f"Response {response.status_code} for {request.method} {request.path}",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
            },
        )
        return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class ExceptionHandlerMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if request.path.startswith("/api/"):
            logger.error(
                f"Unhandled exception in {request.method} {request.path}: {str(exception)}",
                exc_info=True,
                extra={
                    "method": request.method,
                    "path": request.path,
                    "user": request.user if request.user.is_authenticated else "Anonymous",
                    "exception_type": type(exception).__name__,
                },
            )

            response_data = {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
                "detail": str(exception) if settings.DEBUG else None,
            }

            return JsonResponse(response_data, status=500)

        return None
