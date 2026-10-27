from rest_framework.routers import DefaultRouter

from apps.farms.views import FarmHistoryModelViewsets, FarmModelViewsets

router = DefaultRouter()
router.register("farms", FarmModelViewsets, basename="farm")
router.register("farm-history", FarmHistoryModelViewsets, basename="farm-history")

urlpatterns = router.urls
