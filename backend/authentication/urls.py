from django.urls import path

from . import views


app_name = "authentication"

urlpatterns = [
    path("magic-link/", views.request_magic_link, name="request-magic-link"),
    path("verify-otp/", views.verify_otp, name="verify-otp"),
    path("verify/", views.verify_magic_link, name="verify-magic-link"),
    path("refresh/", views.refresh_token, name="refresh-token"),
]
