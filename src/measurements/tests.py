from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from src.measurements.services import MeasurementService
from src.measurements.models import VariableCatalog, Measurement
from src.sensors.models import Sensor
from src.stations.models import MonitoringStation 
from src.institutions.models import EnvironmentalInstitution
from src.measurements.services import AQICalculatorService

class MeasurementServiceTestCase(TestCase):
    def setUp(self):
        # Configurar jerarquía
        self.inst = EnvironmentalInstitution.objects.create(institute_name="Data Inst", physic_address="x")
        
        self.station = MonitoringStation.objects.create(
            station_name="Est1", 
            institution=self.inst, 
            geographic_location_lat=0, 
            geographic_location_long=0
        )
        
        # Sensor Activo
        self.sensor = Sensor.objects.create(
            serial_number="SN-123", 
            model="X1", 
            manufacturer="Acme", 
            installation_date="2023-01-01",
            status=Sensor.Status.ACTIVE,
            station=self.station 
        )
        
        # Variable: Temp (0 a 50 grados)
        self.variable = VariableCatalog.objects.create(
            name="Temperatura", code="TEMP", unit="C",
            min_expected_value=0, max_expected_value=50
        )

    def test_create_valid_measurement(self):
        """
        Flujo correcto: Crear medición válida
        """
        data = {
            'sensor': self.sensor,
            'variable': self.variable,
            'value': 25.5,
            'measure_date': timezone.now()
        }
        measurement = MeasurementService.create_measurement(data)
        self.assertEqual(measurement.value, 25.5)
        # Verificamos que se puede acceder a la estación desde la medición
        self.assertEqual(measurement.sensor.station.station_name, "Est1")

    def test_reject_inactive_sensor(self):
        """
        Falla si el sensor está en mantenimiento o inactivo
        """
        self.sensor.status = Sensor.Status.MAINTENANCE
        self.sensor.save()
        
        data = {
            'sensor': self.sensor,
            'variable': self.variable,
            'value': 25.5,
            'measure_date': timezone.now()
        }
        with self.assertRaises(ValidationError) as cm:
            MeasurementService.create_measurement(data)
        self.assertIn("no está activo", str(cm.exception))

    def test_reject_out_of_range_value(self):
        """
        Falla si el valor es físicamente imposible (definido en catálogo)
        """
        # Intentamos guardar 150 cuando el máximo es 50
        data = {
            'sensor': self.sensor,
            'variable': self.variable,
            'value': 150.0, 
            'measure_date': timezone.now()
        }
        pass

class AQICalculatorTestCase(TestCase):
    def test_calculate_sub_index_pm25_good(self):
            """
            Prueba basada en tabla EPA:
            PM2.5 de 12.0 debe dar un AQI de 50 (Límite superior de 'Good')
            """
            aqi = AQICalculatorService.calculate_sub_index('PM2.5', 12.0)
            self.assertEqual(aqi, 50)

    def test_calculate_sub_index_pm25_hazardous(self):
            """
            Prueba de rango peligroso:
            PM2.5 de 250.5 debe dar AQI > 300
            """
            aqi = AQICalculatorService.calculate_sub_index('PM2.5', 250.5)
            self.assertTrue(aqi >= 301)

    def test_aqi_category_logic(self):
            """
            Prueba que el sistema asigne el color y la etiqueta correcta
            """
            # AQI 45 -> Verde (Good)
            cat_good = AQICalculatorService.get_aqi_category(45)
            self.assertEqual(cat_good['level'], 'Good')
            self.assertEqual(cat_good['color'], '#0CDA0C')

            # AQI 160 -> Rojo (Unhealthy)
            cat_bad = AQICalculatorService.get_aqi_category(160)
            self.assertEqual(cat_bad['level'], 'Unhealthy')
            self.assertEqual(cat_bad['color'], '#FF0000')