from decimal import Decimal

from rest_framework import serializers

from apps.marketplaces.models import Order, OrderItem, Product


class ProductSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source="farm.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "farm",
            "farm_name",
            "name",
            "description",
            "image",
            "price",
            "unit",
            "quantity_available",
            "is_available",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "farm_name",
            "created_at",
            "updated_at",
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_quantity_available(self, value):
        if value < 0:
            raise serializers.ValidationError("Available quantity cannot be negative.")
        return value


class ProductListSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source="farm.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "farm",
            "farm_name",
            "name",
            "image",
            "description",
            "price",
            "unit",
            "quantity_available",
            "is_available",
            "created_at",
        ]
        read_only_fields = fields


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=22, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "unit",
            "quantity",
            "unit_price",
            "subtotal",
        ]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source="customer.get_full_name", read_only=True)
    seller_name = serializers.CharField(source="seller.get_full_name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "customer_name",
            "seller",
            "seller_name",
            "status",
            "delivery_address",
            "items",
            "total_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_total_amount(self, obj):
        if "total_amount_calculated" in obj.__dict__:
            return obj.__dict__["total_amount_calculated"]

        return obj.total_amount


class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product does not exist.")
        return value


class OrderCreateSerializer(serializers.Serializer):
    delivery_address = serializers.CharField(max_length=500, trim_whitespace=True)
    items = OrderItemCreateSerializer(many=True, allow_empty=False)

    def validate_delivery_address(self, value):
        if not value.strip():
            raise serializers.ValidationError("Delivery address is required.")
        return value

    def validate_items(self, value):
        product_ids = [item["product_id"] for item in value]

        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products are not allowed.")

        return value
