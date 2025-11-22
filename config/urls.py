from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('src.users.urls')), 
    path('api/users/', include('src.users.interfaces.urls')),
    path('api/institutions/', include('src.institutions.urls')),
]
