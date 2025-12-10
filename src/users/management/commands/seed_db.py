from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from common.validation import ValidationStatus
from src.institutions.models import EnvironmentalInstitution, InstitutionColorSet
from src.measurements.models import VariableCatalog
from src.sensors.models import Sensor
from src.stations.models import MonitoringStation
from src.users.models import Role, User, UserRole


class Command(BaseCommand):
    help = "Puebla la DB con datos semilla y configura variables/sensores"

    def handle(self, *args, **kwargs):
        """Método principal que orquesta la creación de datos semilla."""
        try:
            with transaction.atomic():
                # Roles base
                self.create_roles()

                # Super Admin
                self.create_super_admin()

                # Variables de Medición (Catálogo)
                self.create_variables()

                dagma = self.create_institution()
                pepito = self.create_user(dagma)
                station = self.create_station(dagma, pepito)
                self.create_institution_head(dagma)

                # Crear Sensor asociado a la estación
                self.create_sensors(station)

                self.stdout.write(
                    self.style.SUCCESS("¡Base de datos poblada exitosamente!")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def create_roles(self):
        roles = [
            "super_admin",
            "station_admin",
            "researcher",
            "institution_member",
            "institution_head",
            "citizen",
        ]
        for role_name in roles:
            Role.objects.get_or_create(role_name=role_name)
        self.stdout.write(f"- Roles verificados/creados: {len(roles)}")

    def create_institution(self) -> EnvironmentalInstitution:
        inst_data = {
            "institute_name": "DAGMA",
            "physic_address": "Av. 5AN #20N-08, Cali",
            "validation_status": "ACCEPTED",
        }

        institution, created = EnvironmentalInstitution.objects.get_or_create(
            institute_name=inst_data["institute_name"], defaults=inst_data
        )

        if created:
            InstitutionColorSet.objects.create(
                institution=institution, color_hex="#4339F2"
            )
            InstitutionColorSet.objects.create(
                institution=institution, color_hex="#22C55E"
            )
            self.stdout.write(f"- Institución creada: {institution.institute_name}")
        else:
            self.stdout.write(f"- Institución ya existía: {institution.institute_name}")

        return institution

    def create_user(self, institution: EnvironmentalInstitution) -> User:
        email = "pepito.perez@gmail.com"
        password = "pepito1234"

        # Verificamos si existe por email
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                email=email,
                password=password,
                phone="3101234567",
                first_name="Pepito",
                last_name="Pérez",
                job_title="Director Técnico",
                institution=institution,
                is_active=True,
            )  # type: ignore

            # Asignar rol de Admin de Estación
            role_admin = Role.objects.get(role_name="station_admin")
            UserRole.objects.create(
                user=user,
                role=role_admin,
                approved_status=ValidationStatus.ACCEPTED,
                assigned_by=user,
            )

            self.stdout.write(f"- Usuario por defecto creado: {user.email}")
            return user
        else:
            user = User.objects.get(email=email)
            self.stdout.write(f"- Usuario ya existía: {user.email}")
            return user

    def create_super_admin(self):
        email = "admin@vrisa.com"
        password = "admin1234"

        if not User.objects.filter(email=email).exists():
            admin_user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name="Admin",
                last_name="Vrisa",
                phone="0000000000",
            )  # type: ignore

            role_super = Role.objects.get(role_name="super_admin")
            UserRole.objects.create(
                user=admin_user,
                role=role_super,
                approved_status=ValidationStatus.ACCEPTED,
            )

            self.stdout.write(self.style.SUCCESS(f"- Superusuario creado: {email}"))
        else:
            self.stdout.write(f"- Superusuario ya existía: {email}")

    def create_institution_head(self, institution: EnvironmentalInstitution):
        """
        Crea el usuario Representante de la Institución (John Doe).
        Rol: institution_head
        """
        email = "john.doe@dagma.gov"
        password = "doe1234"

        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                email=email,
                password=password,
                phone="3009876543",
                first_name="John",
                last_name="Doe",
                job_title="Director General",
                institution=institution,
                is_active=True,
            )  # type: ignore

            # Asignar rol de Cabeza de Institución
            role_head = Role.objects.get(role_name="institution_head")
            UserRole.objects.create(
                user=user,
                role=role_head,
                approved_status=ValidationStatus.ACCEPTED,
                assigned_by=user,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"- Usuario Representante creado: {user.email} (Rol: institution_head)"
                )
            )
        else:
            self.stdout.write(f"- Usuario Representante ya existía: {email}")

    def create_station(self, institution: EnvironmentalInstitution, manager: User):
        station_name = "La Flora"

        # Coordenadas de La Flora, Cali (IMPORTANTE: Point(longitud, latitud))
        location_point = Point(-76.526, 3.476, srid=4326)

        station, created = MonitoringStation.objects.get_or_create(
            station_name=station_name,
            defaults={
                "location": location_point,
                "institution": institution,
                "manager_user": manager,
                "operative_status": "ACTIVE",
            },
        )

        if created:
            self.stdout.write(
                f"- Estación creada: {station.station_name} (Token: {station.authentication_token})"
            )
        else:
            self.stdout.write(f"- Estación ya existía: {station.station_name}")

        return station

    def create_variables(self):
        """Inicializa el catálogo completo de variables."""
        vars_data = [
            {
                "code": "PM2.5",
                "name": "Material Particulado 2.5",
                "unit": "µg/m³",
                "min": 0,
                "max": 500,
            },
            {
                "code": "PM10",
                "name": "Material Particulado 10",
                "unit": "µg/m³",
                "min": 0,
                "max": 600,
            },
            {
                "code": "CO",
                "name": "Monóxido de Carbono",
                "unit": "µg/m³",
                "min": 0,
                "max": 15000,
            },
            {
                "code": "NO2",
                "name": "Dióxido de Nitrógeno",
                "unit": "µg/m³",
                "min": 0,
                "max": 400,
            },
            {
                "code": "SO2",
                "name": "Dióxido de Azufre",
                "unit": "µg/m³",
                "min": 0,
                "max": 500,
            },
            {
                "code": "O3",
                "name": "Ozono Troposférico",
                "unit": "µg/m³",
                "min": 0,
                "max": 300,
            },
            {
                "code": "TEMP",
                "name": "Temperatura",
                "unit": "°C",
                "min": -10,
                "max": 50,
            },
            {
                "code": "HUM",
                "name": "Humedad Relativa",
                "unit": "%",
                "min": 0,
                "max": 100,
            },
            {
                "code": "AQI",
                "name": "Índice de Calidad del Aire",
                "unit": "AQI",
                "min": 0,
                "max": 500,
            },
        ]
        for var in vars_data:
            VariableCatalog.objects.get_or_create(
                code=var["code"],
                defaults={
                    "name": var["name"],
                    "unit": var["unit"],
                    "min_expected_value": var["min"],
                    "max_expected_value": var["max"],
                },
            )

    def create_sensors(self, station: MonitoringStation):
        """
        Crea los 4 sensores específicos solicitados.
        Usamos el campo 'model' para definir su especialidad.
        """
        sensors_fleet = [
            # SENSOR 1: Clima (Temp + Humedad)
            {
                "serial": "SN-CLIMA-001",
                "model": "VriSA-Meteo",
                "desc": "Sensor Climático",
            },
            # SENSOR 2: Carbono y PM2.5
            {
                "serial": "SN-URBAN-001",
                "model": "VriSA-Urban-Eco",
                "desc": "Sensor Urbano (CO/PM2.5)",
            },
            # SENSOR 3: Industrial (Resto de gases y partículas pesadas)
            {
                "serial": "SN-INDUS-001",
                "model": "VriSA-Heavy-Ind",
                "desc": "Sensor Industrial (PM10/NO2/SO2)",
            },
            # SENSOR 4: Especializado en Ozono
            {
                "serial": "SN-OZONE-001",
                "model": "VriSA-O3-Only",
                "desc": "Sensor Especializado Ozono",
            },
        ]

        self.stdout.write("Configurando flota de 4 sensores...")

        for s_data in sensors_fleet:
            sensor, created = Sensor.objects.update_or_create(
                serial_number=s_data["serial"],
                defaults={
                    "model": s_data["model"],  # ESTO ES CLAVE
                    "manufacturer": "VriSA Labs",
                    "installation_date": timezone.now().date(),
                    "status": Sensor.Status.ACTIVE,
                    "station": station,
                },
            )
            state = "Creado" if created else "Verificado"
            self.stdout.write(f'- {state}: {s_data["desc"]} ({sensor.serial_number})')

    def create_sensor(self, station: MonitoringStation):
        """Crea un sensor físico y lo asigna a la estación"""
        sensor, created = Sensor.objects.get_or_create(
            serial_number="SN-LAFLORA-001",
            defaults={
                "model": "VriSA-Air-X1",
                "manufacturer": "VriSA Labs",
                "installation_date": timezone.now().date(),
                "status": Sensor.Status.ACTIVE,
                "station": station,
            },
        )
        if created:
            self.stdout.write(
                f"- Sensor creado: {sensor.serial_number} -> Asignado a {station.station_name}"
            )
        else:
            self.stdout.write(f"- Sensor ya existía: {sensor.serial_number}")
