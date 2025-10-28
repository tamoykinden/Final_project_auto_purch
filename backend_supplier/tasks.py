from celery import shared_task
from django.db import transaction
from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter
from backend.utils import load_yaml_from_url

@shared_task(bind=True, max_retries=3, time_limit=300)
def do_import(self, shop_id, import_url):
    """
    Асинхронная задача для импорта товаров поставщика.
    
    Args:
        shop_id: ID магазина поставщика
        import_url: URL YAML файла с данными товаров
        
    Return:
        dict: Результат импорта товаров
    """
    try:
        # Загрузка данных из YAML
        data = load_yaml_from_url(import_url)
        
        with transaction.atomic():
            shop = Shop.objects.get(id=shop_id)
            
            # Обработка категорий
            categories_processed = 0
            for category_data in data['categories']:
                category, created = Category.objects.get_or_create(
                    id=category_data['id'],
                    defaults={'name': category_data['name']}
                )
                category.shops.add(shop)
                category.save()
                categories_processed += 1
            
            # Удаление старых товаров магазина
            deleted_count = ProductInfo.objects.filter(shop=shop).delete()[0]
            
            # Обработка товаров
            products_processed = 0
            parameters_processed = 0
            
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
                    parameters_processed += 1
                
                products_processed += 1
            
            return {
                'status': 'success',
                'message': 'Импорт товаров завершен',
                'statistics': {
                    'categories_processed': categories_processed,
                    'products_processed': products_processed,
                    'parameters_processed': parameters_processed,
                    'old_products_deleted': deleted_count,
                    'shop_id': shop_id,
                    'shop_name': shop.name
                }
            }
    
    except Exception as e:
        # Повторная попытка через 120 секунд
        raise self.retry(exc=e, countdown=120)
    