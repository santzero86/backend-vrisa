import requests
import time
from datetime import datetime

# ================= CONFIGURACIÓN =================
WAQI_TOKEN = "5d29432e758a787d8c83242cfe4f4e4394ce0ac4"
WAQI_STATION_URL = f"https://api.waqi.info/feed/cali/?token={WAQI_TOKEN}"

# Configuración de API Local (VriSA)
API_URL = "http://localhost:8000/api"
# Usuario y pass de un admin o usuario registrado en el sistema
VRISA_USER = "san@gmail.com" 
VRISA_PASS = "1234"

SENSOR_ID = 1  
VAR_MAP = {
    "pm25": 1,  # ID de PM2.5 en DB
    "t": 2,     # ID de Temperatura
    "h": 3      # ID de Humedad
}
# =================================================

def obtener_token_vrisa():
    """Se loguea en tu sistema para tener permiso de escribir datos"""
    try:
        resp = requests.post(f"{API_URL}/users/login/", json={
            "email": VRISA_USER,
            "password": VRISA_PASS
        })
        if resp.status_code == 200:
            return resp.json()['access']
        print(f"Error login VriSA: {resp.text}")
        return None
    except Exception as e:
        print(f"VriSA caído: {e}")
        return None

def correr_ingesta():
    print("--- Iniciando Servicio de Ingesta de Datos Reales (WAQI) ---")
    
    while True:
        # 1. Obtener Token fresco del backend
        jwt_token = obtener_token_vrisa()
        if not jwt_token:
            time.sleep(10)
            continue

        headers = {"Authorization": f"Bearer {jwt_token}"}

        try:
            # 2. Consultar datos reales a WAQI
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Consultando API Mundial...")
            waqi_resp = requests.get(WAQI_STATION_URL).json()

            if waqi_resp['status'] == 'ok':
                datos = waqi_resp['data']['iaqi'] # 'iaqi' tiene los valores individuales
                
                # 3. Recorrer los datos y enviarlos a tu Backend
                for key, val_obj in datos.items():
                    if key in VAR_MAP:
                        payload = {
                            "sensor": SENSOR_ID,
                            "variable": VAR_MAP[key],
                            "value": float(val_obj['v']),
                            "measure_date": datetime.now().isoformat()
                        }
                        
                        # POST a tu endpoint de mediciones
                        res = requests.post(
                            f"{API_URL}/measurements/data/", 
                            json=payload, 
                            headers=headers
                        )
                        
                        if res.status_code == 201:
                            print(f"   > Guardado {key}: {val_obj['v']}")
                        else:
                            print(f"   > Error guardando {key}: {res.text}")
            else:
                print("   > Error en respuesta WAQI")

        except Exception as e:
            print(f"   > Error de conexión: {e}")

        # Esperar 5 minutos antes de la próxima consulta
        # (Los datos reales no cambian cada segundo)
        print("   > Esperando 5 minutos...")
        time.sleep(300) 

if __name__ == "__main__":
    correr_ingesta()