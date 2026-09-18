import asyncio
import aiohttp
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message


# Konfiguracja

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "http://127.0.0.1:8000/api"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Przechowuje tokeny zalogowanych użytkowników.
user_tokens = {}

# Przechowuje tymczasowe dane użytkowników.
user_data = {}


def get_headers(user_id):
    """Tworzy nagłówek z tokenem JWT."""

    token = user_tokens[user_id]["access"]

    return {
        "Authorization": f"Bearer {token}"
    }


# Start

@dp.message(CommandStart())
async def start(message: Message):
    """Wyświetla dostępne komendy bota."""

    await message.answer(
        "Welcome in pizzeria!\n\n"
        "/register - create account\n"
        "/login - log in\n"
        "/pizza - choose pizza\n"
        "/cart - show cart\n"
        "/order - create order\n"
        "/logout - log out"
    )


# Rejestracja

@dp.message(Command("register"))
async def register(message: Message):
    """Rozpoczyna rejestrację użytkownika."""

    user_id = message.from_user.id

    # Bot będzie teraz czekał na nazwę użytkownika.
    user_data[user_id] = {
        "action": "register",
        "step": "username"
    }

    await message.answer("Enter your username:")


# Login

@dp.message(Command("login"))
async def login(message: Message):
    """Rozpoczyna logowanie użytkownika."""

    user_id = message.from_user.id

    # Bot będzie teraz czekał na nazwę użytkownika.
    user_data[user_id] = {
        "action": "login",
        "step": "username"
    }

    await message.answer("Enter your username:")


# Logout

@dp.message(Command("logout"))
async def logout(message: Message):
    """Wylogowuje użytkownika."""

    user_id = message.from_user.id

    # Sprawdza, czy użytkownik jest zalogowany.
    if user_id not in user_tokens:
        await message.answer("You are not logged in.")
        return

    # Usuwa tokeny i dane użytkownika.
    del user_tokens[user_id]
    user_data.pop(user_id, None)

    await message.answer("Logged out successfully.")


# Pizza

@dp.message(Command("pizza"))
async def pizza(message: Message):
    """Pobiera z API listę pizz."""

    user_id = message.from_user.id

    # Tylko zalogowany użytkownik może korzystać z koszyka.
    if user_id not in user_tokens:
        await message.answer("You must log in first. Use /login.")
        return

    try:
        # Pobiera pizze z Django API.
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/pizza/"
            ) as response:

                if response.status != 200:
                    await message.answer("Failed to load pizzas.")
                    return

                pizzas = await response.json()

    except aiohttp.ClientError:
        await message.answer("Cannot connect to the server.")
        return

    if not pizzas:
        await message.answer("No pizzas available.")
        return

    # Tworzy listę pizz wyświetlaną użytkownikowi.
    text = "Available pizzas:\n\n"
    pizza_ids = []

    for item in pizzas:
        text += f"{item['id']}. {item['name']}\n"
        pizza_ids.append(item["id"])

    text += "\nEnter pizza ID:"

    # Zapamiętuje dostępne ID pizz.
    user_data[user_id] = {
        "action": "pizza",
        "step": "pizza",
        "pizza_ids": pizza_ids
    }

    await message.answer(text)


# Koszyk

@dp.message(Command("cart"))
async def cart(message: Message):
    """Pobiera z API i wyświetla koszyk użytkownika."""

    user_id = message.from_user.id

    if user_id not in user_tokens:
        await message.answer("You must log in first. Use /login.")
        return

    # Tworzy nagłówek z tokenem JWT.
    headers = get_headers(user_id)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/cart/",
                headers=headers
            ) as response:

                # Status 401 oznacza problem z autoryzacją.
                if response.status == 401:
                    user_tokens.pop(user_id, None)

                    await message.answer(
                        "Your session has expired. Use /login."
                    )
                    return

                if response.status != 200:
                    await message.answer("Could not load cart.")
                    return

                items = await response.json()

    except aiohttp.ClientError:
        await message.answer("Cannot connect to the server.")
        return

    if not items:
        await message.answer("Your cart is empty.")
        return

    # Tworzy wiadomość z zawartością koszyka.
    text = "Your cart:\n\n"

    for item in items:
        text += (
            f"Pizza: {item['pizza']}\n"
            f"Size: {item['size']}\n"
            f"Crust: {item['typecake']}\n"
            f"Quantity: {item['quantity']}\n\n"
        )

    text += "Use /order to create an order."

    await message.answer(text)


# Zamowienie

@dp.message(Command("order"))
async def order(message: Message):
    """Rozpoczyna składanie zamówienia."""

    user_id = message.from_user.id

    if user_id not in user_tokens:
        await message.answer("You must log in first. Use /login.")
        return

    # Pierwszym etapem zamówienia jest podanie adresu.
    user_data[user_id] = {
        "action": "order",
        "step": "address"
    }

    await message.answer("Enter delivery address:")



@dp.message()
async def text_message(message: Message):
    """
    Obsługuje dane wpisywane przez użytkownika podczas
    rejestracji, logowania, wyboru pizzy i zamówienia.
    """

    user_id = message.from_user.id

    # Bot nie oczekuje obecnie żadnych danych.
    if user_id not in user_data:
        await message.answer("Use /start to see available commands.")
        return

    data = user_data[user_id]
    action = data["action"]
    step = data["step"]
    text = message.text.strip()


    # Rejestracja - nazwa uzytkownika

    if action == "register" and step == "username":

    # Nazwa użytkownika musi mieć minimum 3 znaki.
        if len(text) < 3:
            await message.answer(
                "Username must have at least 3 characters."
            )
            return

        user_data[user_id]["username"] = text
        user_data[user_id]["step"] = "email"

        await message.answer("Enter your email:")
        return

    # Rejestracja mail

    if action == "register" and step == "email":

        # Prosta walidacja adresu email.
        if "@" not in text or "." not in text:
            await message.answer("Enter a valid email address.")
            return

        user_data[user_id]["email"] = text
        user_data[user_id]["step"] = "password"

        await message.answer("Enter your password:")
        return
    # Rejestracja - hasło

    if action == "register" and step == "password":

        # Hasło musi mieć minimum 8 znaków.
        if len(text) < 8:
            await message.answer(
                "Password must have at least 8 characters."
            )
            return

        username = data["username"]
        email = data["email"]

        register_data = {
            "username": username,
            "email": email,
            "password": text
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/register/",
                    json=register_data
                ) as response:

                    if response.status != 201:
                        error = await response.text()

                        await message.answer(
                            f"Registration failed.\n{error}"
                        )
                        return

        except aiohttp.ClientError:
            await message.answer("Cannot connect to the server.")
            return

        del user_data[user_id]

        await message.answer(
            "Account created successfully!\n"
            "Use /login to log in."
        )
        return


    # LOGIN - USERNAME

    if action == "login" and step == "username":

        if not text:
            await message.answer("Username cannot be empty.")
            return

        user_data[user_id]["username"] = text
        user_data[user_id]["step"] = "password"

        await message.answer("Enter your password:")
        return


    # LOGIN - PASSWORD

    if action == "login" and step == "password":

        if not text:
            await message.answer("Password cannot be empty.")
            return

        username = data["username"]

        try:
            # Wysyła login i hasło do API.
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/login/",
                    json={
                        "username": username,
                        "password": text
                    }
                ) as response:

                    if response.status != 200:
                        await message.answer(
                            "Incorrect username or password."
                        )
                        return

                    # API zwraca tokeny JWT.
                    tokens = await response.json()

        except aiohttp.ClientError:
            await message.answer("Cannot connect to the server.")
            return

        # Zapisuje tokeny użytkownika.
        user_tokens[user_id] = tokens
        del user_data[user_id]

        await message.answer(
            "Logged in successfully!\n"
            "Use /pizza to choose a pizza."
        )
        return


    # PIZZA - PIZZA ID

    if action == "pizza" and step == "pizza":

        # Sprawdza, czy użytkownik podał liczbę.
        if not text.isdigit():
            await message.answer("Pizza ID must be a number.")
            return

        pizza_id = int(text)

        # Sprawdza, czy pizza istnieje.
        if pizza_id not in data["pizza_ids"]:
            await message.answer("Pizza with this ID does not exist.")
            return

        user_data[user_id]["pizza_id"] = pizza_id

        try:
            # Pobiera dostępne rozmiary z API.
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_URL}/size/"
                ) as response:

                    if response.status != 200:
                        await message.answer("Failed to load sizes.")
                        return

                    sizes = await response.json()

        except aiohttp.ClientError:
            await message.answer("Cannot connect to the server.")
            return

        if not sizes:
            await message.answer("No sizes available.")
            return

        text_sizes = "Available sizes:\n\n"
        size_ids = []

        for size in sizes:
            text_sizes += f"{size['id']}. {size['name']}\n"
            size_ids.append(size["id"])

        text_sizes += "\nEnter size ID:"

        # Przechodzi do wyboru rozmiaru.
        user_data[user_id]["size_ids"] = size_ids
        user_data[user_id]["step"] = "size"

        await message.answer(text_sizes)
        return


    # PIZZA - SIZE ID

    if action == "pizza" and step == "size":

        if not text.isdigit():
            await message.answer("Size ID must be a number.")
            return

        size_id = int(text)

        if size_id not in data["size_ids"]:
            await message.answer("Size with this ID does not exist.")
            return

        user_data[user_id]["size_id"] = size_id

        try:
            # Pobiera dostępne rodzaje ciasta.
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_URL}/typecake/"
                ) as response:

                    if response.status != 200:
                        await message.answer(
                            "Failed to load crust types."
                        )
                        return

                    crusts = await response.json()

        except aiohttp.ClientError:
            await message.answer("Cannot connect to the server.")
            return

        if not crusts:
            await message.answer("No crust types available.")
            return

        text_crusts = "Available crust types:\n\n"
        crust_ids = []

        for crust in crusts:
            text_crusts += f"{crust['id']}. {crust['name']}\n"
            crust_ids.append(crust["id"])

        text_crusts += "\nEnter crust ID:"

        # Przechodzi do wyboru rodzaju ciasta.
        user_data[user_id]["crust_ids"] = crust_ids
        user_data[user_id]["step"] = "crust"

        await message.answer(text_crusts)
        return


    # PIZZA - CRUST ID

    if action == "pizza" and step == "crust":

        if not text.isdigit():
            await message.answer("Crust ID must be a number.")
            return

        crust_id = int(text)

        if crust_id not in data["crust_ids"]:
            await message.answer("Crust with this ID does not exist.")
            return

        # Zapamiętuje ciasto i przechodzi do ilości.
        user_data[user_id]["crust_id"] = crust_id
        user_data[user_id]["step"] = "quantity"

        await message.answer("Enter quantity from 1 to 4:")
        return


    # PIZZA - QUANTITY

    if action == "pizza" and step == "quantity":

        if not text.isdigit():
            await message.answer("Quantity must be a number.")
            return

        quantity = int(text)

        # Sprawdza poprawność ilości.
        if quantity < 1 or quantity > 4:
            await message.answer("Quantity must be from 1 to 4.")
            return

        if user_id not in user_tokens:
            del user_data[user_id]

            await message.answer("You must log in first. Use /login.")
            return

        # Dane pizzy wysyłane do koszyka.
        cart_data = {
            "pizza": data["pizza_id"],
            "size": data["size_id"],
            "typecake": data["crust_id"],
            "quantity": quantity
        }

        headers = get_headers(user_id)

        try:
            # Dodaje pizzę do koszyka przez API.
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/cart/add/",
                    json=cart_data,
                    headers=headers
                ) as response:

                    if response.status == 401:
                        user_tokens.pop(user_id, None)
                        del user_data[user_id]

                        await message.answer(
                            "Your session has expired. Use /login."
                        )
                        return

                    if response.status != 201:
                        error = await response.text()

                        await message.answer(
                            f"Could not add pizza to cart.\n{error}"
                        )
                        return

        except aiohttp.ClientError:
            await message.answer("Cannot connect to the server.")
            return

        # Wybór pizzy został zakończony.
        del user_data[user_id]

        await message.answer(
            "Pizza added to cart!\n\n"
            "Use /pizza to add another pizza.\n"
            "Use /cart to show your cart.\n"
            "Use /order to create an order."
        )
        return


    # ORDER - ADDRESS

    if action == "order" and step == "address":

        # Adres musi mieć minimum 5 znaków.
        if len(text) < 5:
            await message.answer("Enter a valid delivery address.")
            return

        user_data[user_id]["address"] = text
        user_data[user_id]["step"] = "phone"

        await message.answer("Enter your phone number:")
        return


    # ORDER - PHONE

    if action == "order" and step == "phone":

        # Do sprawdzenia numeru usuwamy opcjonalny znak +.
        phone = text.replace("+", "")

        if not phone.isdigit():
            await message.answer(
                "Phone number can contain only numbers "
                "and an optional +."
            )
            return

        if len(phone) < 9:
            await message.answer("Phone number is too short.")
            return

        if user_id not in user_tokens:
            del user_data[user_id]

            await message.answer("You must log in first. Use /login.")
            return

        # Dane zamówienia wysyłane do API.
        order_data = {
            "address": data["address"],
            "phone": text
        }

        headers = get_headers(user_id)

        try:
            # Tworzy zamówienie przez Django API.
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/order/create/",
                    json=order_data,
                    headers=headers
                ) as response:

                    if response.status == 401:
                        user_tokens.pop(user_id, None)
                        del user_data[user_id]

                        await message.answer(
                            "Your session has expired. Use /login."
                        )
                        return

                    if response.status != 201:
                        error = await response.text()

                        await message.answer(
                            f"Order could not be created.\n{error}"
                        )
                        return

                    result = await response.json()

        except aiohttp.ClientError:
            await message.answer("Cannot connect to the server.")
            return

        # Zamówienie zostało zakończone.
        del user_data[user_id]

        await message.answer(
            "Order created successfully!\n\n"
            f"Order ID: {result['order_id']}\n"
            f"Total: {result['value']} zł"
        )
        return


# Run bot

async def main():
    """Uruchamia bota Telegram."""

    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Bot stopped.")