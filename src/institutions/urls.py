from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InstitutionViewSet, IntegrationRequestViewSet

router = DefaultRouter()
# Ruta: /api/institutions/institutes/
# Soporta: GET (Lista/Detalle), POST (Transaccional vía Service), PUT, PATCH, DELETE.
# Nota: El POST espera 'colors_input' para crear colores automáticamente.
router.register(r'institutes', InstitutionViewSet, basename='institute')

# Ruta: /api/institutions/requests/
# Soporta: CRUD estándar.
# Acción Extra: POST /api/institutions/requests/{id}/approve/ (Solo Admins, aprueba y firma).
router.register(r'requests', IntegrationRequestViewSet, basename='integration-request')

urlpatterns = [
    path('', include(router.urls)),
]