from django.test import TestCase
from django.core.exceptions import ValidationError
from src.sensors.services import SensorService
from src.sensors.models import Sensor
from src.stations.models import MonitoringStation
from src.institutions.models import EnvironmentalInstitution
from django.utils import timezone

class SensorServiceTestCase(TestCase):
    def setUp(self):
        """
        Configuración inicial: Creamos la jerarquía necesaria (Institución -> Estación)
        para poder asignarle un sensor a una estación.
        """
        self.institution = EnvironmentalInstitution.objects.create(
            institute_name="Tech Vrisa",
            physic_address="Calle 100"
        )
        self.station = MonitoringStation.objects.create(
            station_name="Estación Central",
            geographic_location_lat=4.6,
            geographic_location_long=-74.0,
            institution=self.institution
        )

    def test_create_sensor_success(self):
        """
        Prueba que el servicio crea un sensor correctamente y lo vincula a la estación.
        """
        data = {
            'model': 'AirSense Pro',
            'manufacturer': 'VrisaLabs',
            'serial_number': 'SN-001',
            'installation_date': timezone.now().date(),
            'status': Sensor.Status.ACTIVE,
            'station': self.station  # Aquí probamos la relación crítica
        }

        sensor = SensorService.create_sensor(data)

        # Verificaciones
        self.assertEqual(sensor.serial_number, 'SN-001')
        self.assertEqual(sensor.station, self.station)
        self.assertEqual(sensor.status, Sensor.Status.ACTIVE)
        # Verificar que se guardó en la DB
        self.assertTrue(Sensor.objects.filter(serial_number='SN-001').exists())

    def test_update_sensor_status_success(self):
        """
        Prueba que se puede actualizar el estado operativo de un sensor.
        """
        # 1. Crear sensor inicial
        sensor = Sensor.objects.create(
            model='Basic',
            manufacturer='Test',
            serial_number='SN-UPDATE',
            installation_date=timezone.now().date(),
            status=Sensor.Status.ACTIVE,
            station=self.station
        )

        # 2. Llamar al servicio para cambiar estado a MANTENIMIENTO
        updated_sensor = SensorService.update_sensor_status(sensor.sensor_id, Sensor.Status.MAINTENANCE)

        # 3. Verificar cambio en memoria y en DB
        self.assertEqual(updated_sensor.status, Sensor.Status.MAINTENANCE)
        sensor.refresh_from_db() # Recargar desde la base de datos
        self.assertEqual(sensor.status, Sensor.Status.MAINTENANCE)

    def test_update_sensor_not_found(self):
        """
        Prueba que el servicio lanza ValidationError si el ID del sensor no existe.
        """
        non_existent_id = 99999
        
        with self.assertRaises(ValidationError) as context:
            SensorService.update_sensor_status(non_existent_id, Sensor.Status.INACTIVE)
        
        self.assertIn(f"El sensor {non_existent_id} no existe", str(context.exception))