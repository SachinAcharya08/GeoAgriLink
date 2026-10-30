from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.marketplaces.views import OrderCreateView, OrderViewSet, ProductViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="products")
router.register("orders", OrderViewSet, basename="orders")

urlpatterns = [
    path("orders/create/", OrderCreateView.as_view(), name="order-create"),
]

urlpatterns += router.urls
