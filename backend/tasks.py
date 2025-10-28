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

@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id, user_email, user_name):
    """
    Асинхронная задача для отправки email подтверждения заказа.
    
    Args:
        order_id: ID заказа
        user_email: Email пользователя
        user_name: Имя пользователя
        
    Return:
        dict: Результат отправки email
    """
    try:
        subject = f'Подтверждение заказа #{order_id}'
        message = f'''
Уважаемый(ая) {user_name}!

Ваш заказ #{order_id} подтвержден. Спасибо за покупку!

Мы уведомим вас о статусе заказа.

С уважением,
Команда магазина
        '''
        
        # Отправка email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        
        return {
            'status': 'success',
            'message': f'Email отправлен на {user_email}',
            'order_id': order_id
        }
        
    except Exception as e:
        # Повторная попытка через 60 секунд
        raise self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def send_email(self, subject, message, recipient_list, from_email=None):
    """
    Универсальная задача для отправки email.
    
    Args:
        subject: Тема письма
        message: Текст письма
        recipient_list: Список получателей
        from_email: Email отправителя (опционально)
        
    Return:
        dict: Результат отправки email
    """
    try:
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
            
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        return {
            'status': 'success',
            'message': f'Email отправлен {len(recipient_list)} получателям',
            'subject': subject
        }
        
    except Exception as e:
        # Повторная попытка через 60 секунд
        raise self.retry(exc=e, countdown=60)
    