from drf_spectacular.utils import extend_schema
from google.auth.exceptions import RefreshError
from rest_framework import response, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.core.translation import TranslationError, translate_payload
from apps.crops.serializers import ProductionHistorySerializers
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
            serializer = FarmHistorySerializers(farm_history)
            return response.Response(serializer.data, status=200)
        except Farms.DoesNotExist:
            return response.Response({"error": "Farm not found."}, status=404)
        except RefreshError:
            return response.Response(
                {"error": "Earth Engine authentication failed. Refresh the service-account key."},
                status=502,
            )
        except FileNotFoundError as exc:
            return response.Response({"error": str(exc)}, status=502)

    @action(detail=True, methods=["get"], url_path="analyze_farm_gee")
    def analyze_farm_gee(self, request, pk=None):

        try:
            farm = self.get_queryset().get(pk=pk)

            result = FarmService.analyze_farm_gee(farm)
            result = translate_payload(result, request.query_params.get("language", "en"))

            return response.Response(
                result,
                status=200,
            )

        except Farms.DoesNotExist:
            return response.Response(
                {"error": "Farm not found."},
                status=404,
            )

        except FarmHistorys.DoesNotExist:
            return response.Response(
                {"error": "Farm history not found."},
                status=404,
            )

        except RuntimeError as exc:
            return response.Response(
                {"error": str(exc)},
                status=502,
            )
        except TranslationError as exc:
            return response.Response({"error": str(exc)}, status=502)

    @action(detail=True, methods=["get"], url_path="production-history")
    def farm_production_history(self, request, pk=None):
        try:
            farm = self.get_queryset().get(pk=pk)
            production_history = farm.production_history.all()
            serializer = ProductionHistorySerializers(production_history, many=True)
            return response.Response(serializer.data)

        except Farms.DoesNotExist:
            return response.Response(
                {"error": "Farm not found."},
                status=404,
            )


@extend_schema(tags=["Farm-History"])
class FarmHistoryModelViewsets(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    serializer_class = FarmHistorySerializers
    permission_classes = [IsAuthenticated]
    filterset_fields = ["farm", "recorded_at"]

    def get_queryset(self):
        return FarmHistorys.objects.filter(farm__owner=self.request.user).select_related("farm")
