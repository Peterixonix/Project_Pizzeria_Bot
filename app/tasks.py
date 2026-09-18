from celery import shared_task


@shared_task
def check_orders():
    print("Checking pizzeria orders...")


@shared_task
def send_notification():
    print("Sending pizzeria notification...")