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

class UserRegisterSerializers(serializers.ModelSerializer):
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