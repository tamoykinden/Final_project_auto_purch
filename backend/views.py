from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import ProductInfoSerializer, UserRegisterSerializer, UserSerializer, CategorySerializer, ShopSerializer
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.generics import ListAPIView
from .models import Category, ProductInfo, Shop

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

class UserProfileView(APIView):
    """
    API-endpoint просмотра и обновления профиля пользователя.
    
    Методы:
        GET - получение информации о текущем пользователе
        PATCH - частичное обновление профиля пользователя
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получение профиля текущего пользователя

        Args:
            request: HTTP запрос
            
        Returnn:
            Response: JSON с данными пользователя
        """

        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'Status': True, 'Message': 'Профиль обновлен'})
        return Response({
            'Status': False,
            'Errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
class ShopListView(ListAPIView):
    """
    API-endpoint для получения списка активных магазинов

    Отображает только магазины, которые принимают заказы (is_active=True).
    Доступен без аутентификации для просмотра каталога.
    
    Методы:
        GET - получение списка магазинов
    """
    queryset = Shop.objects.filter(is_active=True)
    serializer_class = ShopSerializer
    permission_classes = [AllowAny]


class CategoryListView(ListAPIView):
    """
    API-endpoint для получения списка категорий товаров

    Отображает все категории, доступные в системе.
    Доступен без аутентификации.
    
    Методы:
        GET - получение списка категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class ProductInfoListView(ListAPIView):
    """
    API-endpoint для получения списка товаров с фильтрацией

    Поддерживает фильтрацию по магазину и категории через query parameters
    Отображает только товары, которые есть в наличии (quantity > 0).
    
    Методы:
        GET - получение списка товаров с возможностью фильтрации
    """
    serializer_class = ProductInfoSerializer
    permission_classes = [AllowAny]
