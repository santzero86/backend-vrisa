# Generated manually for PostGIS migration

from django.contrib.gis.db import models
from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


def migrate_coordinates_to_point(apps, schema_editor):
    """
    Migra las coordenadas de lat/long a un campo Point.
    """
    MonitoringStation = apps.get_model('stations', 'MonitoringStation')
    for station in MonitoringStation.objects.all():
        if station.geographic_location_lat is not None and station.geographic_location_long is not None:
            # Importante: Point(longitud, latitud)
            from django.contrib.gis.geos import Point
            station.location = Point(
                station.geographic_location_long,
                station.geographic_location_lat,
                srid=4326
            )
            station.save(update_fields=['location'])


def reverse_migrate_point_to_coordinates(apps, schema_editor):
    """
    Migración inversa: restaura lat/long desde el campo Point.
    """
    MonitoringStation = apps.get_model('stations', 'MonitoringStation')
    for station in MonitoringStation.objects.all():
        if station.location:
            station.geographic_location_lat = station.location.y
            station.geographic_location_long = station.location.x
            station.save(update_fields=['geographic_location_lat', 'geographic_location_long'])


class Migration(migrations.Migration):

    dependencies = [
        ('stations', '0005_alter_monitoringstation_operative_status'),
    ]

    operations = [
        # 1. Habilitar extensión PostGIS
        CreateExtension('postgis'),

        # 2. Agregar nuevo campo location (temporalmente nullable para migración)
        migrations.AddField(
            model_name='monitoringstation',
            name='location',
            field=models.PointField(srid=4326, verbose_name='Ubicación', null=True, blank=True),
        ),

        # 3. Migrar datos de lat/long a location
        migrations.RunPython(
            migrate_coordinates_to_point,
            reverse_migrate_point_to_coordinates
        ),

        # 4. Hacer el campo location obligatorio
        migrations.AlterField(
            model_name='monitoringstation',
            name='location',
            field=models.PointField(srid=4326, verbose_name='Ubicación'),
        ),

        # 5. Eliminar campos antiguos
        migrations.RemoveField(
            model_name='monitoringstation',
            name='geographic_location_lat',
        ),
        migrations.RemoveField(
            model_name='monitoringstation',
            name='geographic_location_long',
        ),
    ]
