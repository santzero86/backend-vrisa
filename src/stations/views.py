from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import MonitoringStation, StationAffiliationRequest
from .serializers import MonitoringStationSerializer, StationAffiliationRequestSerializer
from .services import create_affiliation_request, review_affiliation_request


class StationViewSet(viewsets.ModelViewSet):
    """
    Endpoint: /api/stations/
    Permite listar y gestionar las estaciones de monitoreo.
    """

    queryset = MonitoringStation.objects.all()
    serializer_class = MonitoringStationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Opcional: Filtrar solo estaciones activas para usuarios normales,
        o todas para administradores.
        """
        queryset = super().get_queryset()
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(operative_status=status)
        return queryset


class StationAffiliationViewSet(viewsets.ModelViewSet):
    """
    Endpoint: /api/stations/affiliations/
    Gestión de solicitudes de afiliación.
    """

    queryset = StationAffiliationRequest.objects.all()
    serializer_class = StationAffiliationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtrado inteligente:
        - Si soy Station Admin: Veo mis solicitudes creadas.
        - Si soy Institution Admin: Veo solicitudes recibidas por mi institución.
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Filtro simple por query param si se necesita
        target_inst = self.request.query_params.get("target_institution")
        if target_inst:
            queryset = queryset.filter(target_institution_id=target_inst)

        if user.institution:
            # Si es un admin de institución, se muestran las solicitudes dirigidas a su institución
            return queryset.filter(target_institution=user.institution)
        else:
            # Si es un station admin, se muestran las solicitudes que él creó
            return queryset.filter(requester=user)

    def create(self, request, *args, **kwargs):
        """
        POST: Crear una solicitud (Solo Station Admins)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Delegamos al servicio, pasando el usuario autenticado
            req_instance = create_affiliation_request(
                serializer.validated_data, request.user
            )
            output = self.get_serializer(req_instance)
            return Response(output.data, status=status.HTTP_201_CREATED)

        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        """
        POST: /api/stations/affiliations/{id}/review/
        Cuerpo: { "status": "ACCEPTED" | "REJECTED", "comments": "..." }
        Permite a la institución aprobar o rechazar.
        """
        new_status = request.data.get("status")
        comments = request.data.get("comments", "")

        if new_status not in ["ACCEPTED", "REJECTED"]:
            return Response(
                {"detail": "Estado inválido"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            req_instance = review_affiliation_request(
                pk, request.user, new_status, comments
            )
            return Response(self.get_serializer(req_instance).data)

        except DjangoValidationError as e:
            return Response({"detail": e.messages}, status=status.HTTP_403_FORBIDDEN)
