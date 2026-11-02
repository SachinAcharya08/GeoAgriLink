from apps.farms.models import Farms


def resolve_farm(user, farm_name):
    farms = Farms.objects.filter(owner=user)
    if farm_name:
        farms = farms.filter(name__icontains=farm_name)
    farms = list(farms[:5])

    if not farms:
        return None, {"error": "No matching farm found for this user."}
    if len(farms) > 1:
        return None, {
            "error": "Several farms match. Ask the user which one.",
            "farms": [f.name for f in farms],
        }
    return farms[0], None
