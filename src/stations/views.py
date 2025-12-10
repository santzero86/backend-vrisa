from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import MonitoringStation
from .serializers import CreateStationSerializer, MonitoringStationSerializer
from .services import approve_station_service, create_station, get_nearby_stations


class StationViewSet(viewsets.ModelViewSet):
    """
    Endpoint: /api/stations/
    Permite listar y gestionar las estaciones de monitoreo.
    """

    queryset = MonitoringStation.objects.all()
    serializer_class = MonitoringStationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Lógica híbrida:
        1. ?status=ACTIVE -> Público (Dashboard).
        2. Superuser -> Ve todo.
        3. Usuario con Institución -> Ve todas las estaciones de su institución.
        4. Usuario sin Institución (Station Admin suelto) -> Ve solo las que gestiona.
        """
        user = self.request.user
        queryset = super().get_queryset()
        
        # Obtener parámetro de filtro
        status_param = self.request.query_params.get("status")
        institution_param = self.request.query_params.get("institution")

        # Solicitud Pública para Dashboard (Solo Activas)
        if status_param == 'ACTIVE':
            if institution_param:
                queryset = queryset.filter(institution_id=institution_param)
            return queryset.filter(operative_status='ACTIVE')
        
        # Super administrador
        if user.is_superuser:
            if institution_param:
                return queryset.filter(institution_id=institution_param)
            return queryset
        
        if user.institution:
            return queryset.filter(institution=user.institution)
        
        # Filtrar por las que administra el usuario si no es superuser
        return queryset.filter(manager_user=user)
    
    def create(self, request, *args, **kwargs):
        """
        Crea una nueva estación de monitoreo.
        POST: /api/stations/
        Ejemplo de cuerpo: {
            "station_name": "Estación 1",
            "geographic_location_lat": -34.6037,
            "geographic_location_long": -58.3816,
            "address_reference": "Calle 70 Norte #3N-45, Cali",
            "institution_id": 5
        }
        """
        serializer = CreateStationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            station = create_station(serializer.validated_data, request.user.id)
            
            output_serializer = MonitoringStationSerializer(station)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Endpoint personalizado para aprobar una estación.
        POST: /api/stations/{id}/approve/
        """
        try:
            station = approve_station_service(pk)
            # Retornamos la data actualizada usando el serializador existente
            serializer = self.get_serializer(station)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": "Error aprobando la estación", "error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby(self, request):
        """
        Busca estaciones de monitoreo cercanas a una ubicación.
        GET: /api/stations/nearby/?lat=-34.6037&long=-58.3816&radius_km=10

        Query params:
            - lat: Latitud del punto de referencia (requerido)
            - long: Longitud del punto de referencia (requerido)
            - radius_km: Radio de búsqueda en kilómetros (opcional, default: 10)

        Returns:
            Lista de estaciones ordenadas por distancia, incluyendo la distancia en metros
        """
        try:
            # Obtener parámetros de la query
            lat = request.query_params.get('lat')
            long = request.query_params.get('long')
            radius_km = request.query_params.get('radius_km', 10)

            # Validar parámetros requeridos
            if not lat or not long:
                return Response(
                    {"detail": "Los parámetros 'lat' y 'long' son requeridos."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Convertir a float
            try:
                lat = float(lat)
                long = float(long)
                radius_km = float(radius_km)
            except ValueError:
                return Response(
                    {"detail": "Los parámetros deben ser números válidos."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar rangos
            if lat < -90 or lat > 90:
                return Response(
                    {"detail": "La latitud debe estar entre -90 y 90."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if long < -180 or long > 180:
                return Response(
                    {"detail": "La longitud debe estar entre -180 y 180."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if radius_km <= 0:
                return Response(
                    {"detail": "El radio debe ser mayor a 0."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Buscar estaciones cercanas
            nearby_stations = get_nearby_stations(lat, long, radius_km)

            # Serializar resultados
            serializer = MonitoringStationSerializer(nearby_stations, many=True)

            # Agregar distancia a cada resultado (en metros)
            results = []
            for i, station_data in enumerate(serializer.data):
                station_with_distance = dict(station_data)
                # La distancia viene en metros por defecto
                station_with_distance['distance_m'] = round(nearby_stations[i].distance.m, 2)
                results.append(station_with_distance)

            return Response({
                "count": len(results),
                "reference_point": {"lat": lat, "long": long},
                "radius_km": radius_km,
                "stations": results
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"Error al buscar estaciones cercanas: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
