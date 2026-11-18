from rest_framework import mixins, viewsets

from apps.etims.models import EtimsSequence
from apps.etims.permissions import CanManageEtimsConfig
from apps.etims.serializers import EtimsSequenceSerializer


class EtimsSequenceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = EtimsSequence.objects.all()
    serializer_class = EtimsSequenceSerializer
    permission_classes = [CanManageEtimsConfig]
    pagination_class = None