import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created at"), help_text=_("The timestamp when this object was created.")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Updated at"), help_text=_("The timestamp when this object was last updated.")
    )
    is_active = models.BooleanField(
        default=True, verbose_name=_("Active"), help_text=_("Marks whether this object is active or soft deleted.")
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.__class__.__name__} (ID: {self.pk})"
