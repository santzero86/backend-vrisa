from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('src.users.urls')), 
    path('api/institutions/', include('src.institutions.urls')),
    path('api/stations/', include('src.stations.urls')),
    path('api/sensors/', include('src.sensors.urls')),
    path('api/measurements/', include('src.measurements.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
