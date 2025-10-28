import os
from celery import Celery

# Устанавливает переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'final_work_auto_purch.settings')

# Создает экземпляр Celery приложения
app = Celery('final_work_auto_purch')

# Загружает настройки из Django settings с префиксом 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживает задачи в файлах tasks.py приложений
app.autodiscover_tasks()