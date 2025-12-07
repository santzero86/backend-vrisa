import os
import django

# Esto configura el entorno de Django para que el script funcione
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from src.institutions.models import EnvironmentalInstitution
from src.stations.models import MonitoringStation
from src.measurements.models import VariableCatalog
from src.sensors.models import Sensor
from src.users.models import User

def run():
    print("--- Iniciando carga de datos base ---")

    # 1. Crear Institución (DAGMA)
    inst, created = EnvironmentalInstitution.objects.get_or_create(
        institute_name="DAGMA - Cali",
        defaults={'physic_address': "Av. 5AN #20N-08, Cali"}
    )
    if created:
        print(f"✅ Institución creada: {inst.institute_name}")
    else:
        print(f"ℹ️ La institución {inst.institute_name} ya existía")

    # 2. Crear Estación Real (La Flora)
    station, created = MonitoringStation.objects.get_or_create(
        station_name="Estación La Flora",
        defaults={
            'geographic_location_lat': 3.476,
            'geographic_location_long': -76.526,
            'institution': inst,
            'operative_status': 'ACTIVE'
        }
    )
    if created:
        print(f"✅ Estación creada: {station.station_name}")

    # 3. Crear Variables (PM2.5, Temperatura, Humedad)
    var_pm25, _ = VariableCatalog.objects.get_or_create(
        code="PM2.5",
        defaults={'name': "Material Particulado 2.5", 'unit': "µg/m³", 'min_expected_value': 0, 'max_expected_value': 500}
    )
    var_temp, _ = VariableCatalog.objects.get_or_create(
        code="TEMP",
        defaults={'name': "Temperatura", 'unit': "°C", 'min_expected_value': -10, 'max_expected_value': 50}
    )
    var_hum, _ = VariableCatalog.objects.get_or_create(
        code="HUM",
        defaults={'name': "Humedad", 'unit': "%", 'min_expected_value': 0, 'max_expected_value': 100}
    )
    print("✅ Variables del catálogo aseguradas")

    # 4. Crear el Sensor Virtual para WAQI
    sensor, created = Sensor.objects.get_or_create(
        serial_number="WAQI-VIRTUAL-001",
        defaults={
            'model': 'API Gateway WAQI',
            'manufacturer': 'Virtual',
            'installation_date': '2024-01-01',
            'status': 'ACTIVE',
            'station': station
        }
    )
    if created:
        print(f"✅ Sensor Virtual creado: {sensor.serial_number}")
    else:
        print(f"ℹ️ El sensor {sensor.serial_number} ya existía")

    print("\n=============================================")
    print(f"📌 DATOS PARA TU SCRIPT DE INGESTA:")
    print(f"   SENSOR_ID: {sensor.sensor_id}")
    print(f"   ID PM2.5 : {var_pm25.variable_id}")
    print(f"   ID TEMP  : {var_temp.variable_id}")
    print(f"   ID HUM   : {var_hum.variable_id}")
    print("=============================================")

if __name__ == "__main__":
    run()