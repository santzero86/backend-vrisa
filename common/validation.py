from django.db import models


class ValidationStatus(models.TextChoices):
    """
    Estados de validación comunes en el sistema.
    Usado para solicitudes, roles, y otros procesos que requieren aprobación.
    """

    PENDING = "PENDING", "Pendiente de Validación"
    ACCEPTED = "ACCEPTED", "Aceptada"
    REJECTED = "REJECTED", "Rechazada"


class OperativeStatus(models.TextChoices):
    """
    Estados operativos para entidades como estaciones de monitoreo.
    """

    ACTIVE = "ACTIVE", "Operativa"
    PENDING = "PENDING", "Pendiente"
    REJECTED = "REJECTED", "Rechazada"
    MAINTENANCE = "MAINTENANCE", "En Mantenimiento"
    INACTIVE = "INACTIVE", "Inactiva"
    OFFLINE = "OFFLINE", "Fuera de Línea"


"""
Puntos de corte para el cálculo del Índice de Calidad del Aire (AQI).
Basado en el estándar US EPA para los siguientes criterios de contaminación: PM2.5, PM10, O3, CO, NO2, SO2
Cada entrada define un rango de concentración y su correspondiente rango de AQI.
"""
AQI_BREAKPOINTS = {
    # PM2.5 (µg/m³) - Promedios de 24 horas
    'PM2.5': [
        (0.0, 12.0, 0, 50),      # Good
        (12.1, 35.4, 51, 100),   # Moderate
        (35.5, 55.4, 101, 150),  # Unhealthy for Sensitive Groups
        (55.5, 150.4, 151, 200), # Unhealthy
        (150.5, 250.4, 201, 300),# Very Unhealthy
        (250.5, 350.4, 301, 400),# Hazardous
        (350.5, 500.4, 401, 500),# Hazardous
    ],

    # PM10 (µg/m³) - Promedios de 24 horas
    'PM10': [
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 504, 301, 400),
        (505, 604, 401, 500),
    ],

    # O3 (ppb) - Promedios de 8 horas
    'O3': [
        (0, 54, 0, 50),
        (55, 70, 51, 100),
        (71, 85, 101, 150),
        (86, 105, 151, 200),
        (106, 200, 201, 300),
        (201, 404, 301, 400),
        (405, 604, 401, 500),
    ],

    # CO (ppm) - Promedios de 8 horas
    'CO': [
        (0.0, 4.4, 0, 50),
        (4.5, 9.4, 51, 100),
        (9.5, 12.4, 101, 150),
        (12.5, 15.4, 151, 200),
        (15.5, 30.4, 201, 300),
        (30.5, 40.4, 301, 400),
        (40.5, 50.4, 401, 500),
    ],

    # NO2 (ppb) - Promedios de 1 hora
    'NO2': [
        (0, 53, 0, 50),
        (54, 100, 51, 100),
        (101, 360, 101, 150),
        (361, 649, 151, 200),
        (650, 1249, 201, 300),
        (1250, 1649, 301, 400),
        (1650, 2049, 401, 500),
    ],

    # SO2 (ppb) - Promedios de 1 hora
    'SO2': [
        (0, 35, 0, 50),
        (36, 75, 51, 100),
        (76, 185, 101, 150),
        (186, 304, 151, 200),
        (305, 604, 201, 300),
        (605, 804, 301, 400),
        (805, 1004, 401, 500),
    ],
}

"""
Categorías de AQI basadas en los rangos de valores.
Cada categoría incluye:
    - level: Nombre de la categoría
    - color: Código hexadecimal representativo
    - description: Descripción breve de la calidad del aire
"""
AQI_CATEGORIES = {
    (0, 50): {'level': 'Good', 'color': '#00E400', 'description': 'Calidad del aire satisfactoria'},
    (51, 100): {'level': 'Moderate', 'color': '#FFFF00', 'description': 'Calidad del aire aceptable'},
    (101, 150): {'level': 'Unhealthy for Sensitive Groups', 'color': '#FF7E00', 'description': 'Puede afectar a grupos sensibles'},
    (151, 200): {'level': 'Unhealthy', 'color': '#FF0000', 'description': 'Todos pueden experimentar efectos'},
    (201, 300): {'level': 'Very Unhealthy', 'color': '#8F3F97', 'description': 'Alerta de salud'},
    (301, 500): {'level': 'Hazardous', 'color': '#7E0023', 'description': 'Emergencia de salud'},
}
