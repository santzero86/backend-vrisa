from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import StationAffiliationViewSet, StationViewSet

router = DefaultRouter()
router.register(r'', StationViewSet, basename='stations')
router.register(r'affiliations', StationAffiliationViewSet, basename='affiliations')

urlpatterns = [
    path('', include(router.urls)),
]