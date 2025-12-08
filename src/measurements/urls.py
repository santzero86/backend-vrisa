from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MeasurementViewSet, VariableCatalogViewSet,  AirQualityReportView, TrendsReportView, AlertsReportView

router = DefaultRouter()
router.register(r'variables', VariableCatalogViewSet, basename='variables')
router.register(r'data', MeasurementViewSet, basename='measurements')

urlpatterns = [
    path('', include(router.urls)),
    path('reports/air-quality/', AirQualityReportView.as_view(), name='report-air-quality'),
    path('reports/trends/', TrendsReportView.as_view(), name='report-trends'),
    path('reports/alerts/', AlertsReportView.as_view(), name='report-alerts'),
] 