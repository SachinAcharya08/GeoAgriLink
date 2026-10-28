from rest_framework.routers import DefaultRouter

from apps.ai_insights.views import AIInsightModelviewsets

router = DefaultRouter()
router.register("ai-insight", AIInsightModelviewsets, basename="ai-insight")

urlpatterns = router.urls
