from rest_framework.routers import DefaultRouter

from apps.crops.views import CropModelViewsets, ProductionHistoryModelViewset

router = DefaultRouter()
router.register("crops", CropModelViewsets, basename="crop")
router.register("production-history", ProductionHistoryModelViewset, basename="production-history")

urlpatterns = router.urls
