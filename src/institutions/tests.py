import json
import io
from PIL import Image
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from src.institutions.services import InstitutionService
from src.institutions.models import EnvironmentalInstitution
from src.users.models import User

class InstitutionTests(TestCase):
    def setUp(self):
        # Crear usuario para autenticación (si el endpoint lo requiere)
        self.user = User.objects.create_user(email='admin@test.com', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def generate_image_file(self):
        """Genera una imagen dummy en memoria para pruebas de upload"""
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile("logo.jpg", file.read(), content_type="image/jpeg")

    def test_create_institution_service(self):
        """Prueba unitaria del servicio (Lógica interna)"""
        data = {'institute_name': 'EcoLogic', 'physic_address': 'Av Siempre Viva'}
        colors = ['#FF0000', '#00FF00']
        inst = InstitutionService.create_institution(data, colors)
        self.assertTrue(EnvironmentalInstitution.objects.filter(institute_name='EcoLogic').exists())
        self.assertEqual(inst.colors.count(), 2)

    def test_api_register_institution(self):
        """
        Prueba de integración del Endpoint (Simula React + FormData).
        """
        url = reverse('register-institution') 
        
        # Simular FormData
        logo = self.generate_image_file()
        data = {
            'institute_name': 'API Institution',
            'physic_address': 'Calle API 123',
            'institute_logo': logo,
            'colors': json.dumps(['#FFFFFF', '#000000']) # React envía esto como string JSON
        }

        # Multipart/form-data request
        response = self.client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EnvironmentalInstitution.objects.filter(institute_name='API Institution').exists())
        
        # Verificar que el usuario actual es ahora el representante 
        self.user.refresh_from_db()
        # self.assertIsNotNone(self.user.institution)