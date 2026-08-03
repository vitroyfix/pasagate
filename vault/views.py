from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from vault.models import Merchant
from vault.permissions import IsMerchantOwner
from vault.serializers import MerchantRegistrationSerializer, MerchantPublicSerializer


class MerchantRegisterView(generics.CreateAPIView):
    """POST /api/vault/merchants/register/ — onboards a Direct or Custodial merchant."""
    queryset = Merchant.objects.all()
    serializer_class = MerchantRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        merchant = serializer.save()
        return Response(MerchantPublicSerializer(merchant).data, status=201)


class MyMerchantsListView(generics.ListAPIView):
    """GET /api/vault/merchants/ — merchants owned by the logged-in user only."""
    serializer_class = MerchantPublicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Merchant.objects.filter(owner=self.request.user)


class MerchantDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/vault/merchants/<id>/ — owner-only, credential-safe."""
    queryset = Merchant.objects.all()
    serializer_class = MerchantPublicSerializer
    permission_classes = [permissions.IsAuthenticated, IsMerchantOwner]