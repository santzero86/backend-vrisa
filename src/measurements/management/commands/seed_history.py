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
        self.stdout.write("--- Iniciando historial CON ANOMALÍAS ---")

        days_back = 30
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)

        if Measurement.objects.filter(measure_date__gte=start_date).count() > 100:
            self.stdout.write(self.style.WARNING('Datos detectados. Limpia la DB si quieres regenerar.'))
            return

        sensors = Sensor.objects.filter(status=Sensor.Status.ACTIVE)
        variables_map = {v.code: v for v in VariableCatalog.objects.all()}

        current_date = start_date
        batch = []
        total = 0

        # Probabilidad de que un día sea "malo" (Evento de contaminación)
        EVENT_PROBABILITY = 0.05 

        while current_date <= end_date:
            hour_str = str(current_date.hour)
            base_data = HOURLY_PROFILE.get(hour_str, HOURLY_PROFILE.get("0"))

            # Determinar si en esta hora específica ocurre una anomalía (Pico de contaminación)
            is_anomaly_hour = random.random() < EVENT_PROBABILITY

            for sensor in sensors:
                allowed_vars = self.SENSOR_CAPABILITIES.get(sensor.model, [])

                for code in allowed_vars:
                    if code not in variables_map: continue
                    
                    base_val = base_data.get(code, 0)
                    var_obj = variables_map[code]

                    # Lógica de Ruido Normal
                    noise = base_val * random.uniform(0.05, 0.15)
                    final_val = max(0, base_val + random.choice([noise, -noise]))

                    # --- LÓGICA DE ALERTA (DATOS ATÍPICOS) ---
                    # Si es hora de anomalía y NO es Humedad (la humedad no suele tener picos de "alerta" peligrosa igual que gases)
                    if is_anomaly_hour and code != 'HUM':
                        # Multiplicador agresivo para superar el límite
                        spike_factor = random.uniform(1.5, 4.0) 
                        
                        # Forzamos que supere el límite máximo configurado
                        limit = var_obj.max_expected_value
                        potential_alert_val = final_val * spike_factor
                        
                        # Aseguramos que sea una alerta real (un poco por encima del límite)
                        if potential_alert_val < limit:
                            potential_alert_val = limit + random.uniform(1, 20)
                        
                        final_val = potential_alert_val

                    # Corrección física para Humedad
                    if code == "HUM": final_val = min(100, final_val)

                    batch.append(Measurement(
                        sensor=sensor,
                        variable=var_obj,
                        value=round(final_val, 2),
                        measure_date=current_date
                    ))
                    total += 1

            if len(batch) >= 5000:
                Measurement.objects.bulk_create(batch)
                batch = []
                self.stdout.write(f"... {total} registros (Fecha: {current_date.date()})")

            current_date += timedelta(hours=1)

        if batch: Measurement.objects.bulk_create(batch)
        self.stdout.write(self.style.SUCCESS(f'Historial completado con alertas: {total} registros.'))