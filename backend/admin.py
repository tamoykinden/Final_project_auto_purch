from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order, OrderItem

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Админка для модели User
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'type', 'company', 'is_staff')
    list_filter = ('type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('type', 'company', 'position')
        }),
    )

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    """
    Админка для модели Shop
    """
    list_display = ('name', 'url', 'user', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'user__username')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Админка для модели Category
    """
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('shops',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Админка для модели Product
    """
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

class ProductParameterInline(admin.TabularInline):
    """
    Inline для параметров продукта в админке ProductInfo
    """
    model = ProductParameter
    extra = 1

@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    """
    Админка для модели ProductInfo
    """
    list_display = ('product', 'shop', 'price', 'quantity', 'price_rrc')
    list_filter = ('shop',)
    search_fields = ('product__name', 'shop__name')
    inlines = [ProductParameterInline]

@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    """
    Админка для модели Parameter
    """
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    """
    Админка для модели ProductParameter
    """
    list_display = ('product_info', 'parameter', 'value')
    list_filter = ('parameter',)
    search_fields = ('product_info__product__name', 'parameter__name')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """
    Админка для модели Contact
    """
    list_display = ('user', 'city', 'street', 'house', 'phone')
    list_filter = ('city',)
    search_fields = ('user__username', 'city', 'street', 'phone')

class OrderItemInline(admin.TabularInline):
    """
    Inline для элементов заказа в админке Order
    """
    model = OrderItem
    extra = 0
    readonly_fields = ('product_info', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Админка для модели Order
    """
    list_display = ('id', 'user', 'dt', 'status', 'contact')
    list_filter = ('status', 'dt')
    search_fields = ('user__username', 'contact__city')
    readonly_fields = ('dt',)
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Админка для модели OrderItem
    """
    list_display = ('order', 'product_info', 'quantity')
    list_filter = ('order__status',)
    search_fields = ('order__user__username', 'product_info__product__name')
