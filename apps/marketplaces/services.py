from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.marketplaces.models import Order, OrderItem, Product


@transaction.atomic
def create_order(customer, delivery_address, items):

    if not items:
        raise ValidationError("Order must contain at least one product.")

    product_quantities = {}

    for item in items:
        product_id = item["product_id"]

        try:
            quantity = Decimal(str(item["quantity"]))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError("Invalid product quantity.")

        if not quantity.is_finite() or quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

        if product_id in product_quantities:
            raise ValidationError("Duplicate products are not allowed.")

        product_quantities[product_id] = quantity

    # Lock products to prevent concurrent orders from overselling stock.
    products = list(
        Product.objects.select_for_update()
        .select_related("farm__owner")
        .filter(id__in=product_quantities.keys())
        .order_by("id")
    )

    if len(products) != len(product_quantities):
        raise ValidationError("One or more products do not exist.")

    order_items = []
    seller_ids = set()

    for product in products:
        quantity = product_quantities[product.id]

        if not product.is_available:
            raise ValidationError(f"{product.name} is currently unavailable.")

        if product.quantity_available < quantity:
            raise ValidationError(f"Insufficient stock for {product.name}.")

        seller_ids.add(product.farm.owner_id)
        order_items.append((product, quantity))

    if len(seller_ids) != 1:
        raise ValidationError("All products in an order must belong to the same seller.")

    order = Order.objects.create(
        customer=customer,
        seller_id=seller_ids.pop(),
        delivery_address=delivery_address,
        status="pending",
    )

    for product, quantity in order_items:
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit=product.unit,
            quantity=quantity,
            unit_price=product.price,
        )

        product.quantity_available -= quantity
        product.save(update_fields=["quantity_available"])

    return order
