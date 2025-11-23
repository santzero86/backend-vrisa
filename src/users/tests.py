from django.test import TestCase
from django.core.exceptions import ValidationError
from src.users.services import create_user
from src.users.models import User
from src.institutions.models import EnvironmentalInstitution

class UserServiceTestCase(TestCase):
    def setUp(self):
        # Crear datos previos necesarios
        self.institution = EnvironmentalInstitution.objects.create(
            institute_name="Vrisa Corp",
            physic_address="Calle 123"
        )

    def test_create_user_service_success(self):
        """
        Prueba que el servicio crea un usuario y lo vincula a la institución
        correctamente, además de aplicar las reglas de negocio.
        """
        data = {
            'email': 'test@vrisa.com',
            'password': 'password123',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'institution_id': self.institution.id,
            'job_title': 'Analista'
        }
        
        user = create_user(data)
        
        self.assertEqual(user.email, 'test@vrisa.com')
        self.assertEqual(user.institution, self.institution)
        self.assertFalse(user.is_active) # Regla de negocio: nace inactivo
        self.assertTrue(user.check_password('password123'))

    def test_create_user_invalid_institution(self):
        """
        Prueba que falla si la institución no existe (manejado por get_object_or_404)
        """
        data = {
            'email': 'fail@vrisa.com',
            'password': '123',
            'first_name': 'Fail',
            'last_name': 'User',
            'institution_id': 9999 # ID inexistente
        }
        
        # get_object_or_404 lanza Http404, en tests puros a veces queremos capturar eso
        # o asegurarnos que el servicio lo maneje.
        from django.http import Http404
        with self.assertRaises(Http404):
            create_user(data)