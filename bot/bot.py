import asyncio
import aiohttp
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "http://127.0.0.1:8000/api"


# =========================================================
# BOT / DISPATCHER
# =========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_tokens = {}


# =========================================================
# FSM STATES
# =========================================================

class LoginForm(StatesGroup):
    username = State()
    password = State()


class OrderForm(StatesGroup):
    address = State()
    phone = State()


# =========================================================
# MAIN MENU
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Pizza",
                    callback_data="menu_pizza"
                ),
                InlineKeyboardButton(
                    text="Cart",
                    callback_data="menu_cart"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Order",
                    callback_data="menu_order"
                ),
                InlineKeyboardButton(
                    text="Log in",
                    callback_data="menu_login"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Log out",
                    callback_data="menu_logout"
                ),
            ],
        ]
    )

    await message.answer(
        "Welcome in pizzeria!\n\n"
        "Select option:",
        reply_markup=keyboard
    )


@dp.callback_query(F.data == "menu_pizza")
async def menu_pizza(callback: CallbackQuery):
    telegram_user_id = callback.from_user.id

    if telegram_user_id not in user_tokens:
        await callback.message.answer(
            "You must log in first.\n"
            "Use /login"
        )

        await callback.answer()
        return

    await callback.answer()
    await pizzas(callback.message)


@dp.callback_query(F.data == "menu_cart")
async def menu_cart(callback: CallbackQuery):
    await callback.answer()

    await cart(
        callback.message,
        telegram_user_id=callback.from_user.id
    )


@dp.callback_query(F.data == "menu_order")
async def menu_order(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()

    await order_start(
        callback.message,
        state,
        telegram_user_id=callback.from_user.id
    )


@dp.callback_query(F.data == "menu_login")
async def menu_login(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()

    await state.set_state(LoginForm.username)

    await callback.message.answer(
        "Please enter your account username:"
    )


@dp.callback_query(F.data == "menu_logout")
async def menu_logout(callback: CallbackQuery):
    await callback.answer()

    telegram_user_id = callback.from_user.id

    if telegram_user_id in user_tokens:
        del user_tokens[telegram_user_id]

        await callback.message.answer(
            "Logged out successfully!"
        )
    else:
        await callback.message.answer(
            "You are not logged in."
        )


# =========================================================
# LOGIN / LOGOUT
# =========================================================

@dp.message(Command("login"))
async def login_start(
    message: Message,
    state: FSMContext
):
    await state.set_state(LoginForm.username)

    await message.answer(
        "Please enter your account username:"
    )


@dp.message(LoginForm.username)
async def login_username(
    message: Message,
    state: FSMContext
):
    await state.update_data(
        username=message.text
    )

    await state.set_state(
        LoginForm.password
    )

    await message.answer(
        "Please enter your password:"
    )


@dp.message(LoginForm.password)
async def login_password(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    username = data["username"]
    password = message.text

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/login/",
            json={
                "username": username,
                "password": password,
            },
        ) as response:

            if response.status != 200:
                await message.answer(
                    "Incorrect username or password."
                )

                await state.clear()
                return

            tokens = await response.json()

    telegram_user_id = message.from_user.id

    user_tokens[telegram_user_id] = {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
    }

    await state.clear()

    await message.answer(
        "Logged in successfully!"
    )


@dp.message(Command("logout"))
async def logout(message: Message):
    telegram_user_id = message.from_user.id

    if telegram_user_id in user_tokens:
        del user_tokens[telegram_user_id]

        await message.answer(
            "You have been logged out."
        )
    else:
        await message.answer(
            "You are not logged in."
        )


# =========================================================
# PIZZA
# =========================================================

@dp.message(Command("pizza"))
async def pizzas(message: Message):

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_URL}/pizza/"
        ) as response:

            if response.status != 200:
                await message.answer(
                    "The pizza list could not be loaded."
                )
                return

            pizzas_data = await response.json()

    if not pizzas_data:
        await message.answer(
            "No pizzas available."
        )
        return

    buttons = []

    for pizza in pizzas_data:
        pizza_name = pizza.get(
            "name",
            f"Pizza {pizza['id']}"
        )

        buttons.append([
            InlineKeyboardButton(
                text=pizza_name,
                callback_data=f"pizza:{pizza['id']}"
            )
        ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await message.answer(
        "Choose your pizza:",
        reply_markup=keyboard
    )


@dp.callback_query(F.data.startswith("pizza:"))
async def select_pizza(callback: CallbackQuery):
    pizza_id = callback.data.split(":")[1]

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_URL}/size/"
        ) as response:

            if response.status != 200:
                await callback.message.answer(
                    "Unable to retrieve the size."
                )
                await callback.answer()
                return

            sizes = await response.json()

    buttons = []

    for size in sizes:
        size_name = size.get(
            "name",
            str(size.get("size", size["id"]))
        )

        buttons.append([
            InlineKeyboardButton(
                text=f"{size_name}",
                callback_data=(
                    f"size:{pizza_id}:{size['id']}"
                )
            )
        ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.answer(
        "Choose your size:",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("size:"))
async def select_size(callback: CallbackQuery):
    pizza_id, size_id = callback.data.split(":")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_URL}/typecake/"
        ) as response:

            if response.status != 200:
                await callback.message.answer(
                    "Unable to retrieve the type of cake."
                )
                await callback.answer()
                return

            typecakes = await response.json()

    buttons = []

    for typecake in typecakes:
        typecake_name = typecake.get(
            "name",
            f"Cake {typecake['id']}"
        )

        buttons.append([
            InlineKeyboardButton(
                text=typecake_name,
                callback_data=(
                    f"type:{pizza_id}:{size_id}:"
                    f"{typecake['id']}"
                )
            )
        ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.answer(
        "Choose the type of cake:",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("type:"))
async def select_typecake(callback: CallbackQuery):
    _, pizza_id, size_id, typecake_id = (
        callback.data.split(":")
    )

    buttons = [
        [
            InlineKeyboardButton(
                text="1",
                callback_data=(
                    f"add:{pizza_id}:{size_id}:"
                    f"{typecake_id}:1"
                )
            ),
            InlineKeyboardButton(
                text="2",
                callback_data=(
                    f"add:{pizza_id}:{size_id}:"
                    f"{typecake_id}:2"
                )
            ),
            InlineKeyboardButton(
                text="3",
                callback_data=(
                    f"add:{pizza_id}:{size_id}:"
                    f"{typecake_id}:3"
                )
            ),
            InlineKeyboardButton(
                text="4",
                callback_data=(
                    f"add:{pizza_id}:{size_id}:"
                    f"{typecake_id}:4"
                )
            ),
        ]
    ]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    await callback.message.answer(
        "Choose quantity:",
        reply_markup=keyboard
    )

    await callback.answer()


# =========================================================
# ADD TO CART
# =========================================================

@dp.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    telegram_user_id = callback.from_user.id

    if telegram_user_id not in user_tokens:
        await callback.message.answer(
            "You must log in first.\n"
            "Use /login"
        )

        await callback.answer()
        return

    pizza_id, size_id, typecake_id, quantity = (
        callback.data.split(":")
    )

    access_token = user_tokens[
        telegram_user_id
    ]["access"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    data = {
        "pizza": int(pizza_id),
        "size": int(size_id),
        "typecake": int(typecake_id),
        "quantity": int(quantity),
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/cart/add/",
            json=data,
            headers=headers,
        ) as response:

            if response.status == 401:
                await callback.message.answer(
                    "Your session has expired.\n"
                    "Please log in again using /login."
                )
                await callback.answer()
                return

            if response.status != 201:
                error = await response.text()

                await callback.message.answer(
                    f"Unable to add to basket.\n{error}"
                )
                await callback.answer()
                return

    await callback.message.answer(
        "The pizza has been added to your basket!\n\n"
        "Use /cart to view cart."
    )

    await callback.answer()


# =========================================================
# CART
# =========================================================

@dp.message(Command("cart"))
async def cart(
    message: Message,
    telegram_user_id=None
):
    if telegram_user_id is None:
        telegram_user_id = message.from_user.id

    if telegram_user_id not in user_tokens:
        await message.answer(
            "You are not logged in.\n"
            "Use /login."
        )
        return

    access_token = user_tokens[
        telegram_user_id
    ]["access"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_URL}/cart/",
            headers=headers
        ) as response:

            if response.status == 401:
                await message.answer(
                    "Your session has expired.\n"
                    "Please log in again using /login."
                )
                return

            if response.status != 200:
                await message.answer(
                    "The shopping cart could not be loaded."
                )
                return

            cart_items = await response.json()

    if not cart_items:
        await message.answer(
            "Your cart is empty."
        )
        return

    text = "Your cart:\n\n"

    for item in cart_items:
        text += (
            f"{item['pizza']}\n"
            f"Size: {item['size']}\n"
            f"Cake: {item['typecake']}\n"
            f"Quantity: {item['quantity']}\n"
            f"ID position: {item['id']}\n\n"
        )

    await message.answer(text)


# =========================================================
# ORDER
# =========================================================

@dp.message(Command("order"))
async def order_start(
    message: Message,
    state: FSMContext,
    telegram_user_id=None
):
    if telegram_user_id is None:
        telegram_user_id = message.from_user.id

    if telegram_user_id not in user_tokens:
        await message.answer(
            "You are not logged in.\n"
            "Use /login."
        )
        return

    await state.set_state(
        OrderForm.address
    )

    await message.answer(
        "Please enter the delivery address:"
    )


@dp.message(OrderForm.address)
async def order_address(
    message: Message,
    state: FSMContext
):
    await state.update_data(
        address=message.text
    )

    await state.set_state(
        OrderForm.phone
    )

    await message.answer(
        "Please enter your phone number:"
    )


@dp.message(OrderForm.phone)
async def order_phone(
    message: Message,
    state: FSMContext
):
    telegram_user_id = message.from_user.id

    if telegram_user_id not in user_tokens:
        await message.answer(
            "You are not logged in.\n"
            "Use /login."
        )
        await state.clear()
        return

    data = await state.get_data()

    address = data["address"]
    phone = message.text

    access_token = user_tokens[
        telegram_user_id
    ]["access"]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    order_data = {
        "address": address,
        "phone": phone,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/order/create/",
            json=order_data,
            headers=headers,
        ) as response:

            if response.status == 401:
                await message.answer(
                    "Your session has expired. Please log in again."
                )
                await state.clear()
                return

            if response.status != 201:
                error = await response.text()

                await message.answer(
                    "The order could not be placed.\n"
                    f"{error}"
                )
                await state.clear()
                return

            result = await response.json()

    await state.clear()

    await message.answer(
        "Your order has been placed!\n\n"
        f"ID Order: {result['order_id']}\n"
        f"Total: {result['value']} zł"
    )


# =========================================================
# RUN BOT
# =========================================================

async def main():
    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())