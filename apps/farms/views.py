from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.farms.models import FarmHistorys, Farms
from apps.farms.serializers import FarmHistorySerializers, FarmSerializers


class FarmModelViewsets(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FarmSerializers

    def get_queryset(self):
        return Farms.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FarmHistoryModelViewsets(viewsets.ModelViewSet):
    serializer_class = FarmHistorySerializers
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return FarmHistorys.objects.none()

        return FarmHistorys.objects.filter(farm__owner=self.request.user).select_related("farm")
