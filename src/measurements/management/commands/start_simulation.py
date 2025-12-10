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
        self.stdout.write(self.style.WARNING('--- Simulador VriSA (Con Alertas) Iniciado ---'))
        
        # Esperar DB
        while True:
            try:
                if Sensor.objects.exists(): break
            except OperationalError:
                time.sleep(2)
        
        variables_cache = {v.code: v for v in VariableCatalog.objects.all()}

        # Probabilidad de alerta en cada ciclo de envío (10%)
        ALERT_CHANCE = 0.1

        while True:
            try:
                now = timezone.now()
                hour_str = str(now.hour)
                base_data = HOURLY_PROFILE.get(hour_str, HOURLY_PROFILE.get("0"))
                
                sensors = Sensor.objects.filter(status=Sensor.Status.ACTIVE)
                
                # "Episodio Crítico"
                is_critical_moment = random.random() < ALERT_CHANCE

                for sensor in sensors:
                    capabilities = self.SENSOR_CAPABILITIES.get(sensor.model, [])
                    log_readings = []
                    
                    for code in capabilities:
                        if code not in variables_cache: continue
                        var_obj = variables_cache[code]
                        base_val = base_data.get(code, 0)
                        
                        # Variación normal
                        variation = base_val * random.uniform(0.05, 0.15)
                        sim_val = max(0, base_val + random.choice([variation, -variation]))

                        # --- INYECCIÓN DE ALERTA ---
                        # Si estamos en momento crítico, y NO es temperatura/humedad (para dramatismo en contaminantes)
                        if is_critical_moment and code not in ['TEMP', 'HUM']:
                            # Generar valor de alerta
                            spike = random.uniform(1.2, 3.0) # Hasta 3 veces lo normal
                            sim_val = sim_val * spike
                            
                            # Asegurar que cruce el umbral para que se note en el frontend
                            if sim_val < var_obj.max_expected_value:
                                sim_val = var_obj.max_expected_value + 5.0
                        
                        if code == 'HUM': sim_val = min(100, sim_val)

                        # Guardar usando el servicio (que ya modificamos en el Paso 1 para aceptar esto)
                        self.save_measurement(sensor, var_obj, sim_val, now)
                        
                        # Visualización en consola
                        val_str = f"{sim_val:.2f}"
                        if is_critical_moment and code not in ['TEMP', 'HUM']:
                            val_str += " [ALERTA!]" # Marca visual en el log del contenedor
                        
                        log_readings.append(f"{code}={val_str}")
                
                    if log_readings:
                        timestamp = now.strftime('%H:%M:%S')
                        color_style = self.style.ERROR if is_critical_moment else self.style.SUCCESS
                        self.stdout.write(color_style(
                            f"[{timestamp}] {sensor.serial_number}: {' | '.join(log_readings)}"
                        ))
                
                time.sleep(10) 

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error en simulador: {e}'))
                time.sleep(5)

    def save_measurement(self, sensor, variable, value, date):
        try:
            MeasurementService.create_measurement({
                'sensor': sensor,
                'variable': variable,
                'value': round(value, 2),
                'measure_date': date
            })
        except Exception as e:
            print(f"Error guardando: {e}")