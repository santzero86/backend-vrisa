from django.contrib import admin
from .models import EnvironmentalInstitution, IntegrationRequest, InstitutionColorSet

class InstitutionColorSetInline(admin.TabularInline):
    model = InstitutionColorSet
    extra = 1

@admin.register(EnvironmentalInstitution)
class EnvironmentalInstitutionAdmin(admin.ModelAdmin):
    list_display = ('institute_name', 'physic_address', 'created_at')
    search_fields = ('institute_name', 'representative__email')
    list_filter = ('created_at',)
    inlines = [InstitutionColorSetInline] 

@admin.register(IntegrationRequest)
class IntegrationRequestAdmin(admin.ModelAdmin):
    list_display = ('institution', 'request_status', 'request_date', 'reviewed_by')
    search_fields = ('institution__institute_name',)
    list_filter = ('request_status', 'request_date')