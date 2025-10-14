from django.urls import path

from .views import UserViewSet

app_name = "users"

user_me_view = UserViewSet.as_view(
    {
        "get": "me",
        "put": "update_me",
        "patch": "update_me",
    }
)

urlpatterns = [
    path("me/", user_me_view, name="me"),
]
