from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from src.users.infrastructure.serializers import UserSerializer, RegisterUserSerializer
from src.users.infrastructure.repositories import UserRepository
from src.users.application.commands.register_user import RegisterUserCommand
from src.users.application.queries.get_user import GetUserQuery
from src.users.application.dto import RegisterUserDTO
from common.exceptions import NotFoundError, ConflictError

class UserRegistrationView(APIView):
    def post(self: 'UserRegistrationView', request) -> Response:
        serializer: RegisterUserSerializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            # The serializer gives us clean, validated data
            validated_data: dict = serializer.validated_data
            register_dto: RegisterUserDTO = RegisterUserDTO(**validated_data)

            try:
                # 1. Instantiate dependencies
                repository: UserRepository = UserRepository()
                command: RegisterUserCommand = RegisterUserCommand(repository)
                
                # 2. Execute the use case
                created_user_dto = command.execute(register_dto)
                
                # 3. Serialize the output DTO for the response
                response_serializer: UserSerializer = UserSerializer(created_user_dto)
                
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
            except ConflictError as e:
                return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
            except Exception as e:
                return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(APIView):
    def get(self: 'UserDetailView', request, user_id: int) -> Response:
        try:
            # 1. Instantiate dependencies
            repository: UserRepository = UserRepository()
            query: GetUserQuery = GetUserQuery(repository)

            # 2. Execute the use case
            user_dto = query.execute(user_id)

            # 3. Serialize the output DTO for the response
            serializer: UserSerializer = UserSerializer(user_dto)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except NotFoundError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
