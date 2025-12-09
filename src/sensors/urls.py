from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import MaintenanceLogViewSet, SensorViewSet

router = DefaultRouter()
router.register(r'devices', SensorViewSet, basename='sensor')
router.register(r'maintenance', MaintenanceLogViewSet, basename='maintenance')

urlpatterns = [
    path('', include(router.urls)),
]