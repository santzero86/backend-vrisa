import time
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.utils import OperationalError, ProgrammingError
from src.sensors.models import Sensor
from src.measurements.models import VariableCatalog
from src.measurements.services import MeasurementService
from src.measurements.utils.cali_profile import HOURLY_PROFILE

class Command(BaseCommand):
    """
    Simulador de IoT en Tiempo Real.
    
    Funcionalidad:
    1. Se ejecuta infinitamente (como un servicio o worker).
    2. Lee el perfil de contaminantes de Cali según la hora actual.
    3. Detecta dinámicamente TODOS los sensores activos en la base de datos.
    4. Genera mediciones para TODAS las variables (PM2.5, PM10, CO, etc.).
    5. Utiliza el 'MeasurementService' para validar reglas de negocio al guardar.
    """
    help = 'Simula datos multiparamétricos en tiempo real para todos los sensores activos'

    SENSOR_CAPABILITIES = {
        "VriSA-Meteo":      ["TEMP", "HUM"],          # Sensor 1
        "VriSA-Urban-Eco":  ["CO", "PM2.5"],          # Sensor 2
        "VriSA-Heavy-Ind":  ["PM10", "NO2", "SO2"],   # Sensor 3
        "VriSA-O3-Only":    ["O3"]                    # Sensor 4
    }

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('--- Simulador de 4 Sensores Iniciado ---'))
        
        # 1. Espera DB
        while True:
            try:
                if Sensor.objects.exists(): break
            except OperationalError:
                time.sleep(1)
        
        # 2. Cargar Variables
        variables_cache = {}
        all_needed_codes = set([code for sublist in self.SENSOR_CAPABILITIES.values() for code in sublist])
        
        for code in all_needed_codes:
            try:
                variables_cache[code] = VariableCatalog.objects.get(code=code)
            except VariableCatalog.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Falta variable: {code}'))

        self.stdout.write(self.style.SUCCESS('Configuración cargada. Enviando datos...'))

        # 3. Bucle Principal
        while True:
            try:
                now = timezone.now()
                hour_str = str(now.hour)
                base_data = HOURLY_PROFILE.get(hour_str, HOURLY_PROFILE.get("0"))
                
                sensors = Sensor.objects.filter(status=Sensor.Status.ACTIVE)
                
                for sensor in sensors:
                    # Lógica de Contexto: ¿Qué mide este sensor?
                    capabilities = self.SENSOR_CAPABILITIES.get(sensor.model, [])
                    
                    for code in capabilities:
                        if code not in variables_cache: continue
                        
                        var_obj = variables_cache[code]
                        base_val = base_data.get(code, 0)
                        
                        # Simulación
                        variation = base_val * random.uniform(0.05, 0.15)
                        sim_val = max(0, base_val + random.choice([variation, -variation]))
                        if code == 'HUM': sim_val = min(100, sim_val)

                        # Guardar
                        self.save_measurement(sensor, var_obj, sim_val, now)
                    
                time.sleep(10) # Intervalo de envío

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {e}'))
                time.sleep(5)

    def save_measurement(self, sensor, variable, value, date):
        try:
            MeasurementService.create_measurement({
                'sensor': sensor,
                'variable': variable,
                'value': round(value, 2),
                'measure_date': date
            })
        except Exception:
            pass
    