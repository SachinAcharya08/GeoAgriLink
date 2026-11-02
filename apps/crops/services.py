from apps.crops.models import Crop


class CropService:
    @staticmethod
    def get_crop_by_id(crop_id):
        try:
            return Crop.objects.get(id=crop_id)
        except Crop.DoesNotExist:
            return None
