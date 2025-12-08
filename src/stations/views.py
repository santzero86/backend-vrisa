from rest_framework import viewsets, permissions
from .models import MonitoringStation
from .serializers import MonitoringStationSerializer

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
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(operative_status=status)
        return queryset
