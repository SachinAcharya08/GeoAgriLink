from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.base_model import BaseModel

UNIT = [
    ("kg", "Kilogram"),
    ("g", "Gram"),
    ("piece", "Piece"),
    ("dozen", "Dozen"),
    ("liter", "Liter"),
    ("crate", "Crate"),
]


class Product(BaseModel):
    farm = models.ForeignKey("farms.Farms", on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=150)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    unit = models.CharField(max_length=20, choices=UNIT, default="kg")
    quantity_available = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0"), validators=[MinValueValidator(Decimal("0"))]
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["farm", "is_available"]),
            models.Index(fields=["is_available", "name"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gt=0),
                name="product_price_positive",
            ),
            models.CheckConstraint(
                condition=Q(quantity_available__gte=0),
                name="product_quantity_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.farm_id}"


class Order(BaseModel):
    STATUS = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sales_orders",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=STATUS, default="pending", db_index=True)
    delivery_address = models.TextField()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "-created_at"]),
        ]

    @property
    def total_amount(self):
        return sum(
            (item.subtotal for item in self.items.all()),
            start=Decimal("0.00"),
        )

    def __str__(self):
        return f"Order {self.pk} - {self.customer_id}"


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    product_name = models.CharField(max_length=150)
    unit = models.CharField(max_length=20, choices=UNIT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"],
                name="unique_product_per_order",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gt=0),
                name="order_item_price_positive",
            ),
        ]

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
