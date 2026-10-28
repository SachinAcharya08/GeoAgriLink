from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.ai_insights.models import AIInsight
from apps.ai_insights.serializers import AIInsightSerializers


class AIInsightModelviewsets(viewsets.ReadOnlyModelViewSet):
    serializer_class = AIInsightSerializers
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AIInsight.objects.filter(farm__owner=self.request.user).select_related("farm", "production_history")
