from celery import shared_task


# Zadanie Celery przeznaczone do sprawdzania zamówień.
@shared_task
def check_orders():
    print("Checking pizzeria orders...")


# Zadanie Celery przeznaczone do wysyłania powiadomień.
@shared_task
def send_notification():
    print("Sending pizzeria notification...")