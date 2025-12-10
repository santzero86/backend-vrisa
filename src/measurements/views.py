import io
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from src.stations.models import MonitoringStation
from .models import Measurement, VariableCatalog
from .serializers import MeasurementSerializer, VariableCatalogSerializer
from .services import AQICalculatorService, MeasurementService, PDFReportGenerator


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
            measure_date__range=[
                start_date,
                end_date,
            ],  # __date__range ignora la hora para abarcar todo el día
        )

        data = queryset.values("measure_date", "value").order_by("measure_date")

        return Response(list(data), status=status.HTTP_200_OK)


class AirQualityReportView(APIView):
    """
    Genera el reporte ejecutivo estadístico.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        station_id = request.query_params.get('station_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        single_date = request.query_params.get('date')
        
        # Lógica de fechas
        if not start_date and single_date:
            start_date = single_date
            end_date = single_date # El filtro range incluye el día completo si es date object
        elif not start_date or not end_date:
             return Response({"error": "Se requiere start_date y end_date (o date)"}, status=400)
        
        # Resolver Estación (Objeto o None para Global)
        station = None
        if station_id and station_id not in ["", "null", "undefined"]:
            station = get_object_or_404(MonitoringStation, pk=station_id)
        
        variable_code = request.query_params.get('variable_code')
        
        buffer = io.BytesIO()
        report = PDFReportGenerator(buffer)
        report.generate_air_quality_report(station, start_date, end_date, variable_code)
        buffer.seek(0)
        
        if station:
            scope_str = station.station_name.replace(" ", "_").lower()
        else:
            scope_str = "cali_consolidated" 
        
        today_str = timezone.now().strftime('%Y%m%d')
        filename = f"{today_str}_vrisa_general_{scope_str}_report.pdf"
        
        return FileResponse(buffer, as_attachment=True, filename=filename)


class TrendsReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        station_id = request.query_params.get("station_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not station_id or not start_date or not end_date:
            return Response({"error": "Faltan parámetros"}, status=400)

        station = get_object_or_404(MonitoringStation, pk=station_id)

        buffer = io.BytesIO()
        report = PDFReportGenerator(buffer)
        report.generate_trends_report(station, start_date, end_date)

        buffer.seek(0)

        clean_name = station.station_name.replace(" ", "_")
        filename = f"{start_date}_to_{end_date}-{clean_name}-vrisa-trends.pdf"

        return FileResponse(buffer, as_attachment=True, filename=filename)

class AlertsReportView(APIView):
    """
    Vista para generar el reporte de Alertas Críticas.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        station_id = request.query_params.get('station_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        #  Validar fechas
        if not start_date or not end_date:
            return Response({"error": "Se requieren start_date y end_date"}, status=400)
        
        station = None
        if station_id and station_id not in ["", "null", "undefined"]:
            station = get_object_or_404(MonitoringStation, pk=station_id)
        
        # Generar contenido del reporte
        buffer = io.BytesIO()
        report = PDFReportGenerator(buffer)
        report.generate_alerts_report(station, start_date, end_date)
        buffer.seek(0)
        
        # Formato: YYYYMMDD_vrisa_alerts_report.pdf
        today_str = timezone.now().strftime('%Y%m%d')
        scope_str = station.station_name.replace(" ", "_").lower() if station else "cali_consolidated"
        filename = f"{today_str}_vrisa_{scope_str}_alerts_report.pdf"

        return FileResponse(buffer, as_attachment=True, filename=filename)


class CurrentAQIView(APIView):
    """
    Vista para obtener el Índice de Calidad del Aire (AQI) en tiempo real.
    Endpoint: GET /api/measurements/aqi/current/?station_id=1
    Calcula el AQI actual basado en las mediciones más recientes de contaminantes:
    - PM2.5, PM10, O3, CO, NO2, SO2
    Responde con:
    - Valor de AQI
    - Categoría (Good, Moderate, Unhealthy, etc.)
    - Contaminante dominante (el que determinó el AQI)
    - Sub-índices de cada contaminante
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        station_id = request.query_params.get('station_id')
        
        station_name = "Cali (Todas las estaciones)"
        
        # Validación: Si viene ID, verificamos que la estación exista
        if station_id:
            station = get_object_or_404(MonitoringStation, pk=station_id)
            station_name = station.station_name

        try:
            s_id = int(station_id) if station_id else None
            
            aqi_data = AQICalculatorService.calculate_aqi_for_station(station_id=s_id)

            aqi_data['station_name'] = station_name
            
            # Si se consultó una estación específica, agregamos su ID
            if s_id:
                aqi_data['station_id'] = s_id

            return Response(aqi_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Error al calcular AQI", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
