import os
import pandas as pd
from django.conf import settings

# 1. Ruta al archivo CSV
CSV_PATH = os.path.join(settings.BASE_DIR, 'LA_daily_air_quality.csv')

def calcular_perfil_con_pandas():
    # Diccionario por defecto por si falla la lectura (para que no se caiga el sistema)
    perfil_por_defecto = {0: {'PM2.5': 14.2, 'TEMP': 21.5, 'HUM': 82.1}} 

    if not os.path.exists(CSV_PATH):
        print(f"No se encontró el archivo {CSV_PATH}. Usando perfil por defecto.")
        return perfil_por_defecto

    try:
        # 2. Leemos el dataset
        df = pd.read_csv(CSV_PATH)
        
        # Convertimos la fecha para entender las horas
        df['date'] = pd.to_datetime(df['date'])
        
        # 3. Agrupamos por hora (0 a 23) y sacamos el promedio de TODO
        # Esto hace el trabajo matemático difícil por ti
        df['hour'] = df['date'].dt.hour
        promedios = df.groupby('hour').mean(numeric_only=True)

        # 4. Construimos el diccionario final (HOURLY_PROFILE)
        hourly_profile = {}

        for hora in range(24):
            if hora in promedios.index:
                fila = promedios.loc[hora]
                
                # Aquí mapeamos las columnas de TU CSV a las variables del sistema
                hourly_profile[str(hora)] = {
                    # Variables que SÍ están en el CSV:
                    "PM2.5": float(round(fila['pm2_5'], 2)),
                    "PM10":  float(round(fila['pm10'], 2)),
                    "CO":    float(round(fila['carbon_monoxide'], 2)),
                    "NO2":   float(round(fila['nitrogen_dioxide'], 2)),
                    "SO2":   float(round(fila['sulphur_dioxide'], 2)),
                    "O3":    float(round(fila['ozone'], 2)),

                    # Variables que NO están en el CSV (pero el sistema las necesita):
                    # Las simulamos o dejamos fijas para que no falle start_simulation.py
                    "TEMP": 25.0, 
                    "HUM": 70.0
                }
            else:
                # Si falta alguna hora en el CSV, rellenamos con genéricos
                hourly_profile[str(hora)] = {"PM2.5": 10, "TEMP": 25, "HUM": 70}

        print("Perfil de Cali generado exitosamente con Pandas.")
        return hourly_profile

    except Exception as e:
        print(f"Error calculando perfil: {e}")
        return perfil_por_defecto

# Esta variable es la que start_simulation.py va a leer.
HOURLY_PROFILE = calcular_perfil_con_pandas()