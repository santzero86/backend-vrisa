from common.validation import ValidationStatus
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from src.users.models import User, UserRole
from src.users.serializers import (
    CustomTokenObtainPairSerializer,
    RegisterUserSerializer,
    UserSerializer,
    CompleteResearcherSerializer,
    ResearcherRequestSerializer,
)
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
                created_user = user_services.create_user(
                    input_serializer.validated_data
                )

                # 3. Formatear Salida
                output_serializer = UserSerializer(created_user)
                return Response(output_serializer.data, status=status.HTTP_201_CREATED)

            except Exception as e:
                print(f"Error interno: {str(e)}")
                return Response(
                    {"error": "Error interno del servidor", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            stats = user_services.get_user_stats_breakdown()
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResearcherRegistrationView(APIView):
    """
    Endpoint para completar el registro de investigadores.
    Requiere que el usuario esté autenticado.
    Permite subir documentos y completar información adicional.
    La solicitud queda pendiente hasta que un admin la apruebe.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        print("Data recibida (completar investigador):", request.data)
        print("Usuario autenticado:", request.user.email)

        input_serializer = CompleteResearcherSerializer(data=request.data)
        if input_serializer.is_valid():
            try:
                updated_user = user_services.complete_researcher_registration(
                    request.user, input_serializer.validated_data
                )
                output_serializer = UserSerializer(updated_user)
                return Response(
                    {
                        "message": "Registro completado correctamente. Espera la validación de un administrador.",
                        "user": output_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                print(f"Error interno: {str(e)}")
                return Response(
                    {"error": "Error interno del servidor", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        print("Errores:", input_serializer.errors)
        return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PendingResearcherRequestsView(APIView):
    """
    Endpoint para listar todas las solicitudes de investigadores pendientes.
    Lista solicitudes pendientes según el rol del que consulta
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        user = request.user
        
        # Validación de permisos 
        is_institution_head = UserRole.objects.filter(
            user=user,
            role__role_name='institution_head',
            approved_status=ValidationStatus.ACCEPTED
        ).exists()
        
        if not (user.is_superuser or is_institution_head):
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            pending_requests = user_services.get_pending_researcher_requests(user)
            serializer = ResearcherRequestSerializer(pending_requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Error obteniendo solicitudes', 'details': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ApproveResearcherView(APIView):
    """
    Endpoint para aprobar una solicitud de investigador.
    Solo accesible por administradores.
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_role_id):
        try:
            user_role = user_services.approve_researcher_request(
                user_role_id, request.user
            )
            return Response(
                {
                    "message": "Solicitud aprobada correctamente",
                    "status": user_role.approved_status,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": "Error al aprobar la solicitud", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RejectResearcherView(APIView):
    """
    Endpoint para rechazar una solicitud de investigador.
    Solo accesible por administradores.
    """

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_role_id):
        try:
            user_role = user_services.reject_researcher_request(
                user_role_id, request.user
            )
            return Response(
                {"message": "Solicitud rechazada", "status": user_role.approved_status},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": "Error al rechazar la solicitud", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
