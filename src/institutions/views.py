from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import EnvironmentalInstitution
from .serializers import (
    EnvironmentalInstitutionSerializer,
    InstitutionRegistrationSerializer,
)
from .services import InstitutionService


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
        colors_data = validated_data.pop("colors_input", [])

        try:
            # LLAMADA AL SERVICIO
            institution = InstitutionService.create_institution(
                data=validated_data, colors_list=colors_data
            )

            # Serializamos el resultado final (que ahora incluye los colores creados)
            output_serializer = self.get_serializer(institution)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RegisterInstitutionView(APIView):
    """
    Endpoint para que un representante registre su institución.
    Soporta multipart/form-data para subir el logo.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # Crucial para subir imágenes

    def post(self, request):
        serializer = InstitutionRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            colors = validated_data.pop("colors")

            try:
                # Llamada al servicio atómico
                institution = InstitutionService.register_institution(
                    data=validated_data, colors=colors, representative_user=request.user
                )

                # Devolvemos la institución creada usando el serializador de lectura estándar
                return Response(
                    EnvironmentalInstitutionSerializer(institution).data,
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApproveInstitutionView(APIView):
    """
    Endpoint dedicado para aprobar una institución.
    Ruta: POST /api/institutions/requests/<int:pk>/approve/
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            institution = InstitutionService.approve_institution_service(pk)
            # Retornamos la data actualizada
            serializer = EnvironmentalInstitutionSerializer(institution)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": "Error aprobando la institución", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
