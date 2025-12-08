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


### Levantar el proyecto desde un contenedor Docker
```
# Si es la primera vez, debe construirse la imagen
docker compose up --build -d

# En proximas veces, basta con levantar el contenedor
docker compose up -d
```

###  Ejecucion de Migraciones 
```
# Correr las migraciones dentro del contenedor 'backend'
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

### Usuarios creados por defecto
A nivel del archivo [seed_db](src/users/management/commands/seed_db.py) se tiene un script para poblar la base de datos en entorno de desarrollo.
Por ello, es recomendable tener en cuenta que existirán dos usuarios listos para utilizarse en el frontend:

**Superusuario**

    correo: admin@vrisa.com
    password: admin1234


**Administrador de estación** 

    correo: pepito.perez@gmail.com
    password: pepito1234


### Comandos de Django para crear una nueva app o inicializar la aplicacion

```
python manage.py startapp nombre_app

python manage.py runserver
```
