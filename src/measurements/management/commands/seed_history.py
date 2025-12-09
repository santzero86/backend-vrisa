import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from src.sensors.models import Sensor
from src.measurements.models import VariableCatalog, Measurement
from src.measurements.utils.cali_profile import HOURLY_PROFILE

class Command(BaseCommand):
    """
    Comando de gestión para poblar el historial de mediciones.
    
    Características:
    - Multivariable: Genera datos para PM2.5, PM10, CO, NO2, SO2, O3, TEMP, HUM.
    - Multi-sensor: Itera sobre todos los sensores activos en la base de datos.
    - Idempotente: Verifica si ya existen datos para no duplicar al reiniciar el contenedor.
    - Realista: Usa perfiles horarios de Cali y añade variabilidad aleatoria.
    """
    help = 'Genera datos históricos extendidos para todos los sensores y variables.'

    # TABLA DE CAPACIDADES (Mapping Modelo -> Variables)
    SENSOR_CAPABILITIES = {
        "VriSA-Meteo":      ["TEMP", "HUM"],          # Sensor 1
        "VriSA-Urban-Eco":  ["CO", "PM2.5"],          # Sensor 2
        "VriSA-Heavy-Ind":  ["PM10", "NO2", "SO2"],   # Sensor 3
        "VriSA-O3-Only":    ["O3"]                    # Sensor 4
    }

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Iniciando historial para 4 sensores ---")

        # 1. Configuración de tiempo
        days_back = 30
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)

        # 2. Verificar Idempotencia
        if Measurement.objects.filter(measure_date__gte=start_date).count() > 100:
            self.stdout.write(self.style.WARNING('Datos recientes detectados. Omitiendo generación.'))
            return

        # 3. Cargar Sensores
        sensors = Sensor.objects.filter(status=Sensor.Status.ACTIVE)
        if not sensors.exists():
            self.stdout.write(self.style.ERROR('No hay sensores. Ejecuta seed_db.'))
            return

        # 4. Cachear variables necesarias
        variables_map = {}
        all_needed_codes = set([code for sublist in self.SENSOR_CAPABILITIES.values() for code in sublist])
        
        for code in all_needed_codes:
            try:
                variables_map[code] = VariableCatalog.objects.get(code=code)
            except VariableCatalog.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Variable {code} no existe en DB.'))

        # 5. Generación
        current_date = start_date
        total = 0
        batch = []

        while current_date <= end_date:
            hour_str = str(current_date.hour)
            base_data = HOURLY_PROFILE.get(hour_str, HOURLY_PROFILE.get("0"))

            for sensor in sensors:
                # Obtenemos QUÉ debe medir este sensor según su modelo
                allowed_vars = self.SENSOR_CAPABILITIES.get(sensor.model, [])

                for code in allowed_vars:
                    if code not in variables_map: continue
                    
                    # Valor base del perfil
                    base_val = base_data.get(code, 0)
                    
                    # Variabilidad aleatoria
                    noise = base_val * random.uniform(0.05, 0.15)
                    final_val = max(0, base_val + random.choice([noise, -noise]))
                    if code == "HUM": final_val = min(100, final_val)

                    batch.append(Measurement(
                        sensor=sensor,
                        variable=variables_map[code],
                        value=round(final_val, 2),
                        measure_date=current_date
                    ))
                    total += 1

            if len(batch) >= 2000:
                Measurement.objects.bulk_create(batch)
                batch = []
                self.stdout.write(f"... {total} registros")

            current_date += timedelta(hours=1)

        if batch: Measurement.objects.bulk_create(batch)
        self.stdout.write(self.style.SUCCESS(f'Historial completado: {total} registros.'))