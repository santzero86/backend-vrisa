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
    help = 'Simula datos basados en perfiles horarios reales de Cali'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Esperando a que las migraciones terminen...'))
        db_ready = False
        while not db_ready:
            try:
                # Intentamos hacer una consulta ligera para ver si la tabla existe
                Sensor.objects.exists()
                db_ready = True
            except (OperationalError, ProgrammingError):
                # Si falla porque la tabla no existe o la DB se está reiniciando
                self.stdout.write('La base de datos aún no tiene las tablas. Reintentando en 2s...')
                time.sleep(2)
        
        self.stdout.write(self.style.SUCCESS('Base de datos lista'))
        self.stdout.write(self.style.SUCCESS('Iniciando simulación realista (Perfil Cali)...'))

        while True:
            try:
                now = timezone.now()
                current_hour = str(now.hour) 
                base_data = HOURLY_PROFILE.get(current_hour, HOURLY_PROFILE.get("0"))
                
                if not base_data:
                     self.stdout.write(self.style.ERROR('Error leyendo el perfil horario. Revisa cali_profile.py'))
                     time.sleep(5)
                     continue
                 
                # Recuperar variables del catálogo
                try:
                    var_pm25 = VariableCatalog.objects.get(code="PM2.5")
                    var_temp = VariableCatalog.objects.get(code="TEMP")
                    var_hum = VariableCatalog.objects.get(code="HUM")
                except VariableCatalog.DoesNotExist:
                    self.stdout.write(self.style.ERROR('Faltan variables. Ejecuta seed_db.'))
                    break
                
                sensors = Sensor.objects.filter(status=Sensor.Status.ACTIVE)
                if not sensors.exists():
                    self.stdout.write(self.style.WARNING('Esperando sensores activos...'))
                    time.sleep(5)
                    continue

                for sensor in sensors:
                    # 2. Algoritmo de Variación Natural
                    # Tomamos el valor base de la hora y le agregamos "ruido" aleatorio
                    # para que no sea una línea plana perfecta durante la hora.
                    
                    # PM2.5: Base +/- 3 puntos
                    val_pm25 = base_data['PM2.5'] + random.uniform(-3.0, 3.0)
                    val_pm25 = max(0, val_pm25) # No negativos

                    # Temp: Base +/- 0.5 grados
                    val_temp = base_data['TEMP'] + random.uniform(-0.5, 0.5)

                    # Humedad: Base +/- 2%
                    val_hum = base_data['HUM'] + random.uniform(-2.0, 2.0)
                    val_hum = max(0, min(100, val_hum))

                    # 3. Persistencia
                    self.save_measurement(sensor, var_pm25, val_pm25)
                    self.save_measurement(sensor, var_temp, val_temp)
                    self.save_measurement(sensor, var_hum, val_hum)

                    self.stdout.write(
                        f"[{now.strftime('%H:%M:%S')}] {sensor.serial_number} (Hora {current_hour}): "
                        f"PM2.5={val_pm25:.1f} | TEMP={val_temp:.1f}°C | HUM={val_hum:.1f}%"
                    )

                # Frecuencia de actualización (ej: cada 10 segundos)
                time.sleep(10)

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {e}'))
                time.sleep(5)

    def save_measurement(self, sensor, variable, value):
        MeasurementService.create_measurement({
            'sensor': sensor,
            'variable': variable,
            'value': round(value, 2),
            'measure_date': timezone.now()
        })
