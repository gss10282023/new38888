from django.urls import path

from .views import MyStudentSupervisorViewSet, UserViewSet

app_name = "users"

user_me_view = UserViewSet.as_view(
    {
        "get": "me",
        "put": "update_me",
        "patch": "update_me",
    }
)

user_supervisors_list_view = MyStudentSupervisorViewSet.as_view(
    {
        "get": "list",
    }
)

user_supervisors_detail_view = MyStudentSupervisorViewSet.as_view(
    {
        "patch": "partial_update",
    }
)

urlpatterns = [
    path("me/", user_me_view, name="me"),
    path("me/supervisors/", user_supervisors_list_view, name="me-supervisors"),
    path(
        "me/supervisors/<int:pk>/",
        user_supervisors_detail_view,
        name="me-supervisor-detail",
    ),
]
