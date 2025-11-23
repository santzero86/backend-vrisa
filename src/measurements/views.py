from django.shortcuts import render

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Measurement, VariableCatalog
from .serializers import MeasurementSerializer, VariableCatalogSerializer
from .services import MeasurementService

class VariableCatalogViewSet(viewsets.ModelViewSet):
    """
    Endpoint: /api/measurements/variables/
    Gestión del catálogo de variables.
    Permite listar, crear y editar los tipos de contaminantes o variables climáticas.
    Permisos:
        - Requiere autenticación.
        - (TODO: Idealmente solo Administradores deberían poder crear/editar/borrar).
    """
    queryset = VariableCatalog.objects.all()
    serializer_class = VariableCatalogSerializer
    permission_classes = [permissions.IsAuthenticated]

class MeasurementViewSet(viewsets.ModelViewSet):
    """
    Endpoint: /api/measurements/data/
    Gestión de los datos recolectados (Mediciones).
    Permite la ingesta de datos y la consulta histórica.
    """
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Sobrescribe el método POST para delegar la lógica al Service Layer.
        Maneja la traducción de excepciones de negocio (ValidationError) 
        a respuestas HTTP estandarizadas (400 Bad Request).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # La creación al servicio para validar reglas, es delegada a services.py.
            measurement = MeasurementService.create_measurement(serializer.validated_data)
            output_serializer = self.get_serializer(measurement)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            
        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
