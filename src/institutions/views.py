from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import EnvironmentalInstitution, IntegrationRequest
from .serializers import EnvironmentalInstitutionSerializer, IntegrationRequestSerializer
from .services import InstitutionService, IntegrationRequestService

class InstitutionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión de Instituciones Ambientales.
    Rutas principales:
    - GET /api/institutions/institutes/: Lista todas las instituciones.
    - POST /api/institutions/institutes/: Crea una institución y sus colores (Transaccional).
    """
    queryset = EnvironmentalInstitution.objects.all()
    serializer_class = EnvironmentalInstitutionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Sobrescribe el método create para delegar la lógica compleja al InstitutionService.
        Separa los datos del modelo principal de la lista de colores input.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Separamos los datos del modelo principal y los datos extra (colores)
        validated_data = serializer.validated_data
        colors_data = validated_data.pop('colors_input', [])

        try:
            # LLAMADA AL SERVICIO
            institution = InstitutionService.create_institution(
                data=validated_data, 
                colors_list=colors_data
            )
            
            # Serializamos el resultado final (que ahora incluye los colores creados)
            output_serializer = self.get_serializer(institution)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class IntegrationRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión de Solicitudes de Integración.
    Incluye endpoints estándar CRUD y acciones personalizadas para flujos de aprobación.
    """
    queryset = IntegrationRequest.objects.all()
    serializer_class = IntegrationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Crea una solicitud utilizando el servicio para validar reglas de negocio (duplicidad).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # LLAMADA AL SERVICIO DE CREACIÓN
            req_instance = IntegrationRequestService.create_request(serializer.validated_data)
            output_serializer = self.get_serializer(req_instance)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            
        except DjangoValidationError as e:
             return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """
        Acción personalizada para aprobar una solicitud.
        Endpoint: POST /api/institutions/requests/{id}/approve/
        Solo accesible por administradores. Asigna fecha de revisión y revisor automáticamente.
        """
        try:
            # LLAMADA AL SERVICIO DE APROBACIÓN
            IntegrationRequestService.approve_request(pk, request.user)
            return Response({'status': 'Solicitud aprobada correctamente'})
            
        except DjangoValidationError as e:
             return Response({"detail": e.messages}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)