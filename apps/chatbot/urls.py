from rest_framework.routers import DefaultRouter

from apps.chatbot.views import ChatConversationViewSet

router = DefaultRouter()

router.register(
    "conversations",
    ChatConversationViewSet,
    basename="chat-conversation",
)

urlpatterns = router.urls
