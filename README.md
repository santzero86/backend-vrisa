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
pip install psycopg2
```

```
python manage.py makemigrations
```


## Ejecucion de Migraciones 

```
# Correr las migraciones dentro del contenedor 'backend'
docker-compose exec backend python manage.py migrate

# Crear superusuario dentro del contenedor
docker-compose exec backend python manage.py createsuperuser
```