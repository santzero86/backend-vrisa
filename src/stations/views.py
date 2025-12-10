from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import MonitoringStation
from .serializers import CreateStationSerializer, MonitoringStationSerializer
from .services import create_station, approve_station_service 


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
        Opcional: Filtrar solo estaciones activas para usuarios normales,
        o todas para administradores.
        """
        queryset = super().get_queryset()
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(operative_status=status)
        return queryset
    
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
