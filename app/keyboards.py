from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from app.config import settings
from typing import List
from app.models.models import VPN, VPNCategory, UserVPN
import json

#Главное меню клиента

def client_main_kb(user_info) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if user_info.trial_until is None:
        kb.button(text='⌛Пробный период', callback_data='get_trial')
    kb.button(text='🗝️Мои подключения', callback_data='my_keys')       # было my_profile
    kb.button(text='🌍Купить VPN', callback_data='catalog')
    kb.button(text='👨‍💻Тех.Поддержка', callback_data='support')
    # kb.button(text='💌О нас', callback_data='products')               # здесь будет кнопка с моими готовыми решениями
    if user_info.id in settings.ADMIN_IDS:
        kb.button(text='⚙️Админ панель', callback_data='admin_panel')
    kb.adjust(1)
    return kb.as_markup()

def go_on_main() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Посмотреть мои ключи", callback_data="my_keys")    #было purchases
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()

# def purchases_kb(product_id, price) ->InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()
#     kb.button(text='🗑Посмотреть мои ключи', callback_data='purchases')
#     kb.button(text='🏠На главную', callback_data='home')
#     kb.adjust(1)
#     return kb.as_markup()

def product_kb(product_id, price) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='💸Купить', callback_data=f'buy_{product_id}_price{price}')
    kb.button(text='🔙Назад', callback_data='catalog')
    kb.button(text='🏠На главную', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()


def catalog_kb(catalog_data: List[VPNCategory]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    print("Загружаем каталог...")
    for category in catalog_data:
        kb.button(text=category.name, callback_data=f"buy_{category.id}_{category.price}")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup() 

def catalog_key_kb(catalog_data: List[VPN]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    print("Загружаем каталог ключей...")
    for category in catalog_data:
        kb.button(text=f"🔑{category.email}", callback_data=f"show_{category.email}")  
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()



#РАБОТАЕТ
def key_options_kb(key_email: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    print("Открываем информацию о ключе...")
    price = 150
    month = 30
    if key_email.startswith('payed'):
        kb.button(text="Инструкция по подключению", callback_data="instructions")
        kb.button(text="🔄Продлить на месяц", callback_data=f"update|{key_email}|{price}|{month}")
        kb.button(text="🔄Продлить на 3 месяца", callback_data=f"update|{key_email}|{price*3}|{month*3}")
        kb.button(text="🔄Продлить на 6 месяцев", callback_data=f"update|{key_email}|{price*6}|{month*6}")
        kb.button(text="🔄Продлить на год", callback_data=f"update|{key_email}|{price*12}|{month*12}")
        kb.button(text='🔙 Назад', callback_data='my_keys')
        kb.button(text="🏠 На главную", callback_data="home")
        kb.adjust(1)
    else:
        kb.button(text='🔙 Назад', callback_data='my_keys')
        kb.button(text="🏠 На главную", callback_data="home")
        kb.adjust(1)
    return kb.as_markup() 



def get_product_buy_kb(price) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'💸 Оплатить{price}₽', pay=True)],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='my_keys')]
    ])

def instructions_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Iphone", callback_data="instruction_iphone")
    kb.button(text="💬 Android", callback_data="instruction_android")
    kb.button(text="💬 TV приставка", callback_data="instruction_tv")
    kb.button(text="💬 Windows", callback_data="instruction_windows")
    kb.button(text='🏠На главную', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()

def support_help_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='🗝️Мои подключения', callback_data='my_keys')
    kb.button(text='🔙 Назад', callback_data='instructions')
    kb.button(text=f"💬 Написать в поддержку", url="https://t.me/iiinacc")
    kb.button(text='🏠На главную', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()

def products() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=f"💬 Приставка для TV", url="https://t.me/iiinacc")
    kb.button(text=f"💬 Умный роутер", url="https://t.me/iiinacc")

    kb.button(text='🏠На главную', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()



async def sendall_choose_client():
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=f'Всем пользователям', callback_data=f'sendall_all'))
    kb.add(InlineKeyboardButton(text=f'Клиентам с бесплатными серверами', callback_data=f'sendall_free'))
    kb.add(InlineKeyboardButton(text=f'Клиентам с платными серверами', callback_data=f'sendall_paid'))
    kb.add(InlineKeyboardBuilder(text=f'❌Отмена', callback_data=f'start'))
    return kb.adjust(1).as_markup()
