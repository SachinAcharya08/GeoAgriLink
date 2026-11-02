from datetime import date

import requests
from django.conf import settings

from apps.farms.models import FarmHistorys, Farms

from .gee_services import fetch_gee_data

# from rest_framework import status
# from rest_framework.response import Response


class FarmService:
    @staticmethod
    def get_farm_by_id(farm_id):
        try:
            return Farms.objects.get(id=farm_id)
        except Farms.DoesNotExist:
            return None

    @staticmethod
    def get_farm_history_by_id(farm_history_id):
        try:
            return FarmHistorys.objects.get(id=farm_history_id)
        except FarmHistorys.DoesNotExist:
            return None

    @staticmethod
    def fetch_farm_history_indexes(farm_id, recorded_at, days_back):
        farm_history = FarmHistorys.objects.filter(farm_id=farm_id, recorded_at=recorded_at)
        if farm_history.exists():
            return farm_history.first()

        else:
            result = fetch_gee_data(
                Farms.objects.get(id=farm_id).boundary, target_date=recorded_at, days_back=days_back
            )
            farm_history = FarmHistorys.objects.create(farm_id=farm_id, recorded_at=recorded_at, **result)
            return farm_history

    @staticmethod
    def analyze_farm_gee(farm):

        farm_history = FarmService.fetch_farm_history_indexes(
            farm.id,
            date.today(),
            days_back=30,
        )

        payload = {
            "ndvi": farm_history.ndvi,
            "evi": farm_history.evi,
            "ndre": farm_history.ndre,
            "ci_rededge": farm_history.ci_rededge,
            "ndwi": farm_history.ndwi,
            "lswi": farm_history.lswi,
            "lst": farm_history.lst,
            "source": farm_history.source,
        }

        url = f"{settings.FASTAPI_URL.rstrip('/')}/vegetation"

        try:
            api_response = requests.post(
                url,
                json=payload,
                timeout=30,
            )

            api_response.raise_for_status()

            return api_response.json()

        except requests.Timeout:
            raise RuntimeError("AI service request timed out.")

        except requests.HTTPError as exc:
            raise RuntimeError(f"AI service returned HTTP {exc.response.status_code}.")

        except requests.RequestException:
            raise RuntimeError("Unable to connect to AI service.")

        except ValueError:
            raise RuntimeError("AI service returned invalid JSON.")
