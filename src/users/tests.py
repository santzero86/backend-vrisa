from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from src.users.services import create_user
from src.users.models import User, Role
from src.institutions.models import EnvironmentalInstitution

class UserServiceTestCase(TestCase):
    def setUp(self):
        # Crear datos previos necesarios
        self.institution = EnvironmentalInstitution.objects.create(
            institute_name="Vrisa Corp",
            physic_address="Calle 123"
        )
        # Asegurar que existen los roles básicos para el registro
        Role.objects.get_or_create(role_name='citizen')
        Role.objects.get_or_create(role_name='station_admin')

    def test_create_user_service_success(self):
        """
        Prueba que el servicio crea un usuario correctamente.
        CORRECCIÓN: Se ajusta is_active a True según la lógica del servicio.
        """
        data = {
            'email': 'test@vrisa.com',
            'password': 'password123',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'institution_id': self.institution.id,
            'job_title': 'Analista',
            'phone': '1234567890'
        }
        
        user = create_user(data)
        
        self.assertEqual(user.email, 'test@vrisa.com')
        self.assertEqual(user.institution, self.institution)
        self.assertTrue(user.is_active) 
        self.assertTrue(user.check_password('password123'))

    def test_api_register_user(self):
        """
        NUEVO: Prueba el endpoint de registro (Integration Test).
        Simula una petición desde React.
        """
        client = APIClient()
        url = reverse('user-register') 
        data = {
            'email': 'api_user@vrisa.com',
            'password': 'securepass123',
            'first_name': 'API',
            'last_name': 'User',
            'phone': '3001234567',
            'belongsToOrganization': False # Simula el frontend
        }
        
        response = client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='api_user@vrisa.com').exists())