from django.db import models
from django.conf import settings

# Importamos el modelo de usuario configurado en settings.py (tu usuario custom)
User = settings.AUTH_USER_MODEL

# Modelo principal que representa la entidad 'Institución'.
# Hereda de models.Model, lo que le da la capacidad de mapearse a una tabla SQL.
class EnvironmentalInstitution(models.Model):
    institute_name = models.CharField(max_length=255, unique=True, verbose_name="Nombre de la Institución")
    physic_address = models.CharField(max_length=255, verbose_name="Dirección Física")
    institute_logo = models.ImageField(upload_to='institution_logos/', null=True, blank=True, verbose_name="Logo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.institute_name
# Atributo multivaluado para almacenar un conjunto de colores asociados a la institución.
class InstitutionColorSet(models.Model):
    institution = models.ForeignKey(
        EnvironmentalInstitution,
        on_delete=models.CASCADE,
        related_name='colors',
        verbose_name="Institución"
    )

    color_hex = models.CharField(max_length=7, help_text="Formato hexadecimal, ej: #FF5733", verbose_name="Color Hex")
   # Esto asegura que una institución no pueda tener el mismo color repetido.
    class Meta:
        unique_together = ('institution', 'color_hex')
        verbose_name = "Color de Institución"

    def __str__(self):
        return f"{self.institution.institute_name} - {self.color_hex}"


#Solicititud de integración de una institución ambiental al sistema.
class IntegrationRequest(models.Model):
    # La institución que hace la solicitud.
    institution = models.ForeignKey(
        EnvironmentalInstitution,
        on_delete=models.CASCADE, # Si se borra la institución, se borran sus solicitudes.
        related_name='integration_requests',
        verbose_name="Institución Solicitante"
    )

    #Administrador de la estación a registrar
    proposed_station_admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='station_admin_requests',
        verbose_name="Administrador de Estación Propuesto"
    )

    # Estado de la solicitud
    class RequestStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        APPROVED = 'APPROVED', 'Aprobada'
        REJECTED = 'REJECTED', 'Rechazada'

    request_status = models.CharField(
        max_length=10,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
        verbose_name="Estado de la Solicitud"
    )
    
    request_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Solicitud")
    review_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Revisión")
    review_comments = models.TextField(blank=True, verbose_name="Comentarios de Revisión")

    # Usuario que revisó la solicitud, superadministrador
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests',
        verbose_name="Revisado por"
    )
    
    def __str__(self):
        return f"Solicitud de {self.institution.institute_name} - Estado: {self.get_request_status_display()}"