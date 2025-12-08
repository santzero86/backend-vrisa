from django.shortcuts import render

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Measurement, VariableCatalog
from .serializers import MeasurementSerializer, VariableCatalogSerializer
from .services import MeasurementService
from rest_framework.decorators import action
from django.utils.dateparse import parse_datetime
from src.sensors.models import Sensor

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
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Endpoint optimizado para gráficas.
        Params: station_id, variable_code, start_date, end_date
        """
        station_id = request.query_params.get('station_id')
        variable_code = request.query_params.get('variable_code')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Filtro base
        queryset = self.queryset
        
        if station_id:
            # Filtramos mediciones cuyos sensores pertenecen a esa estación
            queryset = queryset.filter(sensor__station_id=station_id)
        
        if variable_code:
            queryset = queryset.filter(variable__code=variable_code)

        if start_date and end_date:
            try:
                # Asegurarse que el formato sea YYYY-MM-DD o ISO
                queryset = queryset.filter(measure_date__range=[start_date, end_date])
            except ValueError:
                return Response({"error": "Formato de fecha inválido"}, status=400)

        # Optimizamos la consulta para traer solo lo necesario
        # Ordenamos por fecha ascendente para la gráfica
        data = queryset.values(
            'measure_date', 
            'value', 
            'sensor__serial_number'
        ).order_by('measure_date')

        return Response(list(data), status=status.HTTP_200_OK)