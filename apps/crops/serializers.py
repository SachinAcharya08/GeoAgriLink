from rest_framework import serializers

from apps.crops.models import Crops, ProductionHistory


class CropSerializers(serializers.ModelSerializer):
    class Meta:
        model = Crops
        fields = "__all__"
        read_only_fields = ["id", "updated_at", "created_at"]


class ProductionHistorySerializers(serializers.ModelSerializer):
    class Meta:
        model = ProductionHistory
        fields = "__all__"
        read_only_fields = ["id", "updated_at", "created_at"]

    def validate(self, attrs):
        planted_date = attrs.get("planted_date", getattr(self.instance, "planted_date", None))
        harvested_date = attrs.get("harvested_date", getattr(self.instance, "harvested_date", None))

        if planted_date and harvested_date and harvested_date < planted_date:
            raise serializers.ValidationError({"harvested_date": "harvest date should be after planted date"})
        return attrs
