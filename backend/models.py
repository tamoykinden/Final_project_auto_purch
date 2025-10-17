from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

    def __str__(self):
        return self.username

class Shop(models.Model):
    name = models.CharField(max_length=100 ,verbose_name='Название магазина')
    url = models.URLField(max_length=500, verbose_name='URL-адрес', null=False, blank=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Список магазинов'
        ordering = ['name']

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Категория')
    shops = models.ManyToManyField(Shop, related_name='categories', verbose_name='Магазины', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', 
                                 on_delete=models.CASCADE, blank=True)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Список продуктов'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ProductInfo(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='product_infos', on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_infos', 
                             on_delete=models.CASCADE, blank=True)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендуемая розничная цена')

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информационный список о продуктах'

    def __str__(self):
        return f'{self.name}: количество: {self.quantity}, цена: {self.price}'

class Parameter(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')

    class Meta:
        verbose_name = 'Название параметра'
        verbose_name_plural = 'Список имен параметров'
        ordering = ('-name')

    def __str__(self):
        return self.name

class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', related_name='product_parametrs', 
                                     on_delete=models.CASCADE, blank=True)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', blank=True,
                                  related_name='product_parametres', on_delete=models.CASCADE)
    value = models.CharField(max_length=100, verbose_name='Значение')

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Список названий параметров'

    def __str__(self):
        return f'{self.parameter} - {self.value}'

class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders',
                             blank=True, on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ['status']

    def __str__(self):
        return f'Заказ от {self.dt}, статус - {self.status}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', 
                              on_delete=models.CASCADE, blank=True)
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='ordered_items', 
                                on_delete=models.CASCADE, blank=True)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='ordered_items',
                             on_delete=models.CASCADE, blank=True)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='contacts',
                             on_delete=models.CASCADE, blank=True)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')
    