from django.urls import path
from .views import InstitutionCreateView

urlpatterns = [
    path('create/', InstitutionCreateView.as_view(), name='institution-create'),
]