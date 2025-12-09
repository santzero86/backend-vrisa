from django.test import TestCase
from django.core.exceptions import ValidationError
from src.institutions.services import InstitutionService
from src.institutions.models import EnvironmentalInstitution

class InstitutionServiceTestCase(TestCase):
    def test_create_institution_with_colors(self):
        """
        Prueba crear institución y sus colores en una sola transacción
        """
        data = {
            'institute_name': 'EcoLogic',
            'physic_address': 'Av Siempre Viva'
        }
        colors = ['#FF0000', '#00FF00']
        
        inst = InstitutionService.create_institution(data, colors)
        
        self.assertTrue(EnvironmentalInstitution.objects.filter(institute_name='EcoLogic').exists())
        self.assertEqual(inst.colors.count(), 2)

    def test_create_institution_excessive_colors(self):
        """
        Prueba la regla de negocio: Máximo 5 colores
        """
        data = {'institute_name': 'Rainbow', 'physic_address': 'Sky'}
        colors = ['#1', '#2', '#3', '#4', '#5', '#6'] # 6 colores
        
        with self.assertRaises(ValidationError):
            InstitutionService.create_institution(data, colors)
            
        # Verificar atomicidad: No se debió crear la institución
        self.assertFalse(EnvironmentalInstitution.objects.filter(institute_name='Rainbow').exists())
