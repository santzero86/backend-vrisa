# Perfil aproximado de calidad del aire en Cali (basado en comportamiento histórico típico)
# Key: Hora del día (0-23)
# Values: Promedios esperados para esa hora

HOURLY_PROFILE = {
    0:  {'PM2.5': 15, 'TEMP': 21, 'HUM': 85}, # Medianoche
    1:  {'PM2.5': 12, 'TEMP': 20, 'HUM': 86},
    2:  {'PM2.5': 10, 'TEMP': 20, 'HUM': 87},
    3:  {'PM2.5': 8,  'TEMP': 19, 'HUM': 88},
    4:  {'PM2.5': 8,  'TEMP': 19, 'HUM': 88},
    5:  {'PM2.5': 12, 'TEMP': 19, 'HUM': 89}, # Empieza actividad
    6:  {'PM2.5': 25, 'TEMP': 20, 'HUM': 85}, # Tráfico mañana
    7:  {'PM2.5': 35, 'TEMP': 21, 'HUM': 80}, # Pico tráfico
    8:  {'PM2.5': 30, 'TEMP': 23, 'HUM': 75},
    9:  {'PM2.5': 25, 'TEMP': 25, 'HUM': 70},
    10: {'PM2.5': 20, 'TEMP': 27, 'HUM': 65},
    11: {'PM2.5': 18, 'TEMP': 29, 'HUM': 60},
    12: {'PM2.5': 15, 'TEMP': 31, 'HUM': 55}, # Mediodía (calor, menos tráfico)
    13: {'PM2.5': 15, 'TEMP': 32, 'HUM': 50},
    14: {'PM2.5': 18, 'TEMP': 32, 'HUM': 48}, # Max calor
    15: {'PM2.5': 20, 'TEMP': 31, 'HUM': 50},
    16: {'PM2.5': 22, 'TEMP': 30, 'HUM': 55},
    17: {'PM2.5': 30, 'TEMP': 28, 'HUM': 60}, # Tráfico tarde
    18: {'PM2.5': 40, 'TEMP': 27, 'HUM': 65}, # Pico tráfico regreso
    19: {'PM2.5': 35, 'TEMP': 26, 'HUM': 70},
    20: {'PM2.5': 30, 'TEMP': 25, 'HUM': 75},
    21: {'PM2.5': 25, 'TEMP': 24, 'HUM': 78},
    22: {'PM2.5': 20, 'TEMP': 23, 'HUM': 80},
    23: {'PM2.5': 18, 'TEMP': 22, 'HUM': 82},
}