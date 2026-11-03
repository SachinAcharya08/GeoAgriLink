import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.chatbot.models import ChatConversation, ChatMessage, PendingAction
from apps.chatbot.serializers import (
    ChatConversationSerializer,
    ChatMessageSerializer,
    ChatRequestSerializer,
    ConfirmActionSerializer,
    VoiceChatRequestSerializer,
)
from apps.chatbot.services.gemini import GeminiService
from apps.chatbot.services.gemini_transcription import (
    TranscriptionError,
    transcribe_audio,
)
from apps.chatbot.tools.writes import EXECUTORS

logger = logging.getLogger(__name__)


@extend_schema(tags=["Chatbots"])
class ChatConversationViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ChatConversationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return ChatConversation.objects.filter(user=self.request.user)

    @extend_schema(responses=ChatMessageSerializer(many=True))
    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        serializer = ChatMessageSerializer(conversation.messages.all(), many=True)
        return Response(serializer.data)

    @extend_schema(request=ChatRequestSerializer)
    @action(detail=False, methods=["post"])
    def chat(self, request):
        serializer = ChatRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        conversation = serializer.validated_data.get("conversation")
        text = serializer.validated_data["content"]
        history = list(conversation.messages.all()) if conversation else []

        try:
            reply, pending_id = GeminiService().generate_response(history, text, request.user)
        except Exception:
            return Response(
                {"detail": "The assistant is unavailable. Try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        with transaction.atomic():
            if conversation is None:
                conversation = ChatConversation.objects.create(user=request.user, title=text[:60])
            ChatMessage.objects.create(conversation=conversation, role=ChatMessage.Role.USER, content=text)
            assistant_msg = ChatMessage.objects.create(
                conversation=conversation,
                role=ChatMessage.Role.ASSISTANT,
                content=reply,
                metadata={"pending_action_id": pending_id} if pending_id else {},
            )

            pending = None
            if pending_id:
                pending = PendingAction.objects.filter(id=pending_id, user=request.user).first()
                if pending:
                    pending.conversation = conversation
                    pending.save(update_fields=["conversation", "updated_at"])

        return Response(
            {
                "conversation_id": conversation.id,
                "message": ChatMessageSerializer(assistant_msg).data,
                "pending_action": ({"id": str(pending.id), "summary": pending.summary} if pending else None),
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(request=VoiceChatRequestSerializer)
    @action(detail=False, methods=["post"], url_path="voice", parser_classes=[MultiPartParser])
    def voice(self, request):
        serializer = VoiceChatRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        try:
            text = transcribe_audio(serializer.validated_data["audio"])
            conversation = serializer.validated_data.get("conversation")
            history = list(conversation.messages.all()) if conversation else []
            reply, pending_id = GeminiService().generate_response(history, text, request.user)
        except TranscriptionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception:
            logger.exception("Voice chat processing failed.")
            return Response(
                {"detail": "The assistant is unavailable. Try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        with transaction.atomic():
            if conversation is None:
                conversation = ChatConversation.objects.create(user=request.user, title=text[:60])
            ChatMessage.objects.create(
                conversation=conversation,
                role=ChatMessage.Role.USER,
                content=text,
                metadata={"source": "voice", "transcription_model": settings.GEMINI_MODEL},
            )
            assistant_msg = ChatMessage.objects.create(
                conversation=conversation,
                role=ChatMessage.Role.ASSISTANT,
                content=reply,
                metadata={"pending_action_id": pending_id} if pending_id else {},
            )

        return Response(
            {
                "conversation_id": conversation.id,
                "transcript": text,
                "message": ChatMessageSerializer(assistant_msg).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(request=ConfirmActionSerializer)
    @action(detail=False, methods=["post"], url_path="chat/confirm")
    def confirm(self, request):
        serializer = ConfirmActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve = serializer.validated_data["approve"]

        with transaction.atomic():
            pending = (
                PendingAction.objects.select_for_update()
                .filter(id=serializer.validated_data["action_id"], user=request.user)
                .first()
            )
            if not pending:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            if pending.status != PendingAction.Status.PENDING:
                return Response({"detail": "Already handled."}, status=status.HTTP_409_CONFLICT)
            if pending.expires_at < timezone.now():
                pending.status = PendingAction.Status.EXPIRED
                pending.save(update_fields=["status", "updated_at"])
                return Response(
                    {"detail": "This request expired. Please ask me again."},
                    status=status.HTTP_410_GONE,
                )

            if not approve:
                pending.status = PendingAction.Status.CANCELLED
                text = "Okay, I cancelled it."
            else:
                try:
                    with transaction.atomic():  # savepoint: a failed write rolls back cleanly
                        text = EXECUTORS[pending.action](pending)
                    pending.status = PendingAction.Status.CONFIRMED
                except ValueError as e:
                    text = str(e)
                    pending.status = PendingAction.Status.FAILED
                except ValidationError:
                    text = "Some details were not valid. Please try again."
                    pending.status = PendingAction.Status.FAILED
                except Exception:
                    logger.exception("Action %s failed", pending.action)
                    text = "Sorry, something went wrong. Please try again."
                    pending.status = PendingAction.Status.FAILED

            pending.save(update_fields=["status", "updated_at"])

            msg = None
            if pending.conversation_id:
                msg = ChatMessage.objects.create(
                    conversation_id=pending.conversation_id,
                    role=ChatMessage.Role.ASSISTANT,
                    content=text,
                    metadata={"action": pending.action, "result": pending.status},
                )

        return Response(
            {
                "status": pending.status,
                "conversation_id": pending.conversation_id,
                "message": ChatMessageSerializer(msg).data if msg else {"content": text},
            }
        )
