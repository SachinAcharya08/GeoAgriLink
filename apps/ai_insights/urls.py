# from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.ai_insights.views import (
    AIInsightModelviewsets,
    CropDiseaseDetectionModelViewSet,
)

router = DefaultRouter()
router.register("ai-insight", AIInsightModelviewsets, basename="ai-insight")
router.register(
    "crop-disease-detection",
    CropDiseaseDetectionModelViewSet,
    basename="crop-disease-detection",
)


urlpatterns = router.urls
