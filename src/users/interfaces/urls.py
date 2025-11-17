from django.urls import path
from src.users.interfaces.views import UserRegistrationView, UserDetailView

urlpatterns: list = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
]
