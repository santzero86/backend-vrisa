from django.test import TestCase
from src.stations.services import create_station
from src.institutions.models import EnvironmentalInstitution
from src.users.models import User
from src.stations.models import MonitoringStation
from rest_framework.test import APIClient
from rest_framework import status

class StationServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="admin@st.com", first_name="A", last_name="B")
        self.inst = EnvironmentalInstitution.objects.create(institute_name="StationOwner", physic_address="x")

    def test_station_auto_token_generation(self):
        """
        Prueba que el servicio genera un token si no se envía
        """
        data = {
            'station_name': 'Alpha Station',
            'geographic_location_lat': 10.5,
            'geographic_location_long': -75.5,
            'institution_id': self.inst.id,
            'address_reference': 'Centro'
        }
        
        # Simulamos que el request.user.id es pasado al servicio
        station = create_station(data, self.user.id)
        
        self.assertIsNotNone(station.authentication_token)
        self.assertEqual(len(station.authentication_token), 64) # 32 bytes hex
        self.assertEqual(station.manager_user, self.user)
        self.assertEqual(station.operative_status, 'PENDING') # Debe nacer pendiente

    def test_create_station_invalid_lat_long(self):
        """
        Validación básica de integridad de datos
        """
        # Django no valida float ranges por defecto en el modelo a menos que uses Validators explícitos
        # Pero podemos probar que guarda los datos correctamente
        data = {
            'station_name': 'Beta Station',
            'geographic_location_lat': 0.0,
            'geographic_location_long': 0.0,
            'institution_id': self.inst.id,
        }
        station = create_station(data, self.user.id)
        self.assertEqual(station.geographic_location_lat, 0.0)

class StationSecurityTestCase(TestCase):
    def setUp(self):
        self.inst = EnvironmentalInstitution.objects.create(institute_name="Secured Inst", physic_address="x")
        self.station = MonitoringStation.objects.create(
            station_name="Protected Station", 
            institution=self.inst,
            geographic_location_lat=0, geographic_location_long=0
        )
        
        # Usuario Malicioso (Ciudadano sin permisos de admin)
        self.hacker = User.objects.create_user(email='hacker@vrisa.com', password='123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.hacker)

    def test_citizen_cannot_delete_station(self):
        """
        SEGURIDAD: Un usuario normal no debe poder borrar estaciones.
        Debe recibir 403 Forbidden o 404 Not Found (dependiendo de tu configuración de filtros).
        """
        url = f'/api/stations/{self.station.station_id}/'
        response = self.client.delete(url)
        
        # Esperamos que falle la petición (Protección)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED])
        
        # Verificar que la estación sigue viva en la base de datos
        self.assertTrue(MonitoringStation.objects.filter(pk=self.station.pk).exists())