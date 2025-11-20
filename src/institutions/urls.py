from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InstitutionViewSet, IntegrationRequestViewSet

router = DefaultRouter()
router.register(r'institutes', InstitutionViewSet, basename='institute')
router.register(r'requests', IntegrationRequestViewSet, basename='integration-request')

urlpatterns = [
    path('', include(router.urls)),
]