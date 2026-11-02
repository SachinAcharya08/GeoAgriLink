from drf_spectacular.utils import extend_schema
from rest_framework import response, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.farms.models import FarmHistorys, Farms
from apps.farms.serializers import FarmHistorySerializers, FarmSerializers
from apps.farms.services import FarmService


@extend_schema(tags=["Farm"])
class FarmModelViewsets(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FarmSerializers

    def get_queryset(self):
        return Farms.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"], url_path="fetch_gee_data")
    def fetch_gee_data(self, request):
        farm_id = request.query_params.get("farm_id")
        recorded_at = request.query_params.get("date")

        if not farm_id or not recorded_at:
            return response.Response({"error": "farm_id and recorded_at are required."}, status=400)

        try:
            farm_history = FarmService.fetch_farm_history_indexes(farm_id, recorded_at, days_back=30)
            serializer = self.get_serializer(farm_history)
            return response.Response(serializer.data)
        except Farms.DoesNotExist:
            return response.Response({"error": "Farm not found."}, status=404)


@extend_schema(tags=["Farm-History"])
class FarmHistoryModelViewsets(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    serializer_class = FarmHistorySerializers
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FarmHistorys.objects.filter(owner=self.request.user)

    @action(detail=True, methods=["get"], url_path="analyze_farm_history")
    def analyze_farm_history(self, request, pk=None):
        try:
            farm_history = FarmHistorys.objects.get(pk=pk)
            analysis_result = FarmService.analyze_farm_history(farm_history)
            return response.Response(analysis_result)
        except FarmHistorys.DoesNotExist:
            return response.Response({"error": "Farm history not found."}, status=404)
