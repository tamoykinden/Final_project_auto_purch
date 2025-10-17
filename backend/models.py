from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

    def __str__(self):
        return self.username

class Shop(models.Model):
    name = models.CharField(max_length=100 ,verbose_name='Название магазина')
    url = models.URLField(max_length=500, verbose_name='URL-адрес')

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Список магазинов'
        ordering = ['name']

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Категория')
    shops = models.ManyToManyField(Shop, related_name='categories', verbose_name='Магазины')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Список продуктов'
        ordering = ['name']

class ProductInfo(models.Model):
    pass

class Parameter(models.Model):
    pass

class ProductParameter(models.Model):
    pass

class Order(models.Model):
    pass

class OrderItem(models.Model):
    pass

class Contact(models.Model):
    pass