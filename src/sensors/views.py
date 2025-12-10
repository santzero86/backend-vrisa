from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from .models import MaintenanceLog, Sensor
from .serializers import MaintenanceLogSerializer, SensorSerializer
from .services import SensorService


class SensorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operaciones CRUD sobre los sensores.
    Delega la creación al SensorService para mantener la consistencia
    y permitir futuras expansiones de lógica de negocio.
    """

    serializer_class = SensorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Sobrescribe la consulta base para filtrar datos según el usuario.
        """
        user = self.request.user
        queryset = Sensor.objects.all()

        # Super Admin: Ve todos los sensores
        if user.is_superuser:
            return queryset

        # Administrador de Estación (station_admin):
        # Filtra los sensores que pertenecen a estaciones donde el usuario es el 'manager_user'.
        if hasattr(user, "managed_stations") and user.managed_stations.exists():
            return queryset.filter(station__manager_user=user)

        # Jefe de Institución (institution_head): Ve sensores de todas las estaciones de su institución.
        if user.institution:
            return queryset.filter(station__institution=user.institution)

        return queryset.none()

    def create(self, request, *args, **kwargs):
        """
        Intercepta la creación para utilizar el SensorService.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Llamada al servicio
            sensor = SensorService.create_sensor(serializer.validated_data)
            output_serializer = self.get_serializer(sensor)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MaintenanceLogViewSet(viewsets.ModelViewSet):
    """
    Endpoint: /api/sensors/maintenance/
    Gestión de la bitácora de mantenimiento.
    """

    serializer_class = MaintenanceLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra los registros de mantenimiento para mostrar solo los relacionados
        con las estaciones que el usuario administra.
        """
        user = self.request.user
        queryset = MaintenanceLog.objects.all()

        # Super Admin: Ve todo el historial
        if user.is_superuser:
            return queryset

        # Administrador de Estación (station_admin)
        if hasattr(user, "managed_stations") and user.managed_stations.exists():
            return queryset.filter(sensor__station__manager_user=user)

        # Jefe de Institución (institution_head)
        # Ve los mantenimientos de todos los sensores de su institución
        if user.institution:
            return queryset.filter(sensor__station__institution=user.institution)

        return queryset.none()

    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario que crea el registro como técnico,
        a menos que se especifique otro.
        """
        serializer.save(technical_user=self.request.user)
