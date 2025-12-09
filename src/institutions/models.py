from django.db import models
from django.conf import settings
from common.validation import ValidationStatus

User = settings.AUTH_USER_MODEL

class EnvironmentalInstitution(models.Model):
    """
    Representa una entidad institucional dentro del sistema ambiental.    
    Esta clase actúa como el modelo principal para almacenar la información
    básica, identidad visual y ubicación de las instituciones aliadas.
    """
    institute_name = models.CharField(max_length=255, unique=True, verbose_name="Nombre de la Institución")
    physic_address = models.CharField(max_length=255, verbose_name="Dirección Física")
    institute_logo = models.ImageField(
        upload_to='institution_logos/',
        null=True,
        blank=True,
        verbose_name="Logo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING,
        verbose_name="Estado de Validación"
    )
    
    def __str__(self):
        return self.institute_name
    
    class Meta:
        db_table = 'environmental_institution'
        verbose_name = "Institución Ambiental"
        verbose_name_plural = "Instituciones Ambientales"
        ordering = ['institute_name']

# Atributo multivaluado para almacenar un conjunto de colores asociados a la institución.
class InstitutionColorSet(models.Model):
    """
    Almacena la configuración de colores corporativos de una institución.
    Se utiliza para personalizar la interfaz de usuario según la identidad
    visual de cada institución. Permite una relación uno a muchos.
    """
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
    
    class Meta:
        db_table = 'institution_color_set'
        unique_together = ('institution', 'color_hex')
        verbose_name = "Color Institucional"
        verbose_name_plural = "Colores Institucionales"
