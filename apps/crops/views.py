from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.crops.models import Crops, ProductionHistory
from apps.crops.serializers import CropSerializers, ProductionHistorySerializers


@extend_schema(tags=["Crop"])
class CropModelViewsets(viewsets.ModelViewSet):
    queryset = Crops.objects.all()
    serializer_class = CropSerializers
    permission_classes = [IsAuthenticated]


@extend_schema(tags=["Crop-Production-History"])
class ProductionHistoryModelViewset(viewsets.ModelViewSet):
    serializer_class = ProductionHistorySerializers
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductionHistory.objects.filter(farm__owner=self.request.user).select_related("crop", "farm")

    def perform_create(self, serializer):
        farm = serializer.validated_data["farm"]
        if farm.owner_id != self.request.user.pk:
            raise PermissionDenied("you don't own this farm")
        serializer.save()
