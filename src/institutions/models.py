from django.db import models
from src.users.models import User

# Modelo para representar una institución ambiental que puede solicitar integración al sistema.
class EnvironmentalInstitution(models.Model):
    institute_name = models.CharField(max_length=255, unique=True, verbose_name="Nombre de la Institución")
    physic_address = models.CharField(max_length=255, verbose_name="Dirección Física")
    institute_logo = models.ImageField(upload_to='institution_logos/', null=True, blank=True, verbose_name="Logo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.institute_name

#Solicititud de integración de una institución ambiental al sistema.
class IntegrationRequest(models.Model):
    # La institución que hace la solicitud.
    institution = models.ForeignKey(
        EnvironmentalInstitution,
        on_delete=models.CASCADE, # Si se borra la institución, se borran sus solicitudes.
        related_name='integration_requests',
        verbose_name="Institución Solicitante"
    )

    #Administrador de la estiación a registrar
    proposed_station_admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
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