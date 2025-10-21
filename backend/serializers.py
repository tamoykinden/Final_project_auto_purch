from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, Contact

class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User: для отображения информации о пользователе
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'type', 'company', 'position')
        read_only_fields = ('id',)

class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователей. 
    Включает валидацию пароля
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'company', 'position', 'type')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        """
        Проверка совпадения паролей
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('Пароли не совпадают')
        return attrs
    
    def create(self, validated_data):
        """
        Создание пользователя с хешированием пароля
        """
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user
    
class ContactSerializer(serializers.ModelSerializer):
    """
    Сериализатор для контактов пользователя
    """
    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }

class ShopSerializer(serializers.ModelSerializer):
    """
    Сериализатор для магазинов
    """
    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'is_active')
        read_only_fields = ('id',)

class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для категорий
    """
    class Meta:
        model = Category
        fields = ('id', 'name')
        read_only_fields = ('id',)

class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для продуктов
    Включает в себя название категории
    """
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category')
        read_only_fields = ('id',)

class ProductParameterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для параметров продукта.
    """
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')

class ProductInfoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для информации о продукте
    Включает параметры продукта
    """
    product = ProductSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    parameters = ProductParameterSerializer(source='product_parameters', many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'product', 'shop', 'external_id', 'model', 'price', 'price_rrc', 'quantity', 'parameters')
        read_only_fields = ('id',)

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для элементов заказа
    """
    product_info = ProductInfoSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity')
        read_only_fields = ('id',)
        extra_kwargs = {
            'order': {'write_only': True}
        }


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания элементов заказа
    """
    class Meta:
        model = OrderItem
        fields = ('product_info', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для заказов.
    Включает элементы заказа и контактную информацию.
    """
    ordered_items = OrderItemSerializer(many=True, read_only=True)
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'dt', 'status', 'contact', 'ordered_items')
        read_only_fields = ('id',)
