from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.middleware.csrf import get_token
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import InvalidCredentials
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer, UserRoleUpdateSerializer

from apps.common.permissions import IsAdmin
from .models import User


class RegisterView(APIView):
    """US1-1"""

    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: UserSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        get_token(request)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """US1-2"""

    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: UserSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"].strip().lower(),
            password=serializer.validated_data["password"],
        )
        if user is None:
            raise InvalidCredentials("Invalid email or password.")
        django_login(request, user)
        get_token(request)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """US1-3"""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        django_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """US1-2, US1-3"""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user).data)

class UserManagementView(APIView):
    """US8-1, US8-2"""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        users = User.objects.all().order_by("email")
        return Response(UserSerializer(users, many=True).data)

    def patch(self, request, user_id):
        target = get_object_or_404(User, id=user_id)
        if target.id == request.user.id and request.data.get("is_admin") is False:
            return Response(
                {"detail": "You cannot remove your own admin role."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserRoleUpdateSerializer(target, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(target).data, status=status.HTTP_200_OK)
