from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from src.institutions.infrastructure.serializers import CreateInstitutionSerializer, InstitutionSerializer
from src.institutions.application.dto import CreateInstitutionDTO
from src.institutions.application.commands.create_institution import CreateInstitutionCommand
from src.institutions.infrastructure.repositories import InstitutionRepository
from src.users.infrastructure.repositories import UserRepository
from common.exceptions import ConflictError, NotFoundError

class InstitutionCreateView(APIView):
    def post(self, request):
        serializer = CreateInstitutionSerializer(data=request.data)
        if serializer.is_valid():
            create_dto = CreateInstitutionDTO(**serializer.validated_data)
            
            try:
                # 1. Instanciar dependencias
                institution_repo = InstitutionRepository()
                user_repo = UserRepository()
                command = CreateInstitutionCommand(institution_repo, user_repo)
                
                # 2. Ejecutar el caso de uso
                created_institution_dto = command.execute(create_dto)
                response_data = {
                    'id': created_institution_dto.id,
                    'institute_name': created_institution_dto.institute_name,
                    'physic_address': created_institution_dto.physic_address,
                    'representative_email': created_institution_dto.representative_email
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            except ConflictError as e:
                return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
            except NotFoundError as e:
                return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                # Captura de errores inesperados
                return Response({'error': 'Ocurrió un error inesperado.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)