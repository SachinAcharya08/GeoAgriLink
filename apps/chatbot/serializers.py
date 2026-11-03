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
        fields = ["id", "conversation", "role", "content", "metadata", "created_at"]
        read_only_fields = fields


class ChatRequestSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000)
    conversation = serializers.PrimaryKeyRelatedField(queryset=ChatConversation.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request:
            self.fields["conversation"].queryset = ChatConversation.objects.filter(user=request.user)


class VoiceChatRequestSerializer(ChatRequestSerializer):
    content = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    audio = serializers.FileField()

    def validate_audio(self, value):
        return validate_audio_file(value)


class TranscriptionPreviewRequestSerializer(serializers.Serializer):
    audio = serializers.FileField()

    def validate_audio(self, value):
        return validate_audio_file(value)


def validate_audio_file(value):
    allowed_types = {
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp4",
        "audio/x-m4a",
        "audio/ogg",
        "audio/webm",
    }
    if value.content_type not in allowed_types:
        raise serializers.ValidationError("Unsupported audio type.")
    if value.size > 10 * 1024 * 1024:
        raise serializers.ValidationError("Audio file cannot exceed 10 MB.")
    return value


class ConfirmActionSerializer(serializers.Serializer):
    action_id = serializers.UUIDField()
    approve = serializers.BooleanField()
