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
    kb.button(text='💌 Оборудование для дома', callback_data='products')               # здесь будет кнопка с моими готовыми решениям
    kb.button(text='📄Правила использования сервиса', callback_data='rules')
    kb.button(text='👨‍💻Тех.Поддержка', callback_data='support')
    if user_info.telegram_id in settings.ADMIN_IDS:
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
        if category.name.lower() == "vless_payed":
            button_text = f"💎 Премиум VPN Финлядния — {category.price}₽"
        else:
            button_text = f"{category.name} — {category.price}₽"    
        kb.button(text=button_text, callback_data=f"buy_{category.id}_{category.price}")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(1)
    return kb.as_markup() 

def catalog_key_kb(catalog_data: List[VPN]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    print("Загружаем каталог ключей...")
    for category in catalog_data:
        if category.email.startswith("payed_"):
            button_text = f"💎Оплаченный VPN ключ {category.email}"
        elif category.email.startswith("trial_"):
            button_text = f"🧪 Пробный VPN {category.email}"
        else:
            button_text = f"{category.email} — до {category.expiry_time}"    
        kb.button(text=button_text, callback_data=f"show_{category.email}")
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
        kb.button(text="🟩Инструкция по подключению", callback_data="instructions")
        kb.button(text="🔄Продлить на месяц", callback_data=f"update|{key_email}|{price}|{month}")
        kb.button(text="🔄Продлить на 3 месяца", callback_data=f"update|{key_email}|{price*3}|{month*3}")
        kb.button(text="🔄Продлить на 6 месяцев", callback_data=f"update|{key_email}|{price*6}|{month*6}")
        kb.button(text="🔄Продлить на год", callback_data=f"update|{key_email}|{price*12}|{month*12}")
        kb.button(text='🔙 Назад', callback_data='my_keys')
        kb.button(text="🏠 На главную", callback_data="home")
        kb.adjust(1)
    else:
        kb.button(text="🟩Инструкция по подключению", callback_data="instructions")
        kb.button(text='🔙 Назад', callback_data='my_keys')
        kb.button(text="🏠 На главную", callback_data="home")
        kb.adjust(1)
    return kb.as_markup() 



def get_product_buy_kb(price) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'💸 Оплатить {price}₽', pay=True)],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='my_keys')]
    ])

def instructions_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🍏 Iphone", callback_data="instruction_iphone")
    kb.button(text="🤖 Android", callback_data="instruction_android")
    kb.button(text="📺 TV приставка", callback_data="instruction_tv")
    kb.button(text="💻 Windows", callback_data="instruction_windows")
    kb.button(text='🔙 Назад', callback_data='my_keys')
    kb.button(text='🏠На главную', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()



def support_help_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=f"💬 Написать в поддержку", url="https://t.me/iiinacc")
    kb.button(text='🏠На главную', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()

def products() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=f"📺 Приставка для TV", url="https://docs.google.com/document/d/1-5FiKRc8yam7ZjeCC0iV_BhV9xYTDfLS8-F18iqvJW4/edit?usp=sharing")
    kb.button(text=f"💬 Умный роутер", url="https://docs.google.com/document/d/1qEvXr3bZNywdviLRMKthgoByxiNCXo582nLI_RHUDak/edit?usp=sharing")
    kb.button(text=f"🛒 Заказать", url="https://t.me/iiinacc")
    kb.button(text='🏠На главную', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()

def key_option_trial_kb()->InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    print("Открываем информацию о ключе...")
    kb.button(text="🟩Инструкция по подключению", callback_data="instructions")
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
