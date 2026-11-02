from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    BasePermission,
    IsAuthenticated,
)
from rest_framework.response import Response

# from apps.farms.models import Farms
from apps.marketplaces.models import Order, Product
from apps.marketplaces.serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    ProductListSerializer,
    ProductSerializer,
)
from apps.marketplaces.services import create_order


class IsFarmerOwnerOrReadOnly(BasePermission):
    """
    Public users can view products.
    Only the owning farmer can modify a product.
    """

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        return obj.farm.owner_id == request.user.id


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsFarmerOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Product.objects.select_related(
            "farm",
            "farm__owner",
        )

        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(
                    is_available=True,
                    quantity_available__gt=0,
                )
                | Q(farm__owner=self.request.user)
            )
        else:
            queryset = queryset.filter(
                is_available=True,
                quantity_available__gt=0,
            )

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer

        return ProductSerializer

    def perform_create(self, serializer):
        # farm = get_object_or_404(
        #     Farms,
        #     owner=self.request.user,
        # )

        serializer.save()


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Customers can only view their own orders.
    Order changes are handled through dedicated business actions.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def _orders_queryset(self, **filters):
        return (
            Order.objects.filter(**filters)
            .select_related(
                "customer",
                "seller",
            )
            .prefetch_related("items")
            .annotate(
                total_amount_calculated=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            F("items__quantity") * F("items__unit_price"),
                            output_field=DecimalField(
                                max_digits=22,
                                decimal_places=2,
                            ),
                        )
                    ),
                    Value(Decimal("0.00")),
                    output_field=DecimalField(
                        max_digits=22,
                        decimal_places=2,
                    ),
                )
            )
            .order_by("-created_at")
        )

    def get_queryset(self):
        return self._orders_queryset(seller=self.request.user)

    @extend_schema(
        responses=OrderSerializer(many=True),
        description="List all orders received by the authenticated farmer.",
    )
    @action(detail=False, methods=["get"], url_path="farmer-orders")
    def farmer_orders(self, request):
        serializer = self.get_serializer(self._orders_queryset(seller=request.user), many=True)
        return Response(serializer.data)

    @extend_schema(
        responses=OrderSerializer(many=True),
        description="List orders placed by the authenticated buyer.",
    )
    @action(detail=False, methods=["get"], url_path="my-orders")
    def my_orders(self, request):
        serializer = self.get_serializer(self._orders_queryset(customer=request.user), many=True)
        return Response(serializer.data)

    @extend_schema(
        request=OrderCreateSerializer,
        responses={status.HTTP_201_CREATED: OrderSerializer},
        description="Create an order with nested order items.",
    )
    @action(detail=False, methods=["post"], url_path="create")
    def create_order(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = create_order(
                customer=request.user,
                **serializer.validated_data,
            )
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise ValidationError(exc.message_dict)
            raise ValidationError(exc.messages)

        order = Order.objects.select_related("customer", "seller").prefetch_related("items").get(pk=order.pk)

        response_serializer = OrderSerializer(order)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )
