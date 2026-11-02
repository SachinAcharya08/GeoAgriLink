from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.chatbot.models import PendingAction
from apps.chatbot.tools.common import resolve_farm
from apps.crops.models import Crops, ProductionHistory
from apps.farms.models import Farms
from apps.marketplaces.models import Order, OrderItem, Product
from apps.marketplaces.serializers import OrderCreateSerializer, ProductSerializer

CONFIRM_MINUTES = 10


def _dec(value):
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None
    return d if d > 0 else None


def _to_datetime(value):
    d = parse_date(str(value or "").strip())
    if not d:
        return None
    return timezone.make_aware(datetime.combine(d, time.min))


def _create_pending(user, action, payload, summary):
    # only one open question per farmer at a time
    PendingAction.objects.filter(user=user, status=PendingAction.Status.PENDING).update(
        status=PendingAction.Status.CANCELLED
    )

    p = PendingAction.objects.create(
        user=user,
        action=action,
        payload=payload,
        summary=summary,
        expires_at=timezone.now() + timedelta(minutes=CONFIRM_MINUTES),
    )
    return {
        "status": "awaiting_confirmation",
        "pending_action_id": str(p.id),
        "summary": summary,
        "instruction": (
            "NOTHING is saved yet. Tell the farmer this summary in simple words "
            "and ask them to tap the Confirm button."
        ),
    }


# ---------- PREPARE (called by Gemini, never writes the real data) ----------


def prepare_post_product(user, name, price, quantity, unit="kg", farm_name="", description=""):
    farm, err = resolve_farm(user, farm_name)
    if err:
        return err

    price_d, qty_d = _dec(price), _dec(quantity)
    if not price_d or not qty_d:
        return {"error": "Price and quantity must be numbers above zero."}

    payload = {
        "farm": str(farm.id),
        "name": name.strip(),
        "description": description or "",
        "price": str(price_d),
        "unit": unit,
        "quantity_available": str(qty_d),
        "is_available": True,
    }
    check = ProductSerializer(data=payload)
    if not check.is_valid():
        return {
            "error": "Invalid details.",
            "details": {k: [str(e) for e in v] for k, v in check.errors.items()},
        }

    summary = f"Post {qty_d} {unit} of {payload['name']} for sale " f"at Rs {price_d} per {unit} from {farm.name}."
    return _create_pending(user, "post_product", payload, summary)


def prepare_place_order(user, product_name, quantity, delivery_address, farm_name=""):
    qty = _dec(quantity)
    if not qty:
        return {"error": "Quantity must be a number above zero."}

    address = (delivery_address or "").strip()
    if not address:
        return {"error": "Delivery address is missing. Ask the farmer for it."}

    qs = (
        Product.objects.filter(is_available=True, quantity_available__gt=0, name__icontains=product_name)
        .exclude(farm__owner=user)  # can't buy from yourself
        .select_related("farm")
    )
    if farm_name:
        qs = qs.filter(farm__name__icontains=farm_name)

    matches = list(qs[:5])
    if not matches:
        return {"error": "No available product found with that name."}
    if len(matches) > 1:
        return {
            "error": "Several products match. Ask the farmer which one.",
            "options": [{"name": p.name, "farm": p.farm.name, "price": str(p.price), "unit": p.unit} for p in matches],
        }

    p = matches[0]
    if qty > p.quantity_available:
        return {"error": f"Only {p.quantity_available} {p.unit} available."}

    payload = {"product_id": str(p.id), "quantity": str(qty), "delivery_address": address}
    summary = (
        f"Order {qty} {p.unit} of {p.name} from {p.farm.name} at Rs {p.price} per {p.unit}. "
        f"Total: Rs {qty * p.price}. Deliver to: {address}."
    )
    return _create_pending(user, "place_order", payload, summary)


def _resolve_crop(user, crop_name):
    qs = Crops.objects.filter(Q(owner=user) | Q(owner__isnull=True), name__icontains=crop_name)
    exact = qs.filter(name__iexact=crop_name).first()
    if exact:
        return exact, None
    matches = list(qs[:5])
    if not matches:
        return None, {"error": "No crop found with that name."}
    if len(matches) > 1:
        return None, {
            "error": "Several crops match. Ask the farmer which one.",
            "options": [c.name for c in matches],
        }
    return matches[0], None


def prepare_add_production_record(
    user,
    crop_name,
    quantity,
    planted_date,
    unit="kg",
    harvested_date="",
    remarks="",
    farm_name="",
):
    farm, err = resolve_farm(user, farm_name)
    if err:
        return err
    crop, err = _resolve_crop(user, crop_name)
    if err:
        return err

    qty = _dec(quantity)
    if not qty:
        return {"error": "Quantity must be a number above zero."}

    planted = _to_datetime(planted_date)
    if not planted:
        return {"error": "Planting date is missing or invalid. Ask the farmer when they planted it."}

    harvested = None
    if harvested_date:
        harvested = _to_datetime(harvested_date)
        if not harvested:
            return {"error": "Harvest date is invalid. Ask the farmer again."}
        if harvested < planted:
            return {"error": "Harvest date cannot be before the planting date."}

    payload = {
        "farm": str(farm.id),
        "crop": str(crop.id),
        "planted_date": planted.isoformat(),
        "harvested_date": harvested.isoformat() if harvested else None,
        "quantity": str(qty),
        "unit": unit,
        "remarks": (remarks or "")[:500],
    }
    when = f", harvested on {harvested.date()}" if harvested else " (not harvested yet)"
    summary = f"Record {qty} {unit} of {crop.name} on {farm.name}, " f"planted on {planted.date()}{when}."
    return _create_pending(user, "add_production_record", payload, summary)


# ---------- EXECUTE (called only by the confirm endpoint) ----------


def execute_post_product(pending):
    s = ProductSerializer(data=pending.payload)
    s.is_valid(raise_exception=True)
    if s.validated_data["farm"].owner_id != pending.user_id:  # re-check at write time
        raise ValueError("You can only post products from your own farm.")
    product = s.save()
    return f"Done! {product.name} is now posted for sale."


def execute_place_order(pending):
    pl = pending.payload
    with transaction.atomic():
        product = Product.objects.select_for_update().select_related("farm").get(id=pl["product_id"], is_available=True)
        s = OrderCreateSerializer(
            data={
                "farm_id": str(product.farm_id),
                "delivery_address": pl["delivery_address"],
                "items": [{"product_id": str(product.id), "quantity": pl["quantity"]}],
            }
        )
        s.is_valid(raise_exception=True)
        qty = s.validated_data["items"][0]["quantity"]

        if product.farm.owner_id == pending.user_id:
            raise ValueError("You can't order your own product.")
        if qty > product.quantity_available:
            raise ValueError("Sorry, the stock just changed. Please ask me again.")

        order = Order.objects.create(
            customer_id=pending.user_id,
            farm=product.farm,
            delivery_address=s.validated_data["delivery_address"],
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit=product.unit,
            quantity=qty,
            unit_price=product.price,
        )
        product.quantity_available -= qty
        product.save(update_fields=["quantity_available", "updated_at"])

    return f"Order placed! Total: Rs {order.total_amount}."


def execute_add_production_record(pending):
    pl = pending.payload
    farm = Farms.objects.filter(id=pl["farm"], owner_id=pending.user_id).first()  # re-check owner
    if not farm:
        raise ValueError("You can only add records to your own farm.")

    record = ProductionHistory(
        farm=farm,
        crop_id=pl["crop"],
        planted_date=datetime.fromisoformat(pl["planted_date"]),
        harvested_date=(datetime.fromisoformat(pl["harvested_date"]) if pl["harvested_date"] else None),
        quantity=Decimal(pl["quantity"]),
        unit=pl["unit"],
        remarks=pl["remarks"],
    )
    try:
        record.full_clean()  # runs your model's clean() and validators
    except DjangoValidationError:
        raise ValueError("Some details were not valid. Please try again.")
    record.save()
    return "Done! Your harvest record is saved."


EXECUTORS = {
    "post_product": execute_post_product,
    "place_order": execute_place_order,
    "add_production_record": execute_add_production_record,
}
