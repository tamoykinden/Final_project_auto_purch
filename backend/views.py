from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    ProductInfoSerializer, UserRegisterSerializer, UserSerializer, 
    CategorySerializer, ShopSerializer, ContactSerializer, OrderSerializer,
    OrderItemCreateSerializer
)
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from .models import Category, ProductInfo, Shop, Contact, Order, OrderItem, Product
from .tasks import send_order_confirmation_email
from celery.result import AsyncResult



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

        if serializer.is_valid():  # ⭐ ИСПРАВИТЬ: добавить скобки ()
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
        """
        Частичное обновление профиля пользователя

        Args:
            request: HTTP запрос с данными для обновления
            
        Return:
            Response: JSON с результатом операции
        """
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

    def get_queryset(self):
        """
        Фильтрация товаров по магазину и категории

        Return:
            QuerySet: Отфильтрованный список товаров
        """
        queryset = ProductInfo.objects.filter(quantity__gt=0)  # Только товары в наличии
        
        # Фильтрация по магазину
        shop_id = self.request.query_params.get('shop_id')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        
        # Фильтрация по категории
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        
        return queryset

class ProductDetailView(RetrieveAPIView):
    """
    API-endpoint для получения детальной информации о конкретном товаре

    Отображает полную информацию о товаре включая характеристики и параметры.
    Доступен без аутентификации.
    
    Методы:
        GET - получение детальной информации о товаре
    """
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer
    permission_classes = [AllowAny]

class ContactView(APIView):
    """
    API-endpoint для управления контактными данными пользователя

    Позволяет добавлять, просматривать и удалять адреса доставки.
    
    Методы:
        GET - получение списка контактов пользователя
        POST - добавление нового контакта
        DELETE - удаление контакта
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получение списка контактов текущего пользователя

        Args:
            request: HTTP запрос
            
        Return:
            Response: JSON со списком контактов
        """
        contacts = Contact.objects.filter(user=request.user)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Добавление нового контакта для пользователя

        Args:
            request: HTTP запрос с данными контакта
            
        Return:
            Response: JSON с результатом операции
        """
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                'Status': True,
                'Message': 'Контакт добавлен'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'Status': False,
            'Errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        Удаление контакта пользователя

        Args:
            request: HTTP запрос с ID контакта для удаления
            
        Return:
            Response: JSON с результатом операции
        """
        contact_id = request.data.get('id')
        if contact_id:
            try:
                contact = Contact.objects.get(id=contact_id, user=request.user)
                contact.delete()
                return Response({'Status': True, 'Message': 'Контакт удален'})
            except Contact.DoesNotExist:
                return Response({
                    'Status': False,
                    'Error': 'Контакт не найден'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'Status': False,
            'Error': 'Не указан ID контакта'
        }, status=status.HTTP_400_BAD_REQUEST)

class BasketView(APIView):
    """
    API-endpoint для работы с корзиной покупок

    Предоставляет полный функционал для управления корзиной:
    - Просмотр содержимого
    - Добавление товаров
    - Изменение количества
    - Удаление товаров
    
    Методы:
        GET - получение содержимого корзины
        POST - добавление товара в корзину
        PATCH - изменение количества товаров в корзине
        DELETE - удаление товаров из корзины
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получение текущего состояния корзины пользователя

        Args:
            request: HTTP запрос
            
        Return:
            Response: JSON с содержимым корзины или сообщением о пустой корзине
        """
        basket = Order.objects.filter(user=request.user, status='basket').first()
        if basket:
            serializer = OrderSerializer(basket)
            return Response(serializer.data)
        return Response({'Status': True, 'Message': 'Корзина пуста'})

    def post(self, request):
        """
        Добавление товара в корзину пользователя

        Если товар уже есть в корзине - увеличивает его количество.
        
        Args:
            request: HTTP запрос с данными товара
            
        Return:
            Response: JSON с результатом операции
        """
        serializer = OrderItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Получаем или создаем корзину пользователя
            basket, created = Order.objects.get_or_create(
                user=request.user, 
                status='basket',
                defaults={'contact': None}
            )
            
            # Проверяем не добавлен ли уже товар
            product_info = serializer.validated_data['product_info']
            quantity = serializer.validated_data['quantity']
            
            order_item, created = OrderItem.objects.get_or_create(
                order=basket,
                product_info=product_info,
                defaults={'quantity': quantity}
            )
            
            if not created:
                order_item.quantity += quantity
                order_item.save()
            
            return Response({
                'Status': True,
                'Message': 'Товар добавлен в корзину'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'Status': False,
            'Errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """
        Изменение количества товаров в корзине

        Args:
            request: HTTP запрос с данными для обновления
            
        Return:
            Response: JSON с результатом операции
        """
        items = request.data.get('items')
        if items:
            basket = Order.objects.filter(user=request.user, status='basket').first()
            if basket:
                for item in items:
                    try:
                        order_item = OrderItem.objects.get(
                            id=item['id'],
                            order=basket
                        )
                        order_item.quantity = item['quantity']
                        order_item.save()
                    except OrderItem.DoesNotExist:
                        continue
                
                return Response({'Status': True, 'Message': 'Корзина обновлена'})
        
        return Response({
            'Status': False,
            'Error': 'Не указаны товары для обновления'
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        Удаление товаров из корзины

        Args:
            request: HTTP запрос со списком ID товаров для удаления
            
        Return:
            Response: JSON с результатом операции
        """
        items = request.data.get('items')
        if items:
            basket = Order.objects.filter(user=request.user, status='basket').first()
            if basket:
                OrderItem.objects.filter(order=basket, id__in=items).delete()
                return Response({'Status': True, 'Message': 'Товары удалены из корзины'})
        
        return Response({
            'Status': False,
            'Error': 'Не указаны товары для удаления'
        }, status=status.HTTP_400_BAD_REQUEST)

class OrderView(APIView):
    """
    API-endpoint для работы с заказами пользователя

    Предоставляет функционал для:
    - Просмотра истории заказов
    - Оформления новых заказов из корзины
    
    Методы:
        GET - получение списка заказов пользователя (история)
        POST - оформление нового заказа из корзины
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получение истории заказов пользователя

        Не включает заказы со статусом 'basket' (корзина).
        
        Args:
            request: HTTP запрос
            
        Return:
            Response: JSON со списком заказов пользователя
        """
        orders = Order.objects.filter(user=request.user).exclude(status='basket')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Оформление заказа из корзины пользователя

        Требует указания контакта для доставки. Переводит заказ из статуса
        'basket' в статус 'new'.
        
        Args:
            request: HTTP запрос с ID контакта для доставки
            
        Return:
            Response: JSON с результатом операции и ID созданного заказа
        """
        contact_id = request.data.get('contact_id')
        if not contact_id:
            return Response({
                'Status': False,
                'Error': 'Не указан контакт для доставки'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Получаем корзину пользователя
                basket = Order.objects.filter(user=request.user, status='basket').first()
                if not basket or not basket.ordered_items.exists():
                    return Response({
                        'Status': False,
                        'Error': 'Корзина пуста'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Проверяем контакт
                contact = Contact.objects.get(id=contact_id, user=request.user)
                
                # Обновляем заказ
                basket.contact = contact
                basket.status = 'new'
                basket.save()
                
                return Response({
                    'Status': True,
                    'Message': 'Заказ оформлен',
                    'OrderID': basket.id
                })
                
        except Contact.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Контакт не найден'
            }, status=status.HTTP_404_NOT_FOUND)

class OrderDetailView(RetrieveAPIView):
    """
    API-endpoint для получения детальной информации о конкретном заказе

    Позволяет пользователю просматривать детали своих заказов.
    
    Методы:
        GET - получение детальной информации о заказе
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        """
        Ограничение доступа только к заказам текущего пользователя

        Return:
            QuerySet: Заказы текущего пользователя
        """
        return Order.objects.filter(user=self.request.user)

class OrderStatusView(APIView):
    """
    API-endpoint для изменения статуса заказа пользователем

    Позволяет пользователю обновлять статус своих заказов в пределах
    разрешенных переходов между статусами.
    
    Методы:
        PATCH - обновление статуса заказа
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        """
        Обновление статуса заказа

        Args:
            request: HTTP запрос с новым статусом
            order_id: ID заказа для обновления
            
        Return:
            Response: JSON с результатом операции
        """
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            new_status = request.data.get('status')
            
            # Проверяем валидность нового статуса
            if new_status in dict(Order.STATE_CHOISES):
                order.status = new_status
                order.save()
                return Response({'Status': True, 'Message': 'Статус обновлен'})
            else:
                return Response({
                    'Status': False,
                    'Error': 'Неверный статус'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Order.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Заказ не найден'
            }, status=status.HTTP_404_NOT_FOUND)

class OrderConfirmView(APIView):
    """
    API-endpoint для подтверждения заказа и отправки email уведомления

    Выполняет финальное подтверждение заказа и отправляет email
    с подтверждением на адрес пользователя.
    
    Методы:
        POST - подтверждение заказа и отправка email
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        """
        Подтверждение заказа и отправка email уведомления

        Args:
            request: HTTP запрос
            order_id: ID заказа для подтверждения
            
        Return:
            Response: JSON с результатом операции
        """
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            
            # Асинхронная отправка email через Celery
            task = send_order_confirmation_email.delay(
                order_id=order.id,
                user_email=request.user.email,
                user_name=request.user.get_full_name() or request.user.username
            )
            
            return Response({
                'Status': True,
                'Message': 'Заказ подтвержден, email отправляется',
                'TaskID': task.id  # ID задачи для отслеживания
            })
            
        except Order.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Заказ не найден'
            }, status=status.HTTP_404_NOT_FOUND)

class TaskStatusView(APIView):
    """
    API-endpoint для проверки статуса Celery задач
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        """
        Получение статуса задачи
        
        Args:
            request: HTTP запрос
            task_id: ID Celery задачи
            
        Return:
            Response: JSON со статусом задачи
        """
        
        task_result = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'status': task_result.status,
            'ready': task_result.ready()
        }
        
        if task_result.ready():
            if task_result.successful():
                response_data['result'] = task_result.result
            else:
                response_data['error'] = str(task_result.result)
        
        return Response(response_data)