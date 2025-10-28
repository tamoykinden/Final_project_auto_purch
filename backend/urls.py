from django.urls import path
from . import views

urlpatterns = [
    # Аутентификация и пользователи
    path('user/register/', views.RegisterView.as_view(), name='user-register'),
    path('user/login/', views.LoginView.as_view(), name='user-login'),
    path('user/profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Каталог товаров
    path('shops/', views.ShopListView.as_view(), name='shop-list'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('products/', views.ProductInfoListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Контактные данные
    path('user/contacts/', views.ContactView.as_view(), name='contact-list'),
    
    # Корзина и заказы
    path('basket/', views.BasketView.as_view(), name='basket'),
    path('orders/', views.OrderView.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/status/', views.OrderStatusView.as_view(), name='order-status'),
    path('orders/<int:order_id>/confirm/', views.OrderConfirmView.as_view(), name='order-confirm'),
]
