from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from src.users.models import User, Role
from src.institutions.models import EnvironmentalInstitution, InstitutionColorSet
from src.stations.models import MonitoringStation
from src.measurements.models import VariableCatalog
from src.sensors.models import Sensor

class Command(BaseCommand):
    help = 'Puebla la DB con datos semilla y configura variables/sensores'

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                self.create_roles()
                
                # Variables de Medición (Catálogo)
                self.create_variables()

                dagma = self.create_institution()
                pepito = self.create_user(dagma)
                station = self.create_station(dagma, pepito)

                # Crear Sensor asociado a la estación
                self.create_sensor(station)

                self.stdout.write(self.style.SUCCESS('¡Base de datos poblada exitosamente!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
    
    def create_roles(self):
        roles = ['super_admin', 'station_admin', 'researcher', 'institution_worker', 'citizen']
        for role_name in roles:
            Role.objects.get_or_create(role_name=role_name)
        self.stdout.write(f'- Roles verificados/creados: {len(roles)}')

    def create_institution(self) -> EnvironmentalInstitution:
        inst_data = {
            'institute_name': 'DAGMA',
            'physic_address': 'Av. 5AN #20N-08, Cali',
            'validation_status': 'ACCEPTED'
        }
        
        institution, created = EnvironmentalInstitution.objects.get_or_create(
            institute_name=inst_data['institute_name'],
            defaults=inst_data
        )

        if created:
            InstitutionColorSet.objects.create(institution=institution, color_hex='#4339F2')
            InstitutionColorSet.objects.create(institution=institution, color_hex='#22C55E')
            self.stdout.write(f'- Institución creada: {institution.institute_name}')
        else:
            self.stdout.write(f'- Institución ya existía: {institution.institute_name}')
        
        return institution

    def create_user(self, institution: EnvironmentalInstitution) -> User:
        email = 'pepito.perez@gmail.com'
        password = 'pepito1234'
        
        # Verificamos si existe por email
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name='Pepito',
                last_name='Pérez',
                job_title='Director Técnico',
                institution=institution,
                is_active=True
            ) # type: ignore
            
            # Asignar rol de Admin de Estación
            role_admin = Role.objects.get(role_name='station_admin')
            user.roles.add(role_admin)
            
            self.stdout.write(f'- Usuario creado: {user.email} (Pass: {password})')
            return user
        else:
            user = User.objects.get(email=email)
            self.stdout.write(f'- Usuario ya existía: {user.email}')
            return user

    def create_station(self, institution: EnvironmentalInstitution, manager: User):
        station_name = 'La Flora'
        
        station, created = MonitoringStation.objects.get_or_create(
            station_name=station_name,
            defaults={
                'geographic_location_lat': 3.476,
                'geographic_location_long': -76.526,
                'institution': institution,
                'manager_user': manager,
                'operative_status': 'ACTIVE'
            }
        )

        if created:
            self.stdout.write(f'- Estación creada: {station.station_name} (Token: {station.authentication_token})')
        else:
            self.stdout.write(f'- Estación ya existía: {station.station_name}')
        
        return station

    def create_variables(self):
        """Inicializa el catálogo de variables"""
        vars_data = [
            {'code': "PM2.5", 'name': "Material Particulado 2.5", 'unit': "µg/m³", 'min': 0, 'max': 500},
            {'code': "TEMP", 'name': "Temperatura", 'unit': "°C", 'min': -10, 'max': 50},
            {'code': "HUM", 'name': "Humedad", 'unit': "%", 'min': 0, 'max': 100},
        ]

        for var in vars_data:
            obj, created = VariableCatalog.objects.get_or_create(
                code=var['code'],
                defaults={
                    'name': var['name'],
                    'unit': var['unit'],
                    'min_expected_value': var['min'],
                    'max_expected_value': var['max']
                }
            )
            if created:
                self.stdout.write(f'- Variable creada: {obj.name}')

    def create_sensor(self, station: MonitoringStation):
        """Crea un sensor físico y lo asigna a la estación"""
        sensor, created = Sensor.objects.get_or_create(
            serial_number="SN-LAFLORA-001",
            defaults={
                'model': 'VriSA-Air-X1',
                'manufacturer': 'VriSA Labs',
                'installation_date': timezone.now().date(),
                'status': Sensor.Status.ACTIVE,
                'station': station
            }
        )
        if created:
            self.stdout.write(f'- Sensor creado: {sensor.serial_number} -> Asignado a {station.station_name}')
        else:
            self.stdout.write(f'- Sensor ya existía: {sensor.serial_number}')
