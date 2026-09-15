import asyncio
import aiohttp
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage



# CONFIGURATION


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "http://127.0.0.1:8000/api"



# BOT / DISPATCHER


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_tokens = {}

def button_keyboard(text, callback_data):
    """Tworzy klawiaturę z jednym przyciskiem."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=text, callback_data=callback_data)
        ]]
    )

def logged_keyboard():
    """Tworzy menu wyświetlane po zalogowaniu użytkownika."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Pizza", callback_data="menu_pizza"),
            InlineKeyboardButton(text="Log out", callback_data="menu_logout")
        ]]
    )

def auth_headers(telegram_user_id):
    """Tworzy nagłówek autoryzacji z tokenem JWT użytkownika."""
    return {
        "Authorization": f"Bearer {user_tokens[telegram_user_id]['access']}"
    }



# FSM STATES



class LoginForm(StatesGroup):
    username = State()
    password = State()


class OrderForm(StatesGroup):
    address = State()
    phone = State()



# MAIN MENU



@dp.message(CommandStart())
async def start(message: Message):
    """Wyświetla główne menu po uruchomieniu bota za pomocą /start."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Pizza", callback_data="menu_pizza")],
            [InlineKeyboardButton(text="Log in", callback_data="menu_login")],
            [InlineKeyboardButton(text="Log out", callback_data="menu_logout")]
        ]
    )

    await message.answer(
        "Welcome in pizzeria!\n\nSelect option:",
        reply_markup=keyboard
    )



@dp.callback_query(F.data == "menu_pizza")
async def menu_pizza(callback: CallbackQuery):
    """Obsługuje przycisk Pizza i sprawdza, czy użytkownik jest zalogowany."""
    if callback.from_user.id not in user_tokens:
        await callback.message.answer(
            "You must log in first.",
            reply_markup=button_keyboard("Log in", "menu_login")
        )
        await callback.answer()
        return

    await callback.answer()
    await pizzas(callback.message)



@dp.callback_query(F.data == "menu_cart")
async def menu_cart(callback: CallbackQuery):
    """Otwiera koszyk zalogowanego użytkownika."""
    await callback.answer()
    await cart(callback.message, callback.from_user.id)



@dp.callback_query(F.data == "menu_order")
async def menu_order(callback: CallbackQuery, state: FSMContext):
    """Rozpoczyna proces składania zamówienia."""
    await callback.answer()
    await order_start(callback.message, state, callback.from_user.id)



@dp.callback_query(F.data == "menu_login")
async def menu_login(callback: CallbackQuery, state: FSMContext):
    """Rozpoczyna proces logowania użytkownika."""
    await callback.answer()
    await state.set_state(LoginForm.username)
    await callback.message.answer("Please enter your account username:")



@dp.callback_query(F.data == "menu_logout")
async def menu_logout(callback: CallbackQuery):
    """Wylogowuje użytkownika poprzez usunięcie zapisanych tokenów."""
    await callback.answer()
    telegram_user_id = callback.from_user.id

    if telegram_user_id not in user_tokens:
        await callback.message.answer("You are not logged in.")
        return

    del user_tokens[telegram_user_id]

    await callback.message.answer(
        "Logged out successfully!",
        reply_markup=button_keyboard("Log in", "menu_login")
    )




# LOGIN / LOGOUT


@dp.message(LoginForm.username)
async def login_username(message: Message, state: FSMContext):
    """Zapisuje nazwę użytkownika i przechodzi do podania hasła."""
    await state.update_data(username=message.text)
    await state.set_state(LoginForm.password)
    await message.answer("Please enter your password:")



@dp.message(LoginForm.password)
async def login_password(message: Message, state: FSMContext):
    """Loguje użytkownika przez API i zapisuje otrzymane tokeny JWT."""
    data = await state.get_data()

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/login/",
            json={
                "username": data["username"],
                "password": message.text
            }
        ) as response:
            if response.status != 200:
                await message.answer("Incorrect username or password.",
                reply_markup=button_keyboard("Log in", "menu_login")
                )
                await state.clear()
                return

            tokens = await response.json()

    user_tokens[message.from_user.id] = {
        "access": tokens["access"],
        "refresh": tokens["refresh"]
    }

    await state.clear()

    await message.answer(
        "Logged in successfully!",
        reply_markup=logged_keyboard()
    )


# PIZZA


async def pizzas(message: Message):
    """Pobiera pizze z API i wyświetla je jako przyciski."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/pizza/") as response:
            if response.status != 200:
                await message.answer("Failed to load pizzas.")
                return

            pizzas_data = await response.json()

    if not pizzas_data:
        await message.answer("No pizzas available.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=pizza["name"],
                callback_data=f"pizza:{pizza['id']}"
            )]
            for pizza in pizzas_data
        ]
    )

    await message.answer("Choose a pizza:", reply_markup=keyboard)



@dp.callback_query(F.data.startswith("pizza:"))
async def select_pizza(callback: CallbackQuery):
    """Obsługuje wybór pizzy i wyświetla dostępne rozmiary."""
    await callback.answer()
    pizza_id = callback.data.split(":")[1]

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/size/") as response:
            if response.status != 200:
                await callback.message.answer("Failed to load sizes.")
                return

            sizes = await response.json()

    if not sizes:
        await callback.message.answer("No sizes available.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=size["name"],
                callback_data=f"size:{pizza_id}:{size['id']}"
            )]
            for size in sizes
        ]
    )

    await callback.message.answer("Choose a size:", reply_markup=keyboard)



@dp.callback_query(F.data.startswith("size:"))
async def select_size(callback: CallbackQuery):
    """Obsługuje wybór rozmiaru i wyświetla dostępne rodzaje ciasta."""
    await callback.answer()
    _, pizza_id, size_id = callback.data.split(":")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/typecake/") as response:
            if response.status != 200:
                await callback.message.answer("Failed to load crust types.")
                return

            typecakes = await response.json()

    if not typecakes:
        await callback.message.answer("No crust types available.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=typecake["name"],
                callback_data=f"typecake:{pizza_id}:{size_id}:{typecake['id']}"
            )]
            for typecake in typecakes
        ]
    )

    await callback.message.answer("Choose a crust type:", reply_markup=keyboard)



@dp.callback_query(F.data.startswith("typecake:"))
async def select_typecake(callback: CallbackQuery):
    """Obsługuje wybór rodzaju ciasta i wyświetla możliwe ilości."""
    await callback.answer()
    _, pizza_id, size_id, typecake_id = callback.data.split(":")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=str(quantity),
                callback_data=f"add:{pizza_id}:{size_id}:{typecake_id}:{quantity}"
            )
            for quantity in range(1, 5)
        ]]
    )

    await callback.message.answer(
        "Choose quantity:",
        reply_markup=keyboard
    )



# ADD TO CART



@dp.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    """Dodaje wybraną konfigurację pizzy do koszyka użytkownika."""
    telegram_user_id = callback.from_user.id

    if telegram_user_id not in user_tokens:
        await callback.message.answer(
            "You must log in first.",
            reply_markup=button_keyboard("Log in", "menu_login")
        )
        await callback.answer()
        return

    _, pizza_id, size_id, typecake_id, quantity = callback.data.split(":")

    headers = auth_headers(telegram_user_id)

    data = {
        "pizza": int(pizza_id),
        "size": int(size_id),
        "typecake": int(typecake_id),
        "quantity": int(quantity)
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/cart/add/",
            json=data,
            headers=headers
        ) as response:
            if response.status == 401:
                await callback.message.answer(
                    "Your session has expired.",
                    reply_markup=button_keyboard("Log in", "menu_login")
                )
                await callback.answer()
                return

            if response.status != 201:
                error = await response.text()
                await callback.message.answer(
                    f"Unable to add to cart.\n{error}"
                )
                await callback.answer()
                return

    await callback.message.answer(
        "The pizza has been added to your cart!",
        reply_markup=button_keyboard("Cart", "menu_cart")
    )
    await callback.answer()



# CART



async def cart(message: Message, telegram_user_id=None):
    """Pobiera z API i wyświetla zawartość koszyka użytkownika."""
    if telegram_user_id is None:
        telegram_user_id = message.from_user.id

    if telegram_user_id not in user_tokens:
        await message.answer(
            "You are not logged in.",
            reply_markup=button_keyboard("Log in", "menu_login")
        )
        return

    headers = auth_headers(telegram_user_id)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_URL}/cart/",
            headers=headers
        ) as response:
            if response.status == 401:
                await message.answer(
                    "Your session has expired.",
                    reply_markup=button_keyboard("Log in", "menu_login")
                )
                return

            if response.status != 200:
                await message.answer("The shopping cart could not be loaded.")
                return

            cart_items = await response.json()

    if not cart_items:
        await message.answer("Your cart is empty.")
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

    await message.answer(
        text,
        reply_markup=button_keyboard("Order", "menu_order")
    )


# ORDER



async def order_start(message: Message, state: FSMContext, telegram_user_id=None):
    """Rozpoczyna składanie zamówienia i prosi o adres dostawy."""
    if telegram_user_id is None:
        telegram_user_id = message.from_user.id

    if telegram_user_id not in user_tokens:
        await message.answer(
            "You are not logged in.",
            reply_markup=button_keyboard("Log in", "menu_login")
        )
        return

    await state.set_state(OrderForm.address)
    await message.answer("Please enter the delivery address:")



@dp.message(OrderForm.address)
async def order_address(message: Message, state: FSMContext):
    """Zapisuje adres dostawy i prosi o numer telefonu."""
    await state.update_data(address=message.text)
    await state.set_state(OrderForm.phone)
    await message.answer("Please enter your phone number:")



@dp.message(OrderForm.phone)
async def order_phone(message: Message, state: FSMContext):
    """Wysyła zamówienie do API i wyświetla potwierdzenie zamówienia."""
    telegram_user_id = message.from_user.id

    if telegram_user_id not in user_tokens:
        await message.answer(
            "You are not logged in.",
            reply_markup=button_keyboard("Log in", "menu_login")
        )
        await state.clear()
        return

    data = await state.get_data()

    headers = auth_headers(telegram_user_id)

    order_data = {
        "address": data["address"],
        "phone": message.text
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/order/create/",
            json=order_data,
            headers=headers
        ) as response:
            if response.status == 401:
                await message.answer(
                    "Your session has expired.",
                    reply_markup=button_keyboard("Log in", "menu_login")
                )
                await state.clear()
                return

            if response.status != 201:
                error = await response.text()
                await message.answer(
                    f"The order could not be placed.\n{error}"
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



# RUN BOT


async def main(): 
    """Uruchamia bota Telegram i rozpoczyna odbieranie wiadomości.""" 
    print("Bot is running...") 
    await dp.start_polling(bot) 
 
 
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")