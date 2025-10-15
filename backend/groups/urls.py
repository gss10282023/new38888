from rest_framework.routers import DefaultRouter

from .views import GroupViewSet

app_name = "groups"

router = DefaultRouter()
router.register("", GroupViewSet, basename="group")

urlpatterns = router.urls
