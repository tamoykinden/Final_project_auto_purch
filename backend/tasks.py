"""
Celery задачи для приложения backend.

Содержит асинхронные задачи для отправки email и импорта товаров.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def debug_task():
    """
    Тестовая задача для проверки работы Celery.
    
    Return:
        str: Сообщение об успешном выполнении
    """
    return 'Celery работает корректно!'