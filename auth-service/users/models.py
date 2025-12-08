from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model where email is the unique identifier
    instead of username.
    """
    # Remove the username field
    username = None

    # Make email unique and required
    email = models.EmailField(_('email address'), unique=True)

    # Add extra fields if needed (e.g., plan type, bio)
    is_verified = models.BooleanField(default=False)

    # Set email as the username field for authentication
    USERNAME_FIELD = 'email'

    # Fields required when creating a superuser (besides email and password)
    REQUIRED_FIELDS = []

    # Use the custom manager (optional, but good practice if we customize creation logic later)
    # objects = CustomUserManager()

    def __str__(self):
        return self.email