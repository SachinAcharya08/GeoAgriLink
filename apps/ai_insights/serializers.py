from rest_framework import serializers

from apps.ai_insights.models import AIInsight


class AIInsightSerializers(serializers.ModelSerializer):
    class Meta:
        model = AIInsight
        fields = "__all__"
        read_only_fields = ["id", "updated_at", "created_at", "generated_at", "result", "model_version"]

    def validate(self, attrs):
        farm = attrs.get(
            "farm",
            getattr(self.instance, "farm", None),
        )
        production_history = attrs.get("production_history", getattr(self.instance, "production_history", None))

        if farm and production_history and production_history.farm_id != farm.id:
            raise serializers.ValidationError(
                {"production_history": ("The production history must belong to the selected farm.")}
            )

        return attrs
