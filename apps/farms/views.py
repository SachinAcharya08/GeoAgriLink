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
    permission_classes = [IsAuthenticated]
    serializer_class = FarmHistorySerializers

    def get_queryset(self):
        return FarmHistorys.objects.filter(owner=self.request.user)
