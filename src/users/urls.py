from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from src.users.views import CustomTokenObtainPairView, UserDetailView, UserRegistrationView

urlpatterns = [
    # Autenticación (JWT)
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Gestión de Usuarios
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
]