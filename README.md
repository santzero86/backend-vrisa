Primero instala el paquete obligatorio:
```
sudo apt install python3-venv -y
```

Desde tu carpeta backend-vrisa:
```
python3 -m venv vrisa_env
```

Activar el entorno virtual
```
source vrisa_env/bin/activate
```
Cuando esté activo, verás algo como:

(venv) pepito@...

4. Instalar Django dentro del venv
```
pip install django djangorestframework
```