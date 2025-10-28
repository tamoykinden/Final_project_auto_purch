from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem
from backend.utils import load_yaml_from_url
from .tasks import do_import


class SupplierUpdate(APIView):
    """
    API-endpoint для обновления прайс-листа поставщика

    Поставщик может загрузить YAML файл с обновленными данными товаров.
    Доступно только пользователям с типом 'supplier'.
    
    Методы:
        POST - загрузка и обновление прайс-листа
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Обновление прайс-листа поставщика из YAML файла

        Args:
            request: HTTP запрос с URL YAML файла или файлом
            
        Return:
            Response: JSON с результатом операции
        """
        # Проверяется что пользователь - поставщик
        if request.user.type != 'supplier':
            return Response({
                'Status': False,
                'Error': 'Доступно только для поставщиков'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Получается магазин пользователя
        try:
            shop = Shop.objects.get(user=request.user)
        except Shop.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Магазин не найден для данного пользователя'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Обрабатывается загрузка из URL
        url = request.data.get('url')
        if url:
            # Асинхронный импорт через Celery
            task = do_import.delay(shop_id=shop.id, import_url=url)
            
            return Response({
                'Status': True,
                'Message': 'Импорт товаров запущен в фоновом режиме',
                'TaskID': task.id,
                'ShopID': shop.id
            })
        
        return Response({
            'Status': False,
            'Error': 'Не указан URL для загрузки'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def _import_price_data(self, data, shop):
        """
        Внутренний метод для импорта данных прайс-листа

        Args:
            data: Данные из YAML файла
            shop: Магазин поставщика
            
        Return:
            Response: JSON с результатом операции
        """
        try:
            with transaction.atomic():
                # Обработка категории
                for category_data in data['categories']:
                    category, created = Category.objects.get_or_create(
                        id=category_data['id'],
                        defaults={'name': category_data['name']}
                    )
                    category.shops.add(shop)
                    category.save()
                
                # Удаление старыъ товаров магазина
                ProductInfo.objects.filter(shop=shop).delete()
                
                # Обработка товаров
                products_count = 0
                for item in data['goods']:
                    product, created = Product.objects.get_or_create(
                        name=item['name'],
                        category_id=item['category']
                    )
                    
                    product_info = ProductInfo.objects.create(
                        product=product,
                        shop=shop,
                        external_id=item['id'],
                        model=item['model'],
                        price=item['price'],
                        price_rrc=item['price_rrc'],
                        quantity=item['quantity']
                    )
                    
                    # Обработка параметров
                    for name, value in item.get('parameters', {}).items():
                        parameter, created = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(
                            product_info=product_info,
                            parameter=parameter,
                            value=str(value)
                        )
                    
                    products_count += 1
                
                return Response({
                    'Status': True,
                    'Message': f'Прайс-лист обновлен. Обработано товаров: {products_count}'
                })
                
        except KeyError as e:
            return Response({
                'Status': False,
                'Error': f'Отсутствует обязательное поле в данных: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'Status': False,
                'Error': f'Ошибка импорта данных: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class SupplierOrders(APIView):
    """
    API-endpoint для просмотра заказов поставщика

    Показывает заказы, содержащие товары данного поставщика.
    Доступно только пользователям с типом 'supplier'.
    
    Методы:
        GET - получение списка заказов
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получение списка заказов для поставщика

        Args:
            request: HTTP запрос
            
        Return:
            Response: JSON со списком заказов
        """
        # Проверяется что пользователь - поставщик
        if request.user.type != 'supplier':
            return Response({
                'Status': False,
                'Error': 'Доступно только для поставщиков'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Получается магазин пользователя
        try:
            shop = Shop.objects.get(user=request.user)
        except Shop.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Магазин не найден для данного пользователя'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Получаются заказы, содержащие товары данного магазина
        orders = Order.objects.filter(
            ordered_items__product_info__shop=shop
        ).exclude(status='basket').distinct().order_by('-dt')
        
        # Формируются данные для ответа
        orders_data = []
        for order in orders:
            # Получаются только товары данного поставщика в заказе
            supplier_items = OrderItem.objects.filter(
                order=order,
                product_info__shop=shop
            )
            
            # Считается общая сумма товаров поставщика в заказе
            total_amount = sum(
                item.quantity * item.product_info.price 
                for item in supplier_items
            )
            
            order_info = {
                'id': order.id,
                'dt': order.dt,
                'status': order.status,
                'user': order.user.username,
                'total_amount': total_amount,
                'items_count': supplier_items.count(),
                'contact': {
                    'city': order.contact.city if order.contact else None,
                    'phone': order.contact.phone if order.contact else None
                }
            }
            
            orders_data.append(order_info)
        
        return Response(orders_data)
    
# backend_supplier/views.py - ДОБАВИТЬ этот класс

class SupplierOrderDetail(APIView):
    """
    API-endpoint для просмотра деталей заказа поставщика

    Показывает детальную информацию о конкретном заказе.
    Доступно только пользователям с типом 'supplier'.
    
    Методы:
        GET - получение деталей заказа
        PATCH - обновление статуса заказа
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """
        Получение деталей заказа для поставщика

        Args:
            request: HTTP запрос
            order_id: ID заказа
            
        Return:
            Response: JSON с деталями заказа
        """
        # Проверяется что пользователь - поставщик
        if request.user.type != 'supplier':
            return Response({
                'Status': False,
                'Error': 'Доступно только для поставщиков'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            shop = Shop.objects.get(user=request.user)
            order = Order.objects.get(id=order_id)
            
            # Проверяется что заказ содержит товары данного поставщика
            supplier_items = OrderItem.objects.filter(
                order=order,
                product_info__shop=shop
            )
            
            if not supplier_items.exists():
                return Response({
                    'Status': False,
                    'Error': 'Заказ не содержит товаров данного магазина'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Формируется детальная информация
            order_detail = {
                'id': order.id,
                'dt': order.dt,
                'status': order.status,
                'user': {
                    'username': order.user.username,
                    'email': order.user.email,
                    'first_name': order.user.first_name,
                    'last_name': order.user.last_name,
                    'company': order.user.company
                },
                'contact': {
                    'city': order.contact.city,
                    'street': order.contact.street,
                    'house': order.contact.house,
                    'apartment': order.contact.apartment,
                    'phone': order.contact.phone
                } if order.contact else None,
                'items': []
            }
            
            for item in supplier_items:
                item_info = {
                    'id': item.id,
                    'product_name': item.product_info.product.name,
                    'model': item.product_info.model,
                    'quantity': item.quantity,
                    'price': item.product_info.price,
                    'total': item.quantity * item.product_info.price
                }
                
                # Добавляются параметры товара если есть
                parameters = item.product_info.product_parameters.all()
                if parameters.exists():
                    item_info['parameters'] = [
                        {'name': param.parameter.name, 'value': param.value}
                        for param in parameters
                    ]
                
                order_detail['items'].append(item_info)
            
            return Response(order_detail)
            
        except Shop.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Магазин не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except Order.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Заказ не найден'
            }, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, order_id):
        """
        Обновление статуса заказа поставщиком

        Args:
            request: HTTP запрос с новым статусом
            order_id: ID заказа
            
        Return:
            Response: JSON с результатом операции
        """
        # Проверяется что пользователь - поставщик
        if request.user.type != 'supplier':
            return Response({
                'Status': False,
                'Error': 'Доступно только для поставщиков'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            shop = Shop.objects.get(user=request.user)
            order = Order.objects.get(id=order_id)
            
            # Проверяется что заказ содержит товары данного поставщика
            supplier_items = OrderItem.objects.filter(
                order=order,
                product_info__shop=shop
            )
            
            if not supplier_items.exists():
                return Response({
                    'Status': False,
                    'Error': 'Заказ не содержит товаров данного магазина'
                }, status=status.HTTP_404_NOT_FOUND)
            
            new_status = request.data.get('status')
            if new_status and new_status in dict(Order.STATE_CHOISES):
                order.status = new_status
                order.save()
                
                return Response({
                    'Status': True,
                    'Message': f'Статус заказа обновлен на: {new_status}'
                })
            else:
                return Response({
                    'Status': False,
                    'Error': 'Неверный статус'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Shop.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Магазин не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        except Order.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Заказ не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
# backend_supplier/views.py - ДОБАВИТЬ этот класс

class SupplierState(APIView):
    """
    API-endpoint для управления состоянием магазина

    Позволяет поставщику включать/выключать прием заказов.
    Доступно только пользователям с типом 'supplier'.
    
    Методы:
        GET - получение текущего состояния
        PATCH - обновление состояния
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получение текущего состояния магазина

        Args:
            request: HTTP запрос
            
        Return:
            Response: JSON с состоянием магазина
        """
        # Проверяется что пользователь - поставщик
        if request.user.type != 'supplier':
            return Response({
                'Status': False,
                'Error': 'Доступно только для поставщиков'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            shop = Shop.objects.get(user=request.user)
            
            # Считается количество активных товаров
            active_products_count = ProductInfo.objects.filter(
                shop=shop, 
                quantity__gt=0
            ).count()
            
            # Считается количество заказов в работе
            active_orders_count = Order.objects.filter(
                ordered_items__product_info__shop=shop
            ).exclude(status__in=['basket', 'delivered', 'canceled']).distinct().count()
            
            return Response({
                'Status': True,
                'shop_name': shop.name,
                'is_active': shop.is_active,
                'statistics': {
                    'active_products': active_products_count,
                    'active_orders': active_orders_count,
                    'total_products': ProductInfo.objects.filter(shop=shop).count()
                }
            })
        except Shop.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Магазин не найден'
            }, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        """
        Обновление состояния магазина

        Args:
            request: HTTP запрос с новым состоянием
            
        Return:
            Response: JSON с результатом операции
        """
        # Проверяется что пользователь - поставщик
        if request.user.type != 'supplier':
            return Response({
                'Status': False,
                'Error': 'Доступно только для поставщиков'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            shop = Shop.objects.get(user=request.user)
            is_active = request.data.get('is_active')
            
            if is_active is not None:
                shop.is_active = is_active
                shop.save()
                
                state = 'включен' if is_active else 'выключен'
                return Response({
                    'Status': True,
                    'Message': f'Прием заказов {state}'
                })
            else:
                return Response({
                    'Status': False,
                    'Error': 'Не указан параметр is_active'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Shop.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Магазин не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
class SupplierImportView(APIView):
    """
    API-endpoint для запуска импорта товаров поставщика через админку
    
    Позволяет администраторам запускать импорт для любого поставщика.
    Требует прав администратора.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Запуск импорта товаров для поставщика через админку
        
        Args:
            request: HTTP запрос с данными импорта
            
        Return:
            Response: JSON с результатом операции
        """
        # Проверяются права администратора
        if not request.user.is_staff:
            return Response({
                'Status': False,
                'Error': 'Доступно только для администраторов'
            }, status=status.HTTP_403_FORBIDDEN)
        
        shop_id = request.data.get('shop_id')
        import_url = request.data.get('import_url')
        
        if not shop_id or not import_url:
            return Response({
                'Status': False,
                'Error': 'Не указаны shop_id или import_url'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            shop = Shop.objects.get(id=shop_id)
            
            # Асинхронный импорт через Celery
            task = do_import.delay(shop_id=shop.id, import_url=import_url)
            
            return Response({
                'Status': True,
                'Message': f'Импорт товаров для магазина "{shop.name}" запущен',
                'TaskID': task.id,
                'ShopID': shop.id,
                'ShopName': shop.name
            })
            
        except Shop.DoesNotExist:
            return Response({
                'Status': False,
                'Error': 'Магазин не найден'
            }, status=status.HTTP_404_NOT_FOUND)
