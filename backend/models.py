from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Модель пользователей
    """
    USER_TYPE_CHOICES = (
        ('buyer', 'Покупатель'),
        ('supplier', 'Поставщик'),
    )
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, 
                          max_length=10, default='buyer')
    company = models.CharField(verbose_name='Компания', max_length=100, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=100, blank=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Список пользователей'
        ordering = ('email',)

    def __str__(self):
        return f'{self.first_name} {self.last_name}' if self.first_name else self.username

class Shop(models.Model):
    """
    Модель магазинов
    """
    name = models.CharField(max_length=100 ,verbose_name='Название магазина')
    url = models.URLField(max_length=500, verbose_name='URL-адрес', null=False, blank=True)
    user = models.OneToOneField(User, verbose_name='Владелец', blank=True, 
                                null=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(verbose_name='Статус получения заказов', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Список магазинов'
        ordering = ['-name']

    def __str__(self):
        return self.name

class Category(models.Model):
    """
    Модель категорий
    """
    name = models.CharField(max_length=100, verbose_name='Категория')
    shops = models.ManyToManyField(Shop, related_name='categories', verbose_name='Магазины', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Список категорий'
        ordering = ['-name']

    def __str__(self):
        return self.name

class Product(models.Model):
    """
    Модель товаров (продуктов)
    """
    name = models.CharField(max_length=200, verbose_name='Название товара')
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', 
                                 on_delete=models.CASCADE, blank=True)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Список продуктов'
        ordering = ['-name']
    
    def __str__(self):
        return self.name

class ProductInfo(models.Model):
    """
    Модель информации о продукте
    """
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='product_infos', on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_infos', 
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(verbose_name='Цена', decimal_places=2, max_digits=10)
    price_rrc = models.DecimalField(verbose_name='Рекомендуемая розничная цена', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информационный список о продуктах'
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop'], name='unique_product_info')
        ]

    def __str__(self):
        return f'{self.product.name}: количество: {self.quantity}, цена: {self.price}'

class Parameter(models.Model):
    """
    Модель параметра
    """
    name = models.CharField(max_length=100, verbose_name='Название параметра')

    class Meta:
        verbose_name = 'Название параметра'
        verbose_name_plural = 'Список имен параметров'
        ordering = ('-name',)

    def __str__(self):
        return self.name

class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', related_name='product_parameters', 
                                     on_delete=models.CASCADE, blank=True)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', blank=True,
                                  related_name='product_parameters', on_delete=models.CASCADE)
    value = models.CharField(max_length=100, verbose_name='Значение')

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Список параметров'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter')
        ]

    def __str__(self):
        return f'{self.parameter} - {self.value}'
    
class Contact(models.Model):
    """
    Модель контактов
    """
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='contacts',
                             on_delete=models.CASCADE, blank=True)
    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.CharField(max_length=200, verbose_name='Улица')
    house = models.CharField(max_length=100, verbose_name='Дом')
    structure = models.CharField(max_length=10, verbose_name='Корпус', blank=True)
    building = models.CharField(max_length=10, verbose_name='Строение', blank=True)
    apartment = models.CharField(max_length=10, verbose_name='Квартира')
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')

    class Meta:
        verbose_name = 'Контакты пользователей'
        verbose_name_plural = 'Список контактов пользователей'

    def __str__(self):
        return f'{self.city}, {self.street}, {self.house}, {self.apartment}'

class Order(models.Model):
    """
    Модель заказов
    """

    STATE_CHOISES = (
        ('basket', 'Статус корзины'),
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('assembled', 'Собран'),
        ('sent', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменен'),
    )

    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    status = models.CharField(max_length=20, verbose_name='Статус заказа', choices=STATE_CHOISES)
    contact = models.ForeignKey(Contact, verbose_name='Контакты', blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ['status', '-dt']

    def __str__(self):
        return f'Заказ от {self.dt}, статус - {self.status}'

class OrderItem(models.Model):
    """
    Модель заказанных позиций
    """
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', 
                              on_delete=models.CASCADE, blank=True)
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', 
                                     related_name='ordered_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = 'Список заказанных позиций'
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product_info'], name='unique_order_item')
        ]

    def __str__(self):
        return f'Позиция заказа {self.order.id}: {self.product_info.product.name}'
    
