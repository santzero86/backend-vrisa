import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ImageRL
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.utils import timezone
import matplotlib.pyplot as plt
from src.measurements.models import Measurement, VariableCatalog
import matplotlib
matplotlib.use('Agg')

class PDFReportGenerator:
    def __init__(self, buffer):
        self.buffer = buffer
        self.doc = SimpleDocTemplate(self.buffer, pagesize=letter)
        self.elements = []
        self.styles = getSampleStyleSheet()
        
        # Estilo personalizado para títulos
        self.styles.add(ParagraphStyle(name='CenterTitle', parent=self.styles['Heading1'], alignment=1))

    def add_header(self, title, subtitle):
        self.elements.append(Paragraph(title, self.styles['CenterTitle']))
        self.elements.append(Paragraph(subtitle, self.styles['Normal']))
        self.elements.append(Spacer(1, 20))
        self.elements.append(Paragraph(f"Generado el: {timezone.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal']))
        self.elements.append(Spacer(1, 20))

    def generate_air_quality_report(self, station, date, variable_code=None):
        """
        Genera reporte tabular.
        Args:
            variable_code (str, optional): Código de la variable para filtrar (ej: 'PM2.5').
        """
        subtitle = f"Fecha consultada: {date}"
        if variable_code:
            subtitle += f" | Variable: {variable_code}"
            
        self.add_header(f"Reporte de Calidad del Aire - {station.station_name}", subtitle)

        # Filtro base
        filters = {
            'sensor__station': station,
            'measure_date__date': date
        }
        # Filtro opcional por variable
        if variable_code:
            filters['variable__code'] = variable_code

        measurements = Measurement.objects.filter(**filters).select_related('variable').order_by('measure_date')

        if not measurements.exists():
            self.elements.append(Paragraph("No hay datos registrados para los criterios seleccionados.", self.styles['Normal']))
        else:
            data = [['Hora', 'Variable', 'Valor', 'Unidad', 'Estado']]
            for m in measurements:
                limit = m.variable.max_expected_value
                status = "Normal" if m.value <= limit else "ALERTA"
                
                row = [
                    m.measure_date.strftime('%H:%M'),
                    m.variable.code,
                    f"{m.value:.2f}",
                    m.variable.unit,
                    status
                ]
                data.append(row)

            # Estilo de tabla mejorado
            table = Table(data, colWidths=[60, 100, 80, 60, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.26, 0.22, 0.95)), # Brand Blue
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            self.elements.append(table)

        self.doc.build(self.elements)

    def generate_trends_report(self, station, start_date, end_date, variable_code=None):
        """
        Genera gráficas de tendencia. Si hay variable_code, solo genera esa gráfica.
        """
        subtitle = f"Desde: {start_date} Hasta: {end_date}"
        if variable_code:
            subtitle += f" | Variable: {variable_code}"

        self.add_header("Reporte de Tendencias", f"Estación: {station.station_name} | {subtitle}")

        # Determinar qué variables graficar
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

                plt.figure(figsize=(7, 3.5)) # Gráfica más compacta
                plt.plot(dates, values, label=var.name, color='#4339F2', linewidth=2)
                plt.title(f"Comportamiento de {var.name}")
                plt.ylabel(f"{var.unit}")
                plt.grid(True, linestyle='--', alpha=0.6)
                plt.xticks(rotation=20, fontsize=8)
                plt.tight_layout()

                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=100)
                plt.close()
                img_buffer.seek(0)

                self.elements.append(Paragraph(f"Variable: {var.name} ({var.code})", self.styles['Heading3']))
                self.elements.append(ImageRL(img_buffer, width=450, height=225))
                self.elements.append(Spacer(1, 15))
            elif variable_code:
                 self.elements.append(Paragraph(f"No hay datos para {var.name} en este rango.", self.styles['Normal']))

        self.doc.build(self.elements)

    def generate_alerts_report(self, station_id=None):
        """Genera reporte de valores fuera de rango (Alertas Críticas)"""
        title = "Reporte de Alertas Críticas"
        subtitle = "Mediciones que exceden los límites permitidos (Últimas 24h)"
        self.add_header(title, subtitle)

        # Lógica: Buscar mediciones donde value > variable.max_expected_value
        alerts = Measurement.objects.filter(
            measure_date__gte=timezone.now() - timezone.timedelta(hours=24)
        ).select_related('sensor__station', 'variable')

        if station_id:
            alerts = alerts.filter(sensor__station_id=station_id)

        # Filtrar en Python (o usar F expressions en query compleja)
        critical_alerts = [m for m in alerts if m.value > m.variable.max_expected_value]

        if not critical_alerts:
            self.elements.append(Paragraph("No se han detectado alertas críticas en las últimas 24 horas.", self.styles['Normal']))
        else:
            data = [['Fecha/Hora', 'Estación', 'Variable', 'Valor Registrado', 'Límite Máximo']]
            for m in critical_alerts:
                data.append([
                    m.measure_date.strftime('%Y-%m-%d %H:%M'),
                    m.sensor.station.station_name if m.sensor.station else "N/A",
                    m.variable.code,
                    f"{m.value:.2f} {m.variable.unit}",
                    f"{m.variable.max_expected_value:.2f}"
                ])

            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred), # Encabezado Rojo
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.red), # Texto de datos en rojo
            ]))
            self.elements.append(table)

        self.doc.build(self.elements)