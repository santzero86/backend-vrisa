import os
import pandas as pd
from django.conf import settings

CSV_PATH = os.path.join(settings.BASE_DIR, 'data/LA_daily_air_quality.csv')

def calcular_perfil_con_pandas():
    """
    Lee el archivo CSV histórico y calcula el promedio de cada contaminante
    agrupado por hora del día (0-23).
    
    Returns:
        dict: Un diccionario donde la clave es la hora (str '0'-'23') y el valor
              es otro diccionario con los promedios de cada variable.
    """
    # Perfil de seguridad por si falla la lectura del CSV
    perfil_por_defecto = {
        str(h): {
            'PM2.5': 15.0, 'PM10': 30.0, 'CO': 200.0, 
            'NO2': 15.0, 'SO2': 5.0, 'O3': 20.0, 
            'TEMP': 25.0, 'HUM': 70.0
        } for h in range(24)
    }
    if not os.path.exists(CSV_PATH):
        print(f"No se encontró el archivo {CSV_PATH}. Usando perfil por defecto.")
        return perfil_por_defecto

    try:
        df = pd.read_csv(CSV_PATH)
        
        # Convierte la fecha para entender las horas
        df['date'] = pd.to_datetime(df['date'])
        
        # Agrupar por hora (0 a 23) y sacamos el promedio
        df['hour'] = df['date'].dt.hour

        # Calcular el promedio por hora ignorando nulos (NaN)
        promedios = df.groupby('hour').mean(numeric_only=True)

        # Construir el diccionario final (HOURLY_PROFILE)
        hourly_profile = {}

        for hora in range(24):
            if hora in promedios.index:
                fila = promedios.loc[hora]
                
                # Se mapean las columnas del CSV a las variables del sistema
                hourly_profile[str(hora)] = {
                    "PM2.5": float(round(fila['pm2_5'], 2)),
                    "PM10":  float(round(fila['pm10'], 2)),
                    "CO":    float(round(fila['carbon_monoxide'], 2)),
                    "NO2":   float(round(fila['nitrogen_dioxide'], 2)),
                    "SO2":   float(round(fila['sulphur_dioxide'], 2)),
                    "O3":    float(round(fila['ozone'], 2)),

                    # Variables que NO están en el CSV
                    "TEMP": 25.0, 
                    "HUM": 70.0
                }
            else:
                # Rellenamos con genéricos en caso de datos faltantes
                hourly_profile[str(hora)] = {"PM2.5": 10, "TEMP": 25, "HUM": 70}

        print("Perfil de Cali generado exitosamente con Pandas.")
        return hourly_profile

    except Exception as e:
        print(f"Error calculando perfil: {e}")
        return perfil_por_defecto

HOURLY_PROFILE = calcular_perfil_con_pandas()