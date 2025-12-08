from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('src.users.urls')), 
    path('api/institutions/', include('src.institutions.urls')),
    path('api/stations/', include('src.stations.urls')),
    path('api/sensors/', include('src.sensors.urls')),
    path('api/measurements/', include('src.measurements.urls')),
]
