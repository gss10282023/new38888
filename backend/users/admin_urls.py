from django.urls import path

from .views import AdminUserViewSet, admin_stats

app_name = "admin_panel"

admin_user_list = AdminUserViewSet.as_view({"get": "list", "post": "create"})
admin_user_detail = AdminUserViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)
admin_user_status = AdminUserViewSet.as_view({"put": "update_status", "patch": "update_status"})
admin_user_filters = AdminUserViewSet.as_view({"get": "filter_options"})
admin_user_export = AdminUserViewSet.as_view({"get": "export"})

urlpatterns = [
    path("stats/", admin_stats, name="stats"),
    path("users/", admin_user_list, name="user-list"),
    path("users/<int:pk>/", admin_user_detail, name="user-detail"),
    path("users/<int:pk>/status/", admin_user_status, name="user-update-status"),
    path("users/filters/", admin_user_filters, name="user-filters"),
    path("users/export/", admin_user_export, name="user-export"),
]
