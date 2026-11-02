from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.base_model import BaseModel

CROP_CATEGORIES = [
    ("cereals", "Cereals"),
    ("vegetables", "Vegetables"),
    ("fruits", "Fruits"),
    ("pulses", "Pulses"),
    ("oilseeds", "Oilseeds"),
    ("cash_crops", "Cash Crops"),
    ("spices", "Spices"),
    ("other", "Other"),
]


class Crops(BaseModel):
    name = models.CharField(max_length=500)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="crops",
        null=True,
        blank=True,
    )
    category = models.CharField(max_length=250, choices=CROP_CATEGORIES, default="other")
    image = models.ImageField(upload_to="crops/", blank=True, null=True)
    desc = models.TextField(max_length=1000)

    class Meta:
        db_table = "Crops"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductionHistory(BaseModel):
    crop = models.ForeignKey("crops.Crops", on_delete=models.PROTECT, related_name="production_history")
    farm = models.ForeignKey("farms.Farms", on_delete=models.CASCADE, related_name="production_history")
    planted_date = models.DateTimeField()
    harvested_date = models.DateTimeField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=20, default="kg")
    remarks = models.TextField(max_length=500, blank=True)

    class Meta:
        db_table = "ProductionHistory"
        ordering = ["-planted_date"]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="production_quantity_positive"),
            models.CheckConstraint(
                condition=models.Q(harvested_date__isnull=True)
                | models.Q(harvested_date__gte=models.F("planted_date")),
                name=("harvest_after_planting"),
            ),
        ]

    def __str__(self):
        return f"{self.crop.name} - {self.farm.name}"

    def clean(self):
        super().clean()

        if self.planted_date and self.harvested_date and self.harvested_date < self.planted_date:
            raise ValidationError({"harvested_date": "harvest date can't be before planting date."})
