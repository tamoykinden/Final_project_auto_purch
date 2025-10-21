from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import UserRegisterSerializer
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth import authenticate

class RegisterView(APIView):
    """
    API-endpoint регистрации новых пользователей.
    
    Поддерживает регистрацию как покупателей, так и поставщиков.
    При успешной регистрации автоматические создается токен аутентификации.

    Методы:
        - POST - создание нового пользователя с валидацией данных
    """
    permission_classes = [AllowAny] # Класс разрешения с неограниченным доступом

    def post(self, request):
        """
        Регистрация нового пользователя в системе

        Args:
            - request: HTTP-запрос с данными для регистрации
        
        Return:
            - Response: JSON-объект с результатом операции и токеноом аутентификации
        """

        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid:
            user = serializer.save() # Сохраняем пользователя в БД, если прошла валидация
            token, created = Token.objects.get_or_create(user=user) # Создается токен

            return Response({
                'Status': True,
                'Message': 'Пользователь успешно зарегистрирован',
                'Token': token.key
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'Status': False,
            'Errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    API-endpoint для аутентификациия пользователя.

    Проверяет учетные данные и возвращает токен доступа.

    Методы:
        - POST - аутентификация пользователя по email и паролю
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Аутентификация пользователя в системе.

        Args:
            - request: HTTP-запрос с учетными данными

        Return:
            - Response: JSON с результатом аутентификации и токеном
        """
        # Получаем имя пользователя и пароль
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password) # Если аутенцифицирует - возвращает User, в обратном - None

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'Status': True,
                'Token': token.key
            })
        
        return Response({
            'Status': False,
            'Error': 'Неверные учетные данные'
        }, status=status.HTTP_401_UNAUTHORIZED)
