from rest_framework.routers import DefaultRouter

from apps.marketplaces.views import OrderViewSet, ProductViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="products")
router.register("orders", OrderViewSet, basename="orders")

urlpatterns = router.urls
