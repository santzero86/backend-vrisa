from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from src.users.models import User
from src.users.serializers import CustomTokenObtainPairSerializer, RegisterUserSerializer, UserSerializer
import src.users.services as user_services

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint de Login.
    Recibe email y password, retorna Access Token y Refresh Token.
    Usa el serializador personalizado para inyectar claims extra.
    """
    serializer_class = CustomTokenObtainPairSerializer

class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny] 
    def post(self, request):
        print("Data recibida:", request.data)
        # 1. Validar Entrada
        input_serializer = RegisterUserSerializer(data=request.data)
        if input_serializer.is_valid():
            try:
                # 2. Llamar a la lógica de negocio (Servicio)
                created_user = user_services.create_user(input_serializer.validated_data)
                
                # 3. Formatear Salida
                output_serializer = UserSerializer(created_user)
                return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                print(f"Error interno: {str(e)}")
                return Response(
                    {'error': 'Error interno del servidor', 'details': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        print("Errores:", input_serializer.errors)
        return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(APIView):
    def get(self, request, user_id: int):
        # El servicio maneja la lógica de "No encontrado" (404) internamente
        user = user_services.get_user_by_id(user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserStatsView(APIView):
    """
    Endpoint para obtener estadísticas generales de usuarios.
    Solo accesible por administradores.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        try:
            total_count = user_services.get_total_users_count()
            return Response({'total_users': total_count}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Error obteniendo estadísticas', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )