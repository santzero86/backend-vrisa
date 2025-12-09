import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from src.sensors.models import Sensor
from src.measurements.models import VariableCatalog, Measurement
from src.measurements.services import MeasurementService
from src.measurements.utils.cali_profile import HOURLY_PROFILE

class Command(BaseCommand):
    """
    Comando de gestión de Django para poblar la base de datos con datos históricos.
    
    Funcionalidad:
    1. Verifica si ya existen datos recientes para evitar duplicados (Idempotencia).
    2. Genera mediciones para los últimos 30 días basándose en el perfil de Cali.
    3. Simula variaciones aleatorias para dar realismo a las gráficas.
    """
    help = 'Genera datos históricos para los últimos 30 días si no existen.'

    def handle(self, *args, **kwargs):
        """
        Punto de entrada principal del comando.
        """
        self.stdout.write("--- Iniciando verificación de histórico ---")

        # 1. Configuración de rango de tiempo
        days_back = 30
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)

        # 2. Verificación de Idempotencia (Evitar duplicados)
        # Si ya hay mediciones en las últimas 24 horas registradas en la DB, asumimos que el histórico existe.
        if Measurement.objects.filter(measure_date__gte=start_date).exists():
            self.stdout.write(self.style.WARNING(
                'Aviso: Ya existen datos históricos en el rango de los últimos 30 días. '
                'Se omite la generación para evitar duplicados.'
            ))
            return

        # 3. Obtención de Sensores Activos
        sensors = Sensor.objects.filter(status=Sensor.Status.ACTIVE)
        if not sensors.exists():
            self.stdout.write(self.style.ERROR('Error: No hay sensores activos. Ejecuta seed_db primero.'))
            return

        # 4. Obtención de Variables del Catálogo
        try:
            var_pm25 = VariableCatalog.objects.get(code="PM2.5")
            var_temp = VariableCatalog.objects.get(code="TEMP")
            var_hum = VariableCatalog.objects.get(code="HUM")
        except VariableCatalog.DoesNotExist:
            self.stdout.write(self.style.ERROR('Error: Faltan variables en el catálogo (PM2.5, TEMP o HUM).'))
            return

        self.stdout.write(self.style.SUCCESS(f'Generando datos desde {start_date.date()} hasta {end_date.date()}...'))

        # 5. Bucle de Generación de Datos
        current_date = start_date
        total_created = 0

        # Iteramos hora por hora desde hace 30 días hasta hoy
        while current_date <= end_date:
            hour_str = str(current_date.hour)
            # Obtenemos el perfil base de Cali para esa hora específica
            base_data = HOURLY_PROFILE.get(hour_str, HOURLY_PROFILE.get("0"))
            
            for sensor in sensors:
                # Aplicamos "ruido" aleatorio para que los datos no se vean artificiales
                val_pm25 = max(0, base_data['PM2.5'] + random.uniform(-5.0, 5.0))
                val_temp = base_data['TEMP'] + random.uniform(-2.0, 2.0)
                # La humedad no puede pasar de 0 a 100
                val_hum = max(0, min(100, base_data['HUM'] + random.uniform(-5.0, 5.0)))

                try:
                    # Inserción directa (Bulk create sería más rápido, pero esto valida lógica)
                    # Nota: Usamos create_measurement del servicio si queremos validaciones estrictas,
                    # o Measurement.objects.create directamente para mayor velocidad en seeds masivos.
                    # Aquí usamos el modelo directo para no saturar los logs de validación.
                    Measurement.objects.create(
                        sensor=sensor,
                        variable=var_pm25,
                        value=round(val_pm25, 2),
                        measure_date=current_date
                    )
                    Measurement.objects.create(
                        sensor=sensor,
                        variable=var_temp,
                        value=round(val_temp, 2),
                        measure_date=current_date
                    )
                    Measurement.objects.create(
                        sensor=sensor,
                        variable=var_hum,
                        value=round(val_hum, 2),
                        measure_date=current_date
                    )
                    total_created += 3
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creando medición: {e}'))

            # Avanzamos el reloj una hora
            current_date += timedelta(hours=1)
            
            # Feedback visual cada 1000 registros
            if total_created % 2000 == 0:
                self.stdout.write(f"... {total_created} registros generados")

        self.stdout.write(self.style.SUCCESS(f'¡Histórico completado exitosamente! Total mediciones: {total_created}'))
        