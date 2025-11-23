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
pip install -r requirements.txt
```


### Levantar el proyecto
```
docker-compose up --build
```

###  Ejecucion de Migraciones 
```
# Correr las migraciones dentro del contenedor 'backend'
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Crear superusuario dentro del contenedor
docker-compose exec backend python manage.py createsuperuser
```


(vrisa_env) pepito@~    python manage.py createsuperuser
Dirección de correo: admin@vrisa.com
First name: Admin
Last name: Vrisa
Password: 
Password (again): 
Superuser created successfully.


### Comandos de Django para crear una nueva app o inicializar la aplicacion

```
python manage.py startapp nombre_app

python manage.py runserver
```
