import io
from datetime import timedelta
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image as ImageRL
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from common.validation import AQI_BREAKPOINTS, AQI_CATEGORIES
from src.sensors.models import Sensor
from .models import Measurement, VariableCatalog

# Configurar backend no interactivo para matplotlib
matplotlib.use("Agg")


class MeasurementService:
    """
    Capa de servicio para la gestión de mediciones.
    Centraliza la lógica de negocio, validaciones de integridad y control de calidad
    de datos antes de persistir en la base de datos.
    """

    @staticmethod
    def create_measurement(data: dict) -> Measurement:
        """
        Crea un registro de medición validando reglas estrictas de negocio.
        Flujo de Validación:
        1. Verifica que el Sensor exista y esté en estado 'ACTIVE'.
        2. Verifica que el valor medido esté dentro de los rangos físicos posibles
           definidos en el catálogo de variables (Control de Calidad).
        Args:
            data (dict): Diccionario con datos validados (sensor, variable, value, date). Proviene de serializer.validated_data.
        Returns:
            Measurement: La instancia del modelo creada y guardada.
        Raises:
            - Si el sensor está INACTIVO o en MANTENIMIENTO.
            - Si el valor (value) está fuera de los rangos min/max esperados.
        """
        sensor = data.get("sensor")
        variable = data.get("variable")
        value = data.get("value")

        # Sensor Activo
        if sensor.status != Sensor.Status.ACTIVE:
            raise ValidationError(
                f"El sensor {sensor.serial_number} no está activo (Estado: {sensor.status})."
            )

        if value < 0:
            raise ValidationError(
                f"El valor no puede ser negativo para {variable.code}."
            )

        if variable.code == "HUM" and value > 100:
            raise ValidationError("La humedad no puede superar el 100%.")

        with transaction.atomic():
            measurement = Measurement.objects.create(**data)
            return measurement


class PDFReportGenerator:
    """
    Generador de reportes en formato PDF para el sistema VriSA.

    Utiliza ReportLab para la maquetación del documento y Pandas/Matplotlib
    para el procesamiento de datos y generación de gráficas.
    """

    def __init__(self, buffer):
        """
        Inicializa el generador de reportes.

        Args:
            buffer (io.BytesIO): Buffer de memoria donde se escribirá el archivo PDF binario.
        """
        self.buffer = buffer
        # Cambiamos a horizontal (landscape) para que quepan todas las columnas estadísticas
        self.doc = SimpleDocTemplate(self.buffer, pagesize=landscape(letter))
        self.elements = []
        self.styles = getSampleStyleSheet()

        # Estilos personalizados
        self.styles.add(
            ParagraphStyle(
                name="CenterTitle", parent=self.styles["Heading1"], alignment=1
            )
        )
        self.styles.add(
            ParagraphStyle(name="SmallText", parent=self.styles["Normal"], fontSize=8)
        )

    def add_header(self, title, subtitle):
        """
        Agrega el encabezado estándar al flujo del documento.
        Incluye el título principal, subtítulo y la fecha de generación automática.

        Args:
            title (str): Título principal del reporte.
            subtitle (str): Subtítulo (ej: rango de fechas, filtros aplicados).
        """
        self.elements.append(Paragraph(title, self.styles["CenterTitle"]))
        self.elements.append(Paragraph(subtitle, self.styles["Normal"]))
        self.elements.append(Spacer(1, 20))
        self.elements.append(
            Paragraph(
                f"Generado el: {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                self.styles["Normal"],
            )
        )
        self.elements.append(Spacer(1, 20))

    def generate_air_quality_report(
        self, station, start_date, end_date, variable_code=None
    ):
        """
        Genera el Reporte Ejecutivo de Calidad del Aire.

        Este método consulta los datos históricos, los procesa utilizando Pandas para
        obtener estadísticas descriptivas (Media, Mín, Máx, Desviación Estándar) y
        valida si los valores exceden los límites permitidos en el catálogo de variables.

        Estructura del reporte:
        1. Tabla Resumen: Métricas por variable con indicador de estado (OK/ALERTA).
        2. Detalle de Alertas: Lista específica de mediciones que superaron los límites (si existen).

        Args:
            station (MonitoringStation): Instancia de la estación a consultar. Si es None, se consideran todas.
            start_date (str/date): Fecha de inicio del rango de análisis.
            end_date (str/date): Fecha de fin del rango de análisis.
            variable_code (str, optional): Código de variable para filtrar (ej: 'PM2.5'). Si es None, trae todas.
        """
        scope_name = (
            station.station_name
            if station
            else "Red de Monitoreo de Cali (Consolidado)"
        )
        subtitle = f"Periodo analizado: {start_date} al {end_date}"
        if variable_code:
            subtitle += f" | Variable filtrada: {variable_code}"

        self.add_header(
            f"Reporte Ejecutivo de Calidad del Aire - {scope_name}", subtitle
        )

        # Filtros Dinámicos
        filters = {"measure_date__date__range": [start_date, end_date]}
        if station:
            filters["sensor__station"] = station
        if variable_code:
            filters["variable__code"] = variable_code

        # Se obtienen los campos necesarios para el DataFrame
        queryset = (
            Measurement.objects.filter(**filters)
            .select_related("variable")
            .values(
                "measure_date",
                "value",
                "variable__code",
                "variable__name",
                "variable__unit",
                "variable__min_expected_value",
                "variable__max_expected_value",
                "sensor__station__station_name",
            )
        )

        if not queryset.exists():
            self.elements.append(
                Paragraph(
                    "No hay datos registrados para los criterios seleccionados.",
                    self.styles["Normal"],
                )
            )
            self.doc.build(self.elements)
            return

        # Procesamiento con Pandas
        df = pd.DataFrame(list(queryset))
        grouped = df.groupby("variable__code")

        # --- Tabla resumen con estadísticos centrales ---
        self.elements.append(
            Paragraph("Resumen Estadístico por Variable", self.styles["Heading2"])
        )
        self.elements.append(Spacer(1, 10))
        summary_data = [
            [
                "Variable",
                "Unidad",
                "N° Muestras",
                "Promedio",
                "Mínimo",
                "Máximo",
                "Mediana",
                "Desv. Std",
                "C.V (%)",
                "Límite",
                "Estado",
            ]
        ]

        # Lista para guardar alertas detalladas
        alerts_detected = []

        for code, group in grouped:
            # Cálculos estadísticos
            count = group["value"].count()
            mean = group["value"].mean()
            min_val = group["value"].min()
            max_val = group["value"].max()
            median = group["value"].median()
            std_dev = group["value"].std()

            # CV = (Desviación Estándar / Media) * 100
            # Evitamos división por cero
            if mean != 0 and not pd.isna(std_dev):
                cv = (std_dev / abs(mean)) * 100
            else:
                cv = 0.0

            # Metadatos de la variable (tomamos el primero del grupo)
            unit = group["variable__unit"].iloc[0]
            limit_max = group["variable__max_expected_value"].iloc[0]
            limit_min = group["variable__min_expected_value"].iloc[0]

            # Evaluar Estado
            status = "OK"
            if max_val > limit_max or min_val < limit_min:
                status = "ALERTA"
                outliers = group[
                    (group["value"] > limit_max) | (group["value"] < limit_min)
                ]
                for _, row in outliers.iterrows():
                    # Aquí usamos el nombre de la estación que viene en el queryset
                    st_name = row.get("sensor__station__station_name", "N/A")
                    alerts_detected.append(
                        [
                            row["measure_date"].strftime("%Y-%m-%d %H:%M"),
                            st_name,  # Columna extra para saber de qué estación es la alerta
                            code,
                            f"{row['value']:.2f}",
                            f"{limit_max:.2f}",
                        ]
                    )

            row = [
                code,
                unit,
                f"{count}",
                f"{mean:.2f}",
                f"{min_val:.2f}",
                f"{max_val:.2f}",
                f"{median:.2f}",
                f"{std_dev:.2f}" if not pd.isna(std_dev) else "0.00",
                f"{cv:.1f}%",
                f"{limit_max:.0f}",
                status,
            ]
            summary_data.append(row)

        col_widths = [55, 45, 55, 55, 45, 45, 45, 55, 50, 45, 55]
        # Renderizar Tabla Resumen
        table = Table(summary_data, colWidths=col_widths)

        # Estilos dinámicos para la columna de Estado
        table_styles = [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.Color(0.26, 0.22, 0.95),
            ),  # Header Azul
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ]

        # Pintar celdas de estado (Fila, Columna 9 es 'Estado')
        for i, row in enumerate(summary_data[1:], start=1):
            bg_color = colors.red if row[-1] == "ALERTA" else colors.green
            table_styles.append(("BACKGROUND", (10, i), (10, i), bg_color))
            table_styles.append(("TEXTCOLOR", (10, i), (10, i), colors.white))
            table_styles.append(("FONTNAME", (10, i), (10, i), "Helvetica-Bold"))

        table.setStyle(TableStyle(table_styles))
        self.elements.append(table)
        self.elements.append(Spacer(1, 30))

        # --- Detalle de alertas ---
        if alerts_detected:
            self.elements.append(
                Paragraph(
                    "Detalle de Eventos Críticos (Alertas)", self.styles["Heading2"]
                )
            )
            self.elements.append(
                Paragraph(
                    "A continuación se listan los momentos específicos donde se superaron los límites permitidos:",
                    self.styles["Normal"],
                )
            )
            self.elements.append(Spacer(1, 10))

            # Ordenar por fecha
            alerts_detected.sort(key=lambda x: x[0])

            # Headers de alertas
            alerts_data = [
                [
                    "Fecha y Hora",
                    "Estación",
                    "Variable",
                    "Valor Registrado",
                    "Límite Permitido",
                ]
            ] + alerts_detected

            alert_table = Table(
                alerts_data, colWidths=[110, 140, 60, 90, 90], repeatRows=1
            )
            alert_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.firebrick),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.whitesmoke, colors.white],
                        ),
                    ]
                )
            )
            self.elements.append(alert_table)
        else:
            self.elements.append(
                Paragraph(
                    "No se detectaron anomalías ni excesos en los límites durante este periodo.",
                    self.styles["Normal"],
                )
            )

        self.doc.build(self.elements)

    def generate_trends_report(self, station, start_date, end_date, variable_code=None):
        """
        Genera un reporte visual de tendencias.
        Crea gráficas de línea (time-series) para cada variable solicitada usando Matplotlib
        y las incrusta como imágenes en el PDF.

        Args:
            station (MonitoringStation): La estación a analizar.
            start_date (str/date): Fecha de inicio.
            end_date (str/date): Fecha de fin.
            variable_code (str, optional): Si se especifica, solo grafica esa variable.
        """
        subtitle = f"Desde: {start_date} Hasta: {end_date}"
        if variable_code:
            subtitle += f" | Variable: {variable_code}"

        self.add_header(
            "Reporte de Tendencias", f"Estación: {station.station_name} | {subtitle}"
        )

        if variable_code:
            variables = VariableCatalog.objects.filter(code=variable_code)
        else:
            variables = VariableCatalog.objects.all()

        for var in variables:
            data = Measurement.objects.filter(
                sensor__station=station,
                variable=var,
                measure_date__range=[start_date, end_date],
            ).order_by("measure_date")

            if data.exists():
                dates = [m.measure_date for m in data]
                values = [m.value for m in data]

                plt.figure(figsize=(10, 4))
                plt.plot(dates, values, label=var.name, color="#4339F2", linewidth=2)
                plt.axhline(
                    y=var.max_expected_value, color="r", linestyle="--", label="Límite"
                )
                plt.title(f"Comportamiento de {var.name}")
                plt.ylabel(f"{var.unit}")
                plt.legend()
                plt.grid(True, linestyle="--", alpha=0.6)
                plt.tight_layout()

                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format="png", dpi=100)
                plt.close()
                img_buffer.seek(0)

                self.elements.append(
                    Paragraph(
                        f"Variable: {var.name} ({var.code})", self.styles["Heading3"]
                    )
                )
                self.elements.append(ImageRL(img_buffer, width=500, height=200))
                self.elements.append(Spacer(1, 15))

        self.doc.build(self.elements)

    def generate_alerts_report(self, station, start_date, end_date):
        """
        Genera un reporte de incidentes críticos basado en las últimas 24 horas.
        Identifica mediciones que superaron el valor máximo esperado (`max_expected_value`)
        configurado en el catálogo de variables.

        Args:
            station_id (int, optional): ID de la estación para filtrar. Si es None, busca en todas.
        """
        scope_name = station.station_name if station else "Red de Monitoreo de Cali"
        self.add_header(
            f"Reporte de Alertas Críticas - {scope_name}",
            f"Periodo: {start_date} al {end_date}",
        )

        # Filtros
        filters = {"measure_date__date__range": [start_date, end_date]}
        if station:
            filters["sensor__station"] = station

        # Consultar datos
        queryset = Measurement.objects.filter(**filters).select_related(
            "variable", "sensor__station"
        )

        alerts_detected = []

        # Procesar para encontrar valores fuera de rango ( > max o < min )
        for m in queryset:
            is_critical = False
            limit_ref = 0

            # Verificación Límite Superior
            if m.value > m.variable.max_expected_value:
                is_critical = True
                limit_ref = m.variable.max_expected_value
            # Verificación Límite Inferior
            elif m.value < m.variable.min_expected_value:
                is_critical = True
                limit_ref = m.variable.min_expected_value

            if is_critical:
                alerts_detected.append(
                    [
                        m.measure_date.strftime("%Y-%m-%d %H:%M"),
                        m.sensor.station.station_name,
                        m.variable.code,
                        f"{m.value:.2f} {m.variable.unit}",
                        f"{limit_ref:.2f}",
                    ]
                )

        # Renderizar Tabla
        if not alerts_detected:
            self.elements.append(
                Paragraph(
                    "No se han detectado alertas críticas en el periodo seleccionado.",
                    self.styles["Normal"],
                )
            )
        else:
            self.elements.append(
                Paragraph(
                    f"Se encontraron {len(alerts_detected)} eventos fuera de norma:",
                    self.styles["Normal"],
                )
            )
            self.elements.append(Spacer(1, 10))

            # Ordenar por fecha
            alerts_detected.sort(key=lambda x: x[0])

            data = [
                [
                    "Fecha/Hora",
                    "Estación",
                    "Variable",
                    "Valor Registrado",
                    "Límite Permitido",
                ]
            ] + alerts_detected

            table = Table(data, colWidths=[110, 150, 80, 100, 100], repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.firebrick,
                        ),  # Rojo Alerta
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.whitesmoke, colors.white],
                        ),
                        (
                            "TEXTCOLOR",
                            (3, 1),
                            (3, -1),
                            colors.red,
                        ),  # Texto del valor en rojo
                    ]
                )
            )
            self.elements.append(table)

        self.doc.build(self.elements)


class AQICalculatorService:
    """
    Servicio para calcular el Índice de Calidad del Aire (AQI).
    Implementa el estándar US EPA utilizando 6 criterios de contaminación:
    - PM2.5 (Material Particulado 2.5)
    - PM10 (Material Particulado 10)
    - O3 (Ozono)
    - CO (Monóxido de Carbono)
    - NO2 (Dióxido de Nitrógeno)
    - SO2 (Dióxido de Azufre)
    """

    # Contaminantes soportados para cálculo de AQI
    SUPPORTED_POLLUTANTS = ["PM2.5", "PM10", "O3", "CO", "NO2", "SO2"]

    @staticmethod
    def calculate_sub_index(pollutant_code: str, concentration: float) -> float:
        """
        Calcula el sub-índice de AQI para un contaminante específico.
        Usa la fórmula EPA:
        I = [(I_high - I_low) / (C_high - C_low)] * (C - C_low) + I_low
        Args:
            pollutant_code: Código del contaminante (ej: 'PM2.5', 'O3')
            concentration: Concentración medida del contaminante
        Returns:
            float: Valor del sub-índice (0-500+)
        Raises:
            ValueError: Si el contaminante no está soportado
        """
        if pollutant_code not in AQI_BREAKPOINTS:
            raise ValueError(
                f"Contaminante {pollutant_code} no soportado para cálculo de AQI"
            )

        if concentration < 0:
            return 0

        breakpoints = AQI_BREAKPOINTS[pollutant_code]

        # Encontrar el breakpoint correcto
        for c_low, c_high, i_low, i_high in breakpoints:
            if c_low <= concentration <= c_high:
                # Fórmula lineal EPA
                sub_index = ((i_high - i_low) / (c_high - c_low)) * (
                    concentration - c_low
                ) + i_low
                return round(sub_index, 2)

        # Si excede el máximo, retornar el valor más alto
        if concentration > breakpoints[-1][1]:
            # Usar el último breakpoint para calcular una extrapolación
            c_low, c_high, i_low, i_high = breakpoints[-1]
            sub_index = ((i_high - i_low) / (c_high - c_low)) * (
                concentration - c_low
            ) + i_low
            return round(sub_index, 2)

        return 0

    @staticmethod
    def get_aqi_category(aqi_value: float) -> dict:
        """
        Obtiene la categoría descriptiva del AQI.
        Args:
            aqi_value: Valor del AQI calculado
        Returns:
            dict: Información de la categoría (level, color, description)
        """
        for (low, high), category_info in AQI_CATEGORIES.items():
            if low <= aqi_value <= high:
                return category_info

        # Si excede 500, retornar Hazardous
        return AQI_CATEGORIES[(301, 500)]

    @staticmethod
    def calculate_aqi_for_station(station_id: int = None, timestamp=None) -> dict:
        """
        Calcula el AQI actual.
        - Si se provee station_id: Calcula el AQI específico para esa estación.
        - Si station_id es None: Calcula el AQI promedio de la ciudad (basado en todos los sensores activos).
        """
        if timestamp is None:
            timestamp = timezone.now()

        # Ventana de tiempo: últimas 24 horas para tener datos representativos
        time_window_start = timestamp - timedelta(hours=24)

        sub_indices = {}

        # Calcular sub-índice para cada contaminante
        for pollutant_code in AQICalculatorService.SUPPORTED_POLLUTANTS:
            try:
                # Obtener la variable del catálogo
                variable = VariableCatalog.objects.get(code=pollutant_code)

                # Construcción dinámica del QuerySet
                filters = {
                    'variable': variable,
                    'measure_date__gte': time_window_start,
                    'measure_date__lte': timestamp,
                    'sensor__status': Sensor.Status.ACTIVE # IMPORTANTE: Solo datos confiables
                }

                # Si pidieron una estación específica, filtramos por ella.
                # Si es None, el filtro no se aplica y trae datos de toda la red (Cali).
                if station_id:
                    filters['sensor__station_id'] = station_id

                measurements = Measurement.objects.filter(**filters)

                if measurements.exists():
                    # Calculamos el promedio de concentración.
                    # Al ser un AQI "Live" o consolidado, el promedio es la medida estadística 
                    # más segura para representar el estado actual de una zona o estación.
                    avg_concentration = measurements.aggregate(Avg("value"))["value__avg"]

                    if avg_concentration is not None:
                        # Calcular sub-índice usando la fórmula EPA
                        sub_index = AQICalculatorService.calculate_sub_index(
                            pollutant_code, avg_concentration
                        )
                        sub_indices[pollutant_code] = sub_index

            except VariableCatalog.DoesNotExist:
                continue

        # Si después de revisar todos los contaminantes no hay datos:
        if not sub_indices:
            scope_msg = f"la estación {station_id}" if station_id else "la red de monitoreo"
            # Podemos lanzar error o devolver un objeto vacío. 
            # Lanzar error permite al frontend mostrar "Sin datos" o un estado de carga.
            raise ValueError(
                f"No hay datos suficientes recientes (últimas 24h) para calcular AQI en {scope_msg}"
            )

        # El AQI final es el MÁXIMO de todos los sub-índices (el contaminante crítico)
        aqi_value = max(sub_indices.values())
        dominant_pollutant = max(sub_indices, key=sub_indices.get)

        # Obtener información de la categoría (Color, Nivel, Descripción)
        category_info = AQICalculatorService.get_aqi_category(aqi_value)

        return {
            "aqi": round(aqi_value, 2),
            "category": category_info["level"],
            "category_description": category_info["description"],
            "color": category_info["color"],
            "dominant_pollutant": dominant_pollutant,
            "timestamp": timestamp,
            "sub_indices": sub_indices,
            # Retornamos el ID para referencia, o None si fue global
            "station_id": station_id 
        }
    
    @staticmethod
    def calculate_aqi_historical(
        station_id: int, start_date, end_date, interval_hours=1
    ):
        """
        Calcula el AQI histórico para una estación en un rango de fechas.
        Genera valores de AQI agregados por intervalos de tiempo y los persiste
        como mediciones en la base de datos con variable_code='AQI'.
        Args:
            station_id: ID de la estación
            start_date: Fecha de inicio
            end_date: Fecha de fin
            interval_hours: Intervalo en horas entre cálculos (default: 1)
        Returns:
            int: Cantidad de registros de AQI creados
        """
        # Obtener o crear la variable AQI en el catálogo
        aqi_variable, created = VariableCatalog.objects.get_or_create(
            code="AQI",
            defaults={
                "name": "Índice de Calidad del Aire",
                "unit": "AQI",
                "min_expected_value": 0,
                "max_expected_value": 500,
            },
        )

        # Obtener un sensor de la estación para asociar las mediciones
        # (Usamos el primer sensor activo disponible)
        sensor = Sensor.objects.filter(
            station_id=station_id, status=Sensor.Status.ACTIVE
        ).first()

        if not sensor:
            raise ValueError(f"No hay sensores activos en la estación {station_id}")

        current_time = start_date
        aqi_records = []
        created_count = 0

        while current_time <= end_date:
            try:
                # Calcular AQI para este timestamp
                aqi_data = AQICalculatorService.calculate_aqi_for_station(
                    station_id, current_time
                )

                # Verificar si ya existe una medición de AQI en este timestamp
                existing = Measurement.objects.filter(
                    sensor=sensor, variable=aqi_variable, measure_date=current_time
                ).exists()

                if not existing:
                    # Crear registro de medición
                    aqi_records.append(
                        Measurement(
                            sensor=sensor,
                            variable=aqi_variable,
                            value=aqi_data["aqi"],
                            measure_date=current_time,
                        )
                    )
                    created_count += 1

                # Hacer bulk insert cada 500 registros
                if len(aqi_records) >= 500:
                    Measurement.objects.bulk_create(aqi_records, ignore_conflicts=True)
                    aqi_records = []

            except ValueError:
                # Si no hay datos suficientes para este timestamp, continuar
                pass

            current_time += timedelta(hours=interval_hours)

        # Insertar registros restantes
        if aqi_records:
            Measurement.objects.bulk_create(aqi_records, ignore_conflicts=True)

        return created_count
