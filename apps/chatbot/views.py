from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.chatbot.models import ChatConversation
from apps.chatbot.serializers import (
    ChatConversationSerializer,
    ChatMessageSerializer,
)


@extend_schema(tags=["Chatbots"])
class ChatConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ChatConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatConversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        conversation = self.get_object()

        messages = conversation.messages.all()

        serializer = ChatMessageSerializer(
            messages,
            many=True,
        )

        return Response(serializer.data)
