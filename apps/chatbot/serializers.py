from rest_framework import serializers

from apps.chatbot.models import ChatConversation, ChatMessage


class ChatConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatConversation
        fields = ["id", "title", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "metadata", "created_at"]
        read_only_fields = fields


class ChatRequestSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000)
    conversation = serializers.PrimaryKeyRelatedField(queryset=ChatConversation.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request:
            self.fields["conversation"].queryset = ChatConversation.objects.filter(user=request.user)


class ConfirmActionSerializer(serializers.Serializer):
    action_id = serializers.UUIDField()
    approve = serializers.BooleanField()
