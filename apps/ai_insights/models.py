from django.db import models

from apps.core.base_model import BaseModel

INSIGHT_TYPES = [
    ("crop_health", "Crop Health"),
    ("disease_risk", "Disease Risk"),
    ("nutrient_deficiency", "Nutrient Deficiency"),
    ("weather", "Weather"),
    ("other", "Other"),
]


class AIInsight(BaseModel):
    farm = models.ForeignKey("farms.Farms", on_delete=models.CASCADE, related_name="ai_insights")
    production_history = models.ForeignKey(
        "crops.ProductionHistory", on_delete=models.SET_NULL, related_name="ai_insights", null=True, blank=True
    )
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPES)
    result = models.JSONField()
    model_version = models.CharField(max_length=100)
    generated_at = models.DateTimeField()

    class Meta:
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["farm", "-generated_at"]),
            models.Index(
                fields=["insight_type", "-generated_at"],
            ),
        ]

    def __str__(self):
        return f"{self.insight_type} - {self.farm_id}"
