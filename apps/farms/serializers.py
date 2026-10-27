from rest_framework.serializers import ModelSerializer

from apps.farms.models import FarmHistorys, Farms


class FarmSerializers(ModelSerializer):
    class Meta:
        model = Farms
        fields = "__all__"
        read_only_fields = ["id", "owner", "updated_at", "created_at"]


class FarmHistorySerializers(ModelSerializer):
    class Meta:
        model = FarmHistorys
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
