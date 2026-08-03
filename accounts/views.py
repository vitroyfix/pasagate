from rest_framework import generics, permissions
from accounts.serializers import RegisterSerializer, UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — creates a dashboard login account."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]  # anyone can sign up


class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ — returns the currently logged-in user."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# Login itself doesn't need a custom view — simplejwt's built-in
# TokenObtainPairView already does exactly what we need (checks
# username+password, returns access+refresh tokens). We wire it
# directly in urls.py below instead of reimplementing it here.