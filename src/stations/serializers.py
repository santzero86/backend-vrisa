from rest_framework import serializers
from src.institutions.models import EnvironmentalInstitution
from src.stations.models import MonitoringStation
from src.users.serializers import UserSerializer


class MonitoringStationSerializer(serializers.ModelSerializer):
    """
    Serializador de SALIDA completo para la estación.
    """
    
    # Incluimos detalles del manager para no mostrar solo el ID
    manager_user = UserSerializer(read_only=True)
    institution_name = serializers.CharField(
        source="institution.institute_name", read_only=True
    )

    class Meta:
        model = MonitoringStation
        fields = [
            "station_id",
            "station_name",
            "operative_status",
            "geographic_location_lat",
            "geographic_location_long",
            "created_at",
            "updated_at",
            "manager_user",
            "institution_id",
            "institution_name",
        ]


class CreateStationSerializer(serializers.Serializer):
    """
    Serializador de ENTRADA para crear estaciones.
    """

    station_name = serializers.CharField(max_length=150)
    geographic_location_lat = serializers.FloatField()
    geographic_location_long = serializers.FloatField()
    institution_id = serializers.IntegerField()
    manager_user_id = serializers.IntegerField(required=False)

    def validate_geographic_location_lat(self, value):
        if value < -90 or value > 90:
            raise serializers.ValidationError(
                "La latitud debe estar entre -90 y 90 grados."
            )
        return value

    def validate_geographic_location_long(self, value):
        if value < -180 or value > 180:
            raise serializers.ValidationError(
                "La longitud debe estar entre -180 y 180 grados."
            )
        return value

    def validate_institution_id(self, value):
        if not EnvironmentalInstitution.objects.filter(pk=value).exists():
            raise serializers.ValidationError("La institución no existe.")
        return value
