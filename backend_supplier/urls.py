from django.urls import path
from . import views

urlpatterns = [
    # Обновление прайс-листа
    path('update/', views.SupplierUpdate.as_view(), name='supplier-update'),
    
    # Просмотр заказов
    path('orders/', views.SupplierOrders.as_view(), name='supplier-orders'),
    path('orders/<int:order_id>/', views.SupplierOrderDetail.as_view(), name='supplier-order-detail'),
    
    # Управление состоянием магазина
    path('state/', views.SupplierState.as_view(), name='supplier-state'),
    
    path('admin/import/', views.SupplierImportView.as_view(), name='supplier-admin-import'),
]