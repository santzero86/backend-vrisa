from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Measurement, VariableCatalog
from .serializers import MeasurementSerializer, VariableCatalogSerializer
from .services import MeasurementService
from rest_framework.decorators import action
from django.utils.dateparse import parse_datetime
from src.sensors.models import Sensor
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from src.stations.models import MonitoringStation
from .report_generator import PDFReportGenerator
import io

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
            measurement = MeasurementService.create_measurement(
                serializer.validated_data
            )
            output_serializer = self.get_serializer(measurement)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def history(self, request):
        """
        Endpoint optimizado para gráficas.
        Query Params:
            station_id,
            variable_code,
            start_date,
            end_date
        """
        station_id = request.query_params.get("station_id")
        variable_code = request.query_params.get("variable_code")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not all([station_id, variable_code, start_date, end_date]):
            return Response(
                {
                    "error": "Faltan parámetros (station_id, variable_code, start_date, end_date)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filtro base
        queryset = self.queryset.filter(
            sensor__station_id=station_id,
            variable__code=variable_code,
            measure_date__date__range=[
                start_date,
                end_date,
            ],  # __date__range ignora la hora para abarcar todo el día
        )

        data = queryset.values("measure_date", "value").order_by("measure_date")

        return Response(list(data), status=status.HTTP_200_OK)

class AirQualityReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        station_id = request.query_params.get('station_id')
        date = request.query_params.get('date') # Formato YYYY-MM-DD

        if not station_id or not date:
            return Response({"error": "station_id y date son requeridos"}, status=400)

        station = get_object_or_404(MonitoringStation, pk=station_id)
        
        buffer = io.BytesIO()
        report = PDFReportGenerator(buffer)
        report.generate_air_quality_report(station, date)
        
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f'calidad_aire_{date}.pdf')

class TrendsReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        station_id = request.query_params.get('station_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not station_id or not start_date or not end_date:
            return Response({"error": "Faltan parámetros"}, status=400)

        station = get_object_or_404(MonitoringStation, pk=station_id)

        buffer = io.BytesIO()
        report = PDFReportGenerator(buffer)
        report.generate_trends_report(station, start_date, end_date)
        
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='tendencias.pdf')

class AlertsReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        station_id = request.query_params.get('station_id') # Opcional

        buffer = io.BytesIO()
        report = PDFReportGenerator(buffer)
        report.generate_alerts_report(station_id)
        
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='alertas_criticas.pdf')    
