from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from src.measurements.services import MeasurementService
from src.measurements.models import VariableCatalog
from src.sensors.models import Sensor
from src.stations.models import MonitoringStation 
from src.institutions.models import EnvironmentalInstitution

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
            # station=self.station # Descomentar cuando arregles el modelo Sensor
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
        data = {
            'sensor': self.sensor,
            'variable': self.variable,
            'value': 150.0, # Max es 50
            'measure_date': timezone.now()
        }
        with self.assertRaises(ValidationError) as cm:
            MeasurementService.create_measurement(data)
        self.assertIn("fuera del rango permitido", str(cm.exception))
