import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.ai_insights.models import AIInsight
from apps.ai_insights.serializers import (
    AIInsightSerializers,
    CropDiseaseDetectionSerializer,
)


class AIInsightModelviewsets(viewsets.ReadOnlyModelViewSet):
    serializer_class = AIInsightSerializers
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AIInsight.objects.filter(farm__owner=self.request.user).select_related("farm", "production_history")


class CropDiseaseDetectionModelViewSet(viewsets.ModelViewSet):
    serializer_class = CropDiseaseDetectionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["post", "options"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        farm = serializer.validated_data["farm"]
        image = serializer.validated_data["image"]

        url = f"{settings.FASTAPI_URL.rstrip('/')}/analyze"

        try:
            image.seek(0)

            response = requests.post(
                url,
                files={
                    "image": (
                        image.name,
                        image,
                        image.content_type,
                    )
                },
                timeout=60,
            )

            response.raise_for_status()
            prediction = response.json()

        except requests.Timeout:
            return Response(
                {"error": "AI service request timed out."},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )

        except requests.HTTPError:
            return Response(
                {"error": "AI service returned an error."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        except requests.RequestException:
            return Response(
                {"error": "Unable to connect to AI service."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except ValueError:
            return Response(
                {"error": "AI service returned invalid JSON."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        image.seek(0)

        insight = AIInsight.objects.create(
            farm=farm,
            image=image,
            insight_type="crop_health",
            result=prediction,
            model_version=prediction.get("meta", {}).get("model", "unknown"),
            generated_at=timezone.now(),
        )

        return Response(
            AIInsightSerializers(insight).data,
            status=status.HTTP_201_CREATED,
        )
