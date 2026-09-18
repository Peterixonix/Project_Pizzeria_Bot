import os

import requests
from celery import shared_task
from dotenv import load_dotenv


load_dotenv()


# Klasa bazowa dla powiadomień.
class NotificationService:
    def send(self, message):
        raise NotImplementedError


# Wysyła powiadomienie przez Telegram.
class TelegramNotiService(NotificationService):
    def send(self, message):
        bot_token = os.getenv("BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": message
            }
        )


# Zadanie Celery wysyłające powiadomienie.
@shared_task
def send_notification(message):
    service = TelegramNotiService()
    service.send(message)