from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from src.users.views import (
    CustomTokenObtainPairView, 
    UserDetailView, 
    UserRegistrationView, 
    UserStatsView,
    ResearcherRegistrationView,
    PendingResearcherRequestsView,
    ApproveResearcherView,
    RejectResearcherView
)

urlpatterns = [
    # Autenticación (JWT)
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Gestión de Usuarios
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('register/researcher/', ResearcherRegistrationView.as_view(), name='researcher-register'),
    path('<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('stats/', UserStatsView.as_view(), name='user-stats'),
    
    # Gestión de solicitudes de investigadores (Admin)
    path('researchers/pending/', PendingResearcherRequestsView.as_view(), name='pending-researchers'),
    path('researchers/<int:user_role_id>/approve/', ApproveResearcherView.as_view(), name='approve-researcher'),
    path('researchers/<int:user_role_id>/reject/', RejectResearcherView.as_view(), name='reject-researcher'),
]