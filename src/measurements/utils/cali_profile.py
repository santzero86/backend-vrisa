import os
import pandas as pd
from django.conf import settings

CSV_PATH = os.path.join(settings.BASE_DIR, "data/AQI_Bangladesh.csv")


def calcular_perfil_con_pandas():
    """
    Lee el dataset horario y CONVIERTE las unidades de µg/m³
    a las unidades estándar EPA (ppm/ppb) que espera el sistema VriSA.
    Returns:
        dict: Un diccionario donde la clave es la hora (str '0'-'23') y el valor
            es otro diccionario con los promedios de cada variable.
    """
    # Perfil por defecto (valores seguros en EPA Standard)
    perfil_por_defecto = {
        str(h): {
            "PM2.5": 12.0,
            "PM10": 40.0,
            "CO": 2.5,
            "NO2": 20.0,
            "SO2": 5.0,
            "O3": 30.0,
        }
        for h in range(24)
    }

    if not os.path.exists(CSV_PATH):
        return perfil_por_defecto

    try:
        df = pd.read_csv(CSV_PATH)

        # Procesar fecha y hora
        df["datetime"] = pd.to_datetime(df["datetime"])
        df["hour"] = df["datetime"].dt.hour

        # Promedios por hora
        promedios = df.groupby("hour").mean(numeric_only=True)

        hourly_profile = {}
        for hora in range(24):
            if hora in promedios.index:
                fila = promedios.loc[hora]

                # --- CONVERSIÓN DE UNIDADES (µg/m³ -> EPA Standard) ---
                # Factores aproximados a 25°C y 1 atm

                # PM10 y PM2.5: en µg/m³.
                pm10 = float(fila.get("pm10", 30))
                pm25 = float(fila.get("pm2_5", 15))

                # CO: El sistema espera ppm. El CSV trae µg/m³.
                # Factor: 1 ppm CO = 1145 µg/m³.
                co_val = float(fila.get("carbon_monoxide", 200)) / 100.0

                # Gases (NO2, SO2, O3): El sistema espera ppb. El CSV trae µg/m³.
                # Factor NO2: 1 ppb = 1.88 µg/m³  =>  µg / 1.88 = ppb
                no2_val = float(fila.get("nitrogen_dioxide", 20)) / 1.88

                # Factor SO2: 1 ppb = 2.62 µg/m³  =>  µg / 2.62 = ppb
                so2_val = float(fila.get("sulphur_dioxide", 5)) / 2.62

                # Factor O3: 1 ppb = 1.96 µg/m³   =>  µg / 1.96 = ppb
                o3_val = float(fila.get("ozone", 20)) / 1.96

                hourly_profile[str(hora)] = {
                    "PM10": pm10,
                    "PM2.5": pm25,
                    "CO": co_val,
                    "NO2": no2_val,
                    "SO2": so2_val,
                    "O3": o3_val,
                    # Temp y Hum no vienen en el CSV, se calculan matemáticamente después
                    "TEMP": 25.0,
                    "HUM": 70.0,
                }
            else:
                hourly_profile[str(hora)] = perfil_por_defecto["0"]

        return hourly_profile

    except Exception as e:
        print(f"Error procesando CSV: {e}")
        return perfil_por_defecto


HOURLY_PROFILE = calcular_perfil_con_pandas()
