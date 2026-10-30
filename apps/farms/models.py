from django.conf import settings
from django.db import models

from apps.core.base_model import BaseModel


class Farms(BaseModel):
    name = models.CharField(max_length=255)
    boundary = models.JSONField()
    address = models.CharField(max_length=500)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="farms")
    area = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "Farms"


class FarmHistorys(BaseModel):
    farm = models.ForeignKey("farms.Farms", on_delete=models.CASCADE, related_name="history")
    recorded_at = models.DateField()
    ci_rededge = models.FloatField(null=True, blank=True)
    evi = models.FloatField(null=True, blank=True)
    lswi = models.FloatField(null=True, blank=True)
    ndre = models.FloatField(null=True, blank=True)
    ndvi = models.FloatField(null=True, blank=True)
    ndwi = models.FloatField(null=True, blank=True)
    lst = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=100, default="GEE")

    def __str__(self):
        return f"{self.farm.name} - {self.recorded_at}"

    class Meta:
        db_table = "FarmHistorys"
        unique_together = ("farm", "recorded_at")
