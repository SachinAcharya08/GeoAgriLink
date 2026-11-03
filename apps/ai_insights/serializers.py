from rest_framework import serializers

from apps.ai_insights.models import AIInsight
from apps.core.translation import TranslationError, translate_payload
from apps.farms.models import Farms


class AIInsightSerializers(serializers.ModelSerializer):
    translated_result = serializers.SerializerMethodField()

    class Meta:
        model = AIInsight
        fields = [
            "id",
            "farm",
            "production_history",
            "image",
            "insight_type",
            "result",
            "translated_result",
            "model_version",
            "generated_at",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "updated_at", "created_at", "generated_at", "result", "model_version"]

    def get_translated_result(self, obj):
        request = self.context.get("request")
        language = request.query_params.get("language", "en") if request else "en"
        try:
            return translate_payload(obj.result, language)
        except TranslationError as exc:
            raise serializers.ValidationError({"language": str(exc)}) from exc

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


class CropDiseaseDetectionSerializer(serializers.Serializer):
    farm = serializers.PrimaryKeyRelatedField(queryset=Farms.objects.all())
    image = serializers.ImageField()

    def validate_farm(self, value):
        if value.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("You do not own this farm.")

        return value

    def validate_image(self, value):
        allowed_types = ["image/jpeg", "image/png", "image/webp"]

        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only JPEG, PNG and WebP images are supported.")

        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image size cannot exceed 5 MB.")

        return value
