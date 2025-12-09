import io
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image as ImageRL
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from src.sensors.models import Sensor
from .models import Measurement, VariableCatalog

# Configurar backend no interactivo para matplotlib
matplotlib.use('Agg')

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

        # 1. Validación de Negocio: Sensor Activo
        if sensor.status != Sensor.Status.ACTIVE:
            raise ValidationError(
                f"El sensor {sensor.serial_number} no está activo (Estado: {sensor.status})."
            )

        # 2. Validación de Negocio: Rango de valores (Calidad de datos simple)
        if value < variable.min_expected_value or value > variable.max_expected_value:
            raise ValidationError(
                f"El valor {value} está fuera del rango permitido para {variable.code}."
            )

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
        self.styles.add(ParagraphStyle(name='CenterTitle', parent=self.styles['Heading1'], alignment=1))
        self.styles.add(ParagraphStyle(name='SmallText', parent=self.styles['Normal'], fontSize=8))

    def add_header(self, title, subtitle):
        """
        Agrega el encabezado estándar al flujo del documento.
        Incluye el título principal, subtítulo y la fecha de generación automática.

        Args:
            title (str): Título principal del reporte.
            subtitle (str): Subtítulo (ej: rango de fechas, filtros aplicados).
        """
        self.elements.append(Paragraph(title, self.styles['CenterTitle']))
        self.elements.append(Paragraph(subtitle, self.styles['Normal']))
        self.elements.append(Spacer(1, 20))
        self.elements.append(Paragraph(f"Generado el: {timezone.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal']))
        self.elements.append(Spacer(1, 20))

    def generate_air_quality_report(self, station, start_date, end_date, variable_code=None):
        """
        Genera el Reporte Ejecutivo de Calidad del Aire.
        
        Este método consulta los datos históricos, los procesa utilizando Pandas para
        obtener estadísticas descriptivas (Media, Mín, Máx, Desviación Estándar) y
        valida si los valores exceden los límites permitidos en el catálogo de variables.

        Estructura del reporte:
        1. Tabla Resumen: Métricas por variable con indicador de estado (OK/ALERTA).
        2. Detalle de Alertas: Lista específica de mediciones que superaron los límites (si existen).

        Args:
            station (MonitoringStation): Instancia de la estación a consultar.
            start_date (str/date): Fecha de inicio del rango de análisis.
            end_date (str/date): Fecha de fin del rango de análisis.
            variable_code (str, optional): Código de variable para filtrar (ej: 'PM2.5'). Si es None, trae todas.
        """
        subtitle = f"Periodo analizado: {start_date} al {end_date}"
        if variable_code:
            subtitle += f" | Variable filtrada: {variable_code}"
            
        self.add_header(f"Reporte Ejecutivo de Calidad del Aire - {station.station_name}", subtitle)

        # Obtener Datos
        filters = {
            'sensor__station': station,
            'measure_date__date__range': [start_date, end_date]
        }
        if variable_code:
            filters['variable__code'] = variable_code

        # Obtenemos los campos necesarios para el DataFrame
        queryset = Measurement.objects.filter(**filters).select_related('variable').values(
            'measure_date', 
            'value', 
            'variable__code', 
            'variable__name', 
            'variable__unit', 
            'variable__min_expected_value', 
            'variable__max_expected_value'
        )

        if not queryset.exists():
            self.elements.append(Paragraph("No hay datos registrados para los criterios seleccionados.", self.styles['Normal']))
            self.doc.build(self.elements)
            return

        # Procesamiento con Pandas
        df = pd.DataFrame(list(queryset))
        grouped = df.groupby('variable__code')

        # --- Tabla resumen con estadísticos centrales ---
        self.elements.append(Paragraph("Resumen Estadístico por Variable", self.styles['Heading2']))
        self.elements.append(Spacer(1, 10))

        summary_data = [['Variable', 'Unidad', 'N° Muestras', 'Promedio', 'Mínimo', 'Máximo', 'Mediana', 'Desv. Std', 'Límite', 'Estado']]
        
        # Lista para guardar alertas detalladas
        alerts_detected = []

        for code, group in grouped:
            # Cálculos estadísticos
            count = group['value'].count()
            mean = group['value'].mean()
            min_val = group['value'].min()
            max_val = group['value'].max()
            median = group['value'].median()
            std_dev = group['value'].std()
            
            # Metadatos de la variable (tomamos el primero del grupo)
            unit = group['variable__unit'].iloc[0]
            limit_max = group['variable__max_expected_value'].iloc[0]
            limit_min = group['variable__min_expected_value'].iloc[0]

            # Evaluar Estado
            status = "OK"
            status_color = colors.green
            
            # Si el promedio o el máximo exceden los límites
            if max_val > limit_max or min_val < limit_min:
                status = "ALERTA"
                status_color = colors.red
                
                # Guardar detalles para la sección de alertas
                # Filtramos las filas de este grupo que exceden el límite
                outliers = group[(group['value'] > limit_max) | (group['value'] < limit_min)]
                for _, row in outliers.iterrows():
                    alerts_detected.append([
                        row['measure_date'].strftime('%Y-%m-%d %H:%M'),
                        code,
                        f"{row['value']:.2f}",
                        f"{limit_max:.2f}"
                    ])

            row = [
                code,
                unit,
                f"{count}",
                f"{mean:.2f}",
                f"{min_val:.2f}",
                f"{max_val:.2f}",
                f"{median:.2f}",
                f"{std_dev:.2f}" if not pd.isna(std_dev) else "0.00",
                f"{limit_max:.0f}",
                status
            ]
            summary_data.append(row)

        # Renderizar Tabla Resumen
        table = Table(summary_data, colWidths=[60, 50, 60, 60, 50, 50, 50, 60, 50, 60])
        
        # Estilos dinámicos para la columna de Estado
        table_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.26, 0.22, 0.95)), # Header Azul
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ]

        # Pintar celdas de estado (Fila, Columna 9 es 'Estado')
        for i, row in enumerate(summary_data[1:], start=1):
            bg_color = colors.red if row[-1] == "ALERTA" else colors.green
            table_styles.append(('BACKGROUND', (9, i), (9, i), bg_color))
            table_styles.append(('TEXTCOLOR', (9, i), (9, i), colors.white))
            table_styles.append(('FONTNAME', (9, i), (9, i), 'Helvetica-Bold'))

        table.setStyle(TableStyle(table_styles))
        self.elements.append(table)
        self.elements.append(Spacer(1, 30))

        # --- Detalle de alertas ---
        if alerts_detected:
            self.elements.append(Paragraph("Detalle de Eventos Críticos (Alertas)", self.styles['Heading2']))
            self.elements.append(Paragraph("A continuación se listan los momentos específicos donde se superaron los límites permitidos:", self.styles['Normal']))
            self.elements.append(Spacer(1, 10))

            # Ordenar por fecha
            alerts_detected.sort(key=lambda x: x[0])
            
            # Headers de alertas
            alerts_data = [['Fecha y Hora', 'Variable', 'Valor Registrado', 'Límite Permitido']] + alerts_detected
            
            alert_table = Table(alerts_data, colWidths=[150, 100, 100, 100], repeatRows=1)
            alert_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.firebrick),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]))
            self.elements.append(alert_table)
        else:
            self.elements.append(Paragraph("No se detectaron anomalías ni excesos en los límites durante este periodo.", self.styles['Normal']))

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

        self.add_header("Reporte de Tendencias", f"Estación: {station.station_name} | {subtitle}")

        if variable_code:
            variables = VariableCatalog.objects.filter(code=variable_code)
        else:
            variables = VariableCatalog.objects.all()

        for var in variables:
            data = Measurement.objects.filter(
                sensor__station=station,
                variable=var,
                measure_date__range=[start_date, end_date]
            ).order_by('measure_date')

            if data.exists():
                dates = [m.measure_date for m in data]
                values = [m.value for m in data]

                plt.figure(figsize=(10, 4)) 
                plt.plot(dates, values, label=var.name, color='#4339F2', linewidth=2)
                plt.axhline(y=var.max_expected_value, color='r', linestyle='--', label='Límite')
                plt.title(f"Comportamiento de {var.name}")
                plt.ylabel(f"{var.unit}")
                plt.legend()
                plt.grid(True, linestyle='--', alpha=0.6)
                plt.tight_layout()

                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=100)
                plt.close()
                img_buffer.seek(0)

                self.elements.append(Paragraph(f"Variable: {var.name} ({var.code})", self.styles['Heading3']))
                self.elements.append(ImageRL(img_buffer, width=500, height=200))
                self.elements.append(Spacer(1, 15))

        self.doc.build(self.elements)

    def generate_alerts_report(self, station_id=None):
        """
        Genera un reporte de incidentes críticos basado en las últimas 24 horas.
        Identifica mediciones que superaron el valor máximo esperado (`max_expected_value`)
        configurado en el catálogo de variables.

        Args:
            station_id (int, optional): ID de la estación para filtrar. Si es None, busca en todas.
        """
        title = "Reporte de Alertas Críticas (Últimas 24h)"
        subtitle = "Mediciones fuera de rango"
        self.add_header(title, subtitle)

        alerts = Measurement.objects.filter(
            measure_date__gte=timezone.now() - timezone.timedelta(hours=24)
        ).select_related('sensor__station', 'variable')

        if station_id:
            alerts = alerts.filter(sensor__station_id=station_id)

        critical_alerts = [m for m in alerts if m.value > m.variable.max_expected_value]

        if not critical_alerts:
            self.elements.append(Paragraph("No se han detectado alertas críticas.", self.styles['Normal']))
        else:
            data = [['Fecha/Hora', 'Estación', 'Variable', 'Valor', 'Límite']]
            for m in critical_alerts:
                data.append([
                    m.measure_date.strftime('%Y-%m-%d %H:%M'),
                    m.sensor.station.station_name,
                    m.variable.code,
                    f"{m.value:.2f}",
                    f"{m.variable.max_expected_value:.0f}"
                ])

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            self.elements.append(table)

        self.doc.build(self.elements)
