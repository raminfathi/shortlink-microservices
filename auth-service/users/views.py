from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import UserRegistrationSerializer
from django.contrib.auth import get_user_model
from .tasks import send_welcome_email
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    Accessible by anyone (AllowAny).
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        """
        Overriding perform_create to add custom logic after save.
        """
        # 2. Save the user to the database
        user = serializer.save()

        # 3. Trigger the background task
        # We use .delay() to send it to Celery (Redis) immediately.
        # This will NOT block the HTTP response.
        send_welcome_email.delay(user.email)