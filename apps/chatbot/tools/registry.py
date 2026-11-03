import logging

from django.db.models import Q
from google.genai import types

from apps.ai_insights.models import AIInsight  # adjust path if different
from apps.chatbot.tools.common import resolve_farm as _resolve_farm
from apps.chatbot.tools.writes import (
    prepare_add_production_record,
    prepare_place_order,
    prepare_post_product,
)
from apps.crops.models import Crops, ProductionHistory
from apps.farms.models import FarmHistorys, Farms
from apps.marketplaces.models import Order, Product

logger = logging.getLogger(__name__)

MAX_ROWS = 10


def _limit(value, default=5):
    try:
        return max(1, min(int(value), MAX_ROWS))
    except (TypeError, ValueError):
        return default


# ---------------- read tools: fn(user, **args) -> JSON-safe ----------------


def list_my_farms(user):
    return [{"name": f.name, "address": f.address, "area": float(f.area)} for f in Farms.objects.filter(owner=user)]


def get_farm_history(user, farm_name="", limit=5):
    farm, err = _resolve_farm(user, farm_name)
    if err:
        return err
    rows = FarmHistorys.objects.filter(farm=farm).order_by("-recorded_at")[: _limit(limit)]
    return {
        "farm": farm.name,
        "records": [
            {
                "date": r.recorded_at.isoformat(),
                "ndvi": r.ndvi,
                "evi": r.evi,
                "ndwi": r.ndwi,
                "ndre": r.ndre,
                "lswi": r.lswi,
                "ci_rededge": r.ci_rededge,
                "land_surface_temp": r.lst,
                "ai_summary": (r.ai_response or "")[:300],
            }
            for r in rows
        ],
    }


def get_production_history(user, farm_name="", limit=5):
    farm, err = _resolve_farm(user, farm_name)
    if err:
        return err
    rows = ProductionHistory.objects.filter(farm=farm).select_related("crop")[: _limit(limit)]
    return {
        "farm": farm.name,
        "records": [
            {
                "crop": r.crop.name,
                "planted": r.planted_date.date().isoformat(),
                "harvested": r.harvested_date.date().isoformat() if r.harvested_date else None,
                "quantity": float(r.quantity),
                "unit": r.unit,
                "remarks": r.remarks,
            }
            for r in rows
        ],
    }


def get_ai_insights(user, farm_name="", insight_type="", limit=3):
    farm, err = _resolve_farm(user, farm_name)
    if err:
        return err
    qs = AIInsight.objects.filter(farm=farm)
    if insight_type:
        qs = qs.filter(insight_type=insight_type)
    return {
        "farm": farm.name,
        "insights": [
            {"type": i.insight_type, "date": i.generated_at.date().isoformat(), "result": i.result}
            for i in qs[: _limit(limit, 3)]
        ],
    }


def list_crops(user, search=""):
    qs = Crops.objects.filter(Q(owner=user) | Q(owner__isnull=True))
    if search:
        qs = qs.filter(name__icontains=search)
    return [{"name": c.name, "category": c.category} for c in qs[:MAX_ROWS]]


def search_marketplace(user, search="", limit=5):
    qs = Product.objects.filter(is_available=True, quantity_available__gt=0).select_related("farm")
    if search:
        qs = qs.filter(name__icontains=search)
    return [
        {
            "name": p.name,
            "farm": p.farm.name,
            "price": float(p.price),
            "unit": p.unit,
            "available": float(p.quantity_available),
        }
        for p in qs[: _limit(limit)]
    ]


def list_my_orders(user, limit=5):
    orders = Order.objects.filter(customer=user).select_related("farm").prefetch_related("items")[: _limit(limit)]
    return [
        {
            "farm": o.farm.name,
            "status": o.status,
            "total": float(o.total_amount),
            "date": o.created_at.date().isoformat(),
            "items": [f"{i.quantity} {i.unit} {i.product_name}" for i in o.items.all()],
        }
        for o in orders
    ]


# ---------------- declarations Gemini sees ----------------


def _str(desc):
    return types.Schema(type="STRING", description=desc)


def _int(desc):
    return types.Schema(type="INTEGER", description=desc)


def _num(desc):
    return types.Schema(type="NUMBER", description=desc)


def _decl(name, description, properties=None, required=None):
    return types.FunctionDeclaration(
        name=name,
        description=description,
        parameters=(
            types.Schema(type="OBJECT", properties=properties, required=required or []) if properties else None
        ),
    )


FARM_NAME = _str("Farm name. Leave empty if the user has only one farm.")

TOOLS = {
    # ----- reads: run immediately -----
    "list_my_farms": {
        "fn": list_my_farms,
        "declaration": _decl("list_my_farms", "List the farmer's farms."),
    },
    "get_farm_history": {
        "fn": get_farm_history,
        "declaration": _decl(
            "get_farm_history",
            "Satellite crop-health readings (NDVI, EVI, etc.) for a farm, newest first.",
            {"farm_name": FARM_NAME, "limit": _int("How many records, max 10")},
        ),
    },
    "get_production_history": {
        "fn": get_production_history,
        "declaration": _decl(
            "get_production_history",
            "Past planting and harvest records for a farm.",
            {"farm_name": FARM_NAME, "limit": _int("How many records, max 10")},
        ),
    },
    "get_ai_insights": {
        "fn": get_ai_insights,
        "declaration": _decl(
            "get_ai_insights",
            "AI-generated insights for a farm (crop health, disease risk, nutrient deficiency, weather).",
            {
                "farm_name": FARM_NAME,
                "insight_type": _str(
                    "One of: crop_health, disease_risk, nutrient_deficiency, weather, other. Empty for all."
                ),
                "limit": _int("How many insights, max 10"),
            },
        ),
    },
    "list_crops": {
        "fn": list_crops,
        "declaration": _decl("list_crops", "Search available crops by name.", {"search": _str("Crop name to search")}),
    },
    "search_marketplace": {
        "fn": search_marketplace,
        "declaration": _decl(
            "search_marketplace",
            "Search products for sale in the marketplace.",
            {"search": _str("Product name to search")},
        ),
    },
    "list_my_orders": {
        "fn": list_my_orders,
        "declaration": _decl("list_my_orders", "The farmer's own orders and their status."),
    },
    # ----- writes: only PREPARE; the farmer must tap Confirm -----
    "post_product": {
        "fn": prepare_post_product,
        "declaration": _decl(
            "post_product",
            "Prepare a marketplace listing for the farmer's produce. Use this tool "
            "whenever the user says list, listing, post, sell, put up for sale, or "
            "create a product. Does NOT save it; the farmer must tap Confirm. "
            "Call once name, price and quantity are known.",
            {
                "name": _str("Product name"),
                "price": _num("Price per unit in Rs"),
                "quantity": _num("Quantity available"),
                "unit": _str("kg, g, piece, dozen, liter or crate. Default kg."),
                "farm_name": FARM_NAME,
                "description": _str("Optional short description"),
            },
            required=["name", "price", "quantity"],
        ),
    },
    "place_order": {
        "fn": prepare_place_order,
        "declaration": _decl(
            "place_order",
            "Prepare an order for a marketplace product. Does NOT place it; "
            "the farmer must tap Confirm. Needs product, quantity and delivery address.",
            {
                "product_name": _str("Product to buy"),
                "quantity": _num("Quantity to buy"),
                "delivery_address": _str("Where to deliver"),
                "farm_name": _str("Seller's farm name, only if several farms sell it"),
            },
            required=["product_name", "quantity", "delivery_address"],
        ),
    },
    "add_production_record": {
        "fn": prepare_add_production_record,
        "declaration": _decl(
            "add_production_record",
            "Prepare a planting/harvest record for a farm. Does NOT save it; "
            "the farmer must tap Confirm. Needs crop, quantity and planting date.",
            {
                "crop_name": _str("Crop name, e.g. wheat"),
                "quantity": _num("Quantity harvested"),
                "planted_date": _str("Planting date as YYYY-MM-DD"),
                "harvested_date": _str("Harvest date as YYYY-MM-DD. Empty if not harvested yet."),
                "unit": _str("kg by default"),
                "farm_name": FARM_NAME,
                "remarks": _str("Optional short note"),
            },
            required=["crop_name", "quantity", "planted_date"],
        ),
    },
}

TOOL_CONFIG = types.Tool(function_declarations=[t["declaration"] for t in TOOLS.values()])


def run_tool(user, name, args):
    tool = TOOLS.get(name)
    if not tool:
        return {"error": f"Unknown tool: {name}"}
    try:
        return {"result": tool["fn"](user, **(args or {}))}
    except Exception:
        logger.exception("Tool %s failed", name)
        return {"error": "Tool failed"}
