from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MeasurementViewSet, VariableCatalogViewSet

router = DefaultRouter()
router.register(r'variables', VariableCatalogViewSet, basename='variables')
router.register(r'data', MeasurementViewSet, basename='measurements')

urlpatterns = [
    path('', include(router.urls)),
] 