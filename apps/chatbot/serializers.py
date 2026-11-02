from rest_framework import serializers

from apps.chatbot.models import ChatConversation, ChatMessage


class ChatConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatConversation
        fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "role",
            "content",
            "metadata",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "role",
            "content",
            "metadata",
            "created_at",
        ]
