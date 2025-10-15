from django.urls import path

from .views import MessageViewSet

app_name = "chat"

message_list = MessageViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

urlpatterns = [
    path("groups/<str:group_id>/messages", message_list, name="group-messages"),
]
