from django.core.management.base import BaseCommand
from django.db import transaction
from backend.models import Shop, Category, Parameter, Product, ProductInfo, ProductParameter
from backend.utils import load_yaml_from_file, load_yaml_from_url

class Command(BaseCommand):
    """
    Management commands для импорта товаров
    Описание: наследуется от класса BaseCommand - базового класса для всех команд усправления Django.
    Предоставляет интерфейс для работы с командной строкой
    """

    help = 'Импорт товаров из YAML-файла или URL'

    def add_arguments(self, parser):
        """
        Функция для определения аргументов командной строки для это команды
        
        Аргументы:
            - parser - ArgumentParser объект для добавления аргументов
        """
        parser.add_argument(
            '--file', # название аргумента
            type=str, #Тип значения
            help='Путь к YAML-файлу с данными для импорта' # текст справки
            )
        parser.add_argument(
            '--url',
            type=str,
            help='URL-адрес YAML-файла для загрузки'
        )
        parser.add_argument(
            '--shop',
            type=str,
            required=True, # Обязательный аргумент
            help='Название магазина, для которого импортирутся товары'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID пользователя-владельца магазина'
        )
    
    def handle(self, *args, **options):
        """
        Основной метод, который выполняется при запуске команды

        Аргументы:
            - *args - позиционные аргументы
            - **options - именованные аргументы командной строки

        Процесс:
            1. Получает аргументы из командной строки.
            2. Загружает данные из YAML (файл или URL).
            3. Вызывает метод импорта данных.
            4. Обрабатывает результаты и выводит
        """

        # Получение значений аргументов
        file_path = options.get('file')
        url = options.get('url')
        shop_name = options.get('shop')
        user_id = options.get('user_id')

        try:
            if file_path: # Проверка источника жанных
                self.stdout.write(f'Загрузка данных из файла: {file_path}') # Загрузка данных из файла
                data = load_yaml_from_file(file_path)
            
            elif url: # Из URL
                self.stdout.write(f'Загрузка данных из URL: {url}')
                data = load_yaml_from_url(url)
            else: #Вывести ошибку
                self.stderr.write(self.style.ERROR('Ошибка, необходимо указать --file или --url'))
                return
            
            self.stdout.write(f'Начало импорта для магазина: {shop_name}')

            success, message = self.import_data(data, shop_name, user_id) # Вызов основного метода импорта

            if success:
                self.stdout.write(self.style.SUCCESS(message)) #Если импорт успешен - зеленое сообщение
            else:
                self.stderr.write(self.style.ERROR(message)) #Если ошибка - красное

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Файл не найден: {file_path}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Другая ошибка: {str(e)}'))

    @transaction.atomic
    def import_data(self, data, shop_name, user_id):
        """
        Основная логика импорта данных

        Используется транзакция: либо все операции выполняются упешно, либо все изменения откатываются при ошибке

        Аргументы:
            - data (dict): Данные из YAML-файла
            - shop_name (str): Название магазина
            - user_id (int): ID пользователя владельца

        Возвращает: tuple (success: bool, message: str)

        Процесс:
        1. Создание/получение магазина.
        2. Обработка категорий.
        3. Удаление старых товаров магазина.
        4. Обработка товаров и их параметров
        """

        try:
            # Работа с магазином

            shop, created = Shop.objects.get_or_create(name=shop_name, 
                                                       defaults={'user_id': user_id} if user_id else {})
            if created:
                self.stdout.write(f'Создан новый магазин: {shop_name}')
            else:
                self.stdout.write(f'Найден существующий магазин: {shop_name}')

            # Обработка категорий
            for category_data in data['categories']: # Проходим по всем категориям из YAML
                category, cat_created = Category.objects.get_or_create( #Создаю или получаю категорию по ID
                    id=category_data['id'], # ID из YAML
                    defaults={'name': category_data['name']}
                )

                # Связываем категорию с магазином
                category.shops.add(shop)
                category.save()

                if cat_created:
                    self.stdout.write(f'Создана категори: {category.name}')

            # Очистка старых данных
            # Удаляем все существующие товары этого магазина, чтобы обнвоить весь ассортимент
            deleted_count = ProductInfo.objects.filter(shop_id=shop.id).delete()[0]
            self.stdout.write(f'Удалено старых товаров: {deleted_count}')

            #Обработка товаров

            #Счетчики для статистики
            products_created = 0
            parameters_created = 0

            for item in data['goods']:
                # Создание или получение основного продукта
                product, prod_created = Product.objects.get_or_create(
                    name=item['name'],
                    category_id=item['category'] # связыаем с категорией
                )
                if prod_created:
                    products_created += 1

                # ProductInfo - конкретное предложение товара в конкретном магазине. Здесь хранится цена, количество...
                product_info = ProductInfo.objects.create(
                    product_id=product.id, #ссылка на основной продукт
                    shop_id=shop.id, #ссылка на магазин
                    external_id=item['id'], # ID из внешней системы
                    model=item['model'], #Модель товара
                    price=item['price'], # Цена
                    price_rrc=item['price_rrc'], #Рекомендованная цена
                    quantity=item['quantity'] # Количество на складе
                )

                # Проходим по всем характеристикам товара
                for param_name, param_value in item['parameters'].items():
                    # Создаем или получаем параметр по названию
                    parameter_object, _ = Parameter.objects.get_or_create(name=param_name)

                    #Создаем связь параметра с товаром
                    ProductParameter.objects.create(
                        product_info_id=product_info.id,
                        parameter_id=parameter_object.id,
                        value=str(param_value)
                    )

                    parameters_created += 1

            self.stdout.write(f'Создано новых продуктов: {products_created}')
            self.stdout.write(f'Создано параметров: {parameters_created}')
            self.stdout.write(f"Обработано товаров: {len(data['goods'])}")

            return True, f'Успешно импортировано для магазина {shop_name}'
        except KeyError as e:
            #Ошибка если в данных отсутствует обязательное поле
            return False, f'Отсутствует обязательное поле в данных: {str(e)}'
        except Exception as e:
            return False, f"Ошибка импорта: {str(e)}"
