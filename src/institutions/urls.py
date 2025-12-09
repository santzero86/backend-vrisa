from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApproveInstitutionView, InstitutionViewSet, RegisterInstitutionView

router = DefaultRouter()
router.register(r'institutes', InstitutionViewSet, basename='institute')

urlpatterns = [
    path('register/', RegisterInstitutionView.as_view(), name='register-institution'),
    path('requests/<int:pk>/approve/', ApproveInstitutionView.as_view(), name='approve-institution'),
    path('', include(router.urls)),
]