import random
import math
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from src.sensors.models import Sensor
from src.measurements.models import VariableCatalog, Measurement
from src.measurements.services import AQICalculatorService
from src.measurements.utils.cali_profile import HOURLY_PROFILE


class Command(BaseCommand):
    help = "Puebla la DB con historial híbrido (Contaminantes CSV + Clima Matemático) desde 1 Nov."

    # Fechas de eventos anómalos a drede (Mes, Día)
    ANOMALY_DATES = [
        (11, 7),  # Día del evento de prueba
        (12, 1),
        (12, 7),
        (12, 24),
        (12, 31),
    ]

    SENSOR_CAPABILITIES = {
        "VriSA-Meteo": ["TEMP", "HUM"],
        "VriSA-Urban-Eco": ["CO", "PM2.5"],
        "VriSA-Heavy-Ind": ["PM10", "NO2", "SO2"],
        "VriSA-O3-Only": ["O3"],
    }

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Generando Historial Híbrido ---")

        # Limpieza
        Measurement.objects.all().delete()

        now = timezone.now()
        start_date = now.replace(month=11, day=1, hour=0, minute=0, second=0)
        if now.month < 11:
            start_date = start_date.replace(year=now.year - 1)
        end_date = now

        sensors = Sensor.objects.filter(status=Sensor.Status.ACTIVE)
        variables_map = {v.code: v for v in VariableCatalog.objects.all()}
        aqi_variable, _ = VariableCatalog.objects.get_or_create(
            code="AQI",
            defaults={"name": "AQI", "unit": "AQI", "max_expected_value": 500},
        )

        current_date = start_date
        batch = []

        total_records = 0
        total_anomalies = 0

        while current_date <= end_date:
            month = current_date.month
            day = current_date.day
            hour = current_date.hour

            # Datos base del CSV
            base_data = HOURLY_PROFILE.get(str(hour), {})

            # Flags de Alerta
            is_anomaly_day = (month, day) in self.ANOMALY_DATES
            is_strong_event = is_anomaly_day and (month == 11 and day == 7)

            current_hour_values = {}

            for sensor in sensors:
                capabilities = self.SENSOR_CAPABILITIES.get(sensor.model, [])

                for code in capabilities:
                    if code not in variables_map:
                        continue
                    var_obj = variables_map[code]
                    final_val = 0
                    is_this_measurement_anomaly = False

                    if code == "TEMP":
                        diurnal = math.cos((hour - 14) * 2 * math.pi / 24)
                        final_val = 26 + (5 * diurnal) + random.uniform(-0.5, 0.5)

                    elif code == "HUM":
                        diurnal = math.cos((hour - 4) * 2 * math.pi / 24)
                        final_val = 70 + (15 * diurnal) + random.uniform(-2, 2)
                        final_val = min(100, max(0, final_val))

                    else:
                        val_csv = base_data.get(code, 10.0)
                        final_val = val_csv * random.uniform(0.95, 1.05)

                    # --- Inyección de alertas ---
                    if is_anomaly_day and code not in ["TEMP", "HUM"]:
                        limit = var_obj.max_expected_value

                        if is_strong_event:
                            # Alerta garantizada entre 8am y 10pm
                            if 8 <= hour <= 22 and limit > 0:
                                target = limit * 1.2
                                final_val = max(final_val * 2, target)
                                is_this_measurement_anomaly = (
                                    True  # Marcamos como anomalía
                                )
                        else:
                            final_val = final_val * 1.3
                            is_this_measurement_anomaly = True  # Marcamos como anomalía

                    # Contadores
                    if is_this_measurement_anomaly:
                        total_anomalies += 1

                    current_hour_values[code] = final_val

                    batch.append(
                        Measurement(
                            sensor=sensor,
                            variable=var_obj,
                            value=round(final_val, 2),
                            measure_date=current_date,
                        )
                    )
                    total_records += 1

            # --- calulo de puntaje AQI ---
            try:
                aqi_vals = []
                for c, v in current_hour_values.items():
                    try:
                        aqi_vals.append(AQICalculatorService.calculate_sub_index(c, v))
                    except:
                        pass

                if aqi_vals:
                    final_aqi = max(aqi_vals)
                    is_aqi_anomaly = False

                    # Forzar AQI visual el 7 Nov si no subió naturalmente
                    if is_strong_event and 8 <= hour <= 22 and final_aqi < 110:
                        final_aqi = random.uniform(115, 150)
                        is_aqi_anomaly = True

                    # Si los contaminantes individuales fueron anomalía, el AQI resultante también cuenta como registro anómalo
                    if is_anomaly_day and (is_strong_event or is_aqi_anomaly):
                        total_anomalies += 1

                    batch.append(
                        Measurement(
                            sensor=sensors.first(),
                            variable=aqi_variable,
                            value=round(final_aqi, 2),
                            measure_date=current_date,
                        )
                    )
                    total_records += 1
            except:
                pass

            # Guardar en lotes
            if len(batch) >= 5000:
                Measurement.objects.bulk_create(batch)
                batch = []
                self.stdout.write(
                    f"... procesado hasta {current_date.date()} {hour}:00"
                )

            current_date += timedelta(hours=1)

        # Guardar remanentes
        if batch:
            Measurement.objects.bulk_create(batch)

        self.stdout.write(
            self.style.SUCCESS(f"---------------------------------------------")
        )
        self.stdout.write(self.style.SUCCESS(f"Historial Regenerado Correctamente."))
        self.stdout.write(
            self.style.SUCCESS(f"Total Registros Agregados: {total_records}")
        )
        self.stdout.write(
            self.style.WARNING(f"Registros Atípicos (Alertas): {total_anomalies}")
        )
