from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import StationViewSet

router = DefaultRouter()
router.register(r'', StationViewSet, basename='stations')

urlpatterns = [
    path('', include(router.urls)),
]