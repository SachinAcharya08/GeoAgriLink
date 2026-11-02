from apps.farms.models import FarmHistorys, Farms

from .gee_services import fetch_gee_data


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
            farm_history = FarmHistorys.objects.create(
                farm_id=farm_id,
                # recorded_at=recorded_at,
                **result
            )
            return farm_history

    @staticmethod
    def analyze_farm_history(farm_history):
        analysis_result = {
            "ci_rededge": farm_history.ci_rededge,
            "evi": farm_history.evi,
            "lswi": farm_history.lswi,
            "ndre": farm_history.ndre,
            "ndvi": farm_history.ndvi,
            "ndwi": farm_history.ndwi,
            "lst": farm_history.lst,
            "source": farm_history.source,
        }
        return analysis_result
