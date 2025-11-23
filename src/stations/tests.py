from django.test import TestCase
from src.stations.services import create_station
from src.institutions.models import EnvironmentalInstitution
from src.users.models import User

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
            # No enviamos token
        }
        
        station = create_station(data, self.user.id)
        
        self.assertIsNotNone(station.authentication_token)
        self.assertEqual(len(station.authentication_token), 64) # 32 bytes hex
        self.assertEqual(station.manager_user, self.user)