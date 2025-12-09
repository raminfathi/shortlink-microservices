import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


# This fixture gives us access to the database for this class
@pytest.mark.django_db
class TestAuthentication:

    def setup_method(self):
        """
        Setup run before each test method.
        We initialize the APIClient here to simulate requests.
        """
        self.client = APIClient()
        # Get URLs by their names (defined in users/urls.py)
        self.register_url = reverse('auth_register')
        self.login_url = reverse('token_obtain_pair')

        # Default user data for testing
        self.user_data = {
            "email": "test@example.com",
            "password": "strongpassword123",
            "first_name": "Test",
            "last_name": "User"
        }

    def test_registration_success(self):
        """
        Test that a user can successfully register with valid data.
        """
        # Send POST request to register endpoint
        response = self.client.post(self.register_url, self.user_data)

        # Check status code is 201 Created
        assert response.status_code == status.HTTP_201_CREATED

        # Verify user is actually created in the database
        assert User.objects.count() == 1
        assert User.objects.get().email == "test@example.com"

    def test_registration_duplicate_email(self):
        """
        Test that registering with an existing email fails (Unique Constraint).
        """
        # 1. Create a user first
        self.client.post(self.register_url, self.user_data)

        # 2. Try to create another user with the SAME email
        response = self.client.post(self.register_url, self.user_data)

        # Should fail with 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self):
        """
        Test that a registered user can login and receive JWT tokens.
        """
        # 1. Create user manually (bypassing API to test login in isolation)
        User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )

        # 2. Attempt login
        login_data = {
            "email": self.user_data['email'],
            "password": self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data)

        # Check success
        assert response.status_code == status.HTTP_200_OK

        # Verify JWT tokens are present in response
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_credentials(self):
        """
        Test login with wrong password fails.
        """
        # 1. Create user
        User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )

        # 2. Attempt login with WRONG password
        login_data = {
            "email": self.user_data['email'],
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, login_data)

        # Check unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED