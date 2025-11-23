from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
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
                # En una app real, aquí deberíamos registrar el error (logging)
                return Response(
                    {'error': 'Error interno del servidor', 'details': str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(APIView):
    def get(self, request, user_id: int):
        # El servicio maneja la lógica de "No encontrado" (404) internamente
        user = user_services.get_user_by_id(user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
