from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import EnvironmentalInstitution, IntegrationRequest
from django.utils import timezone
from .serializers import EnvironmentalInstitutionSerializer, IntegrationRequestSerializer

class InstitutionViewSet(viewsets.ModelViewSet):
    # Maneja todo el CRUD de Instituciones.
    # Automáticamente provee: listar, crear, detalle, actualizar, borrar.
    queryset = EnvironmentalInstitution.objects.all()
    serializer_class = EnvironmentalInstitutionSerializer
    permission_classes = [permissions.IsAuthenticated]

class IntegrationRequestViewSet(viewsets.ModelViewSet):
    #Maneja las solicitudes de integración.
    queryset = IntegrationRequest.objects.all()
    serializer_class = IntegrationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Al crear la solicitud, validamos lógica extra si es necesario
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        integration_request = self.get_object()
        integration_request.request_status = IntegrationRequest.RequestStatus.APPROVED
        integration_request.reviewed_by = request.user 
        integration_request.review_date = timezone.now()
        integration_request.save()
        return Response({'status': 'Solicitud aprobada'})