from app.services.text_format import humanize_timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import User
import app.states as st
import app.keyboards as kb
from app.dao.middleware import BaseDatabaseMiddleware
from datetime import datetime, timedelta, timezone
from app.bot import scheduler
from app.apsched import send_message, send_notification
from apscheduler.triggers.date import DateTrigger
from app.dao.user_dao import User, UserDAO, UserVPN, VPNDAOCategory, VPNDAO, VPNCategory
from app.schemas.schemas import TelegramIDModel, UserModel, VPNEmailFilter
from app.bot import bot
from app.config import settings

from app.services.xui import create_trial, update_month
import json

#Работа с middlewares
client = Router()

#Авторизация пользователя    (В РАБОТЕ !!! # user_info.is_trial_used () - НУЖНО ПРОВЕРЯТЬ НА ЭТО УСЛОВИЕ ЕЩЕ !!!!
@client.message(CommandStart())
async def send_main_menu(message:Message, session_with_commit:AsyncSession, state:FSMContext):
    user_id = message.from_user.id
    user_info = await UserDAO.find_one_or_none(
        session = session_with_commit,
        filters = TelegramIDModel(telegram_id = user_id)
    )
    if user_info:
        if user_info.trial_until and user_info.trial_until > datetime.now():    
            delta = user_info.trial_until - datetime.utcnow()
            await message.answer(
                    text = f'🤖<b>Добро пожаловать</b> \n\n🆓Ваш пробный период действует еще {humanize_timedelta(delta)}',
                    reply_markup=kb.client_main_kb(user_info)
                    )
        else:
            await message.answer(
                    text=f'🤖<b>Добро пожаловать</b> \n\nПриобретайте безопасный,устойчивый высокоскоростной VPN у нас!',
                    reply_markup=kb.client_main_kb(user_info)
                )
        await state.clear()
        return  
    values = UserModel(
        telegram_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        trial_until=None
    )
    await UserDAO.add(session = session_with_commit, values = values)
    user_info = await UserDAO.find_one_or_none(
        session=session_with_commit,
        filters=TelegramIDModel(telegram_id=user_id)
    )
    await message.answer(f"🎉<b>Благодаром за регистрацию!</b>. Теперь выберите необходимое действие.",
                         reply_markup = kb.client_main_kb(user_info))

#Даем триал (проверять триал наличие триала не нужно!)
@client.callback_query(F.data == 'get_trial')
async def get_trial_vpn(callback:CallbackQuery, session_with_commit:AsyncSession):
    user_id = callback.from_user.id
    user_name = callback.from_user.username
    category_vpn = 1 # its trial
    trial_until = datetime.now(timezone.utc) + timedelta(days=7)

    user_info = await UserDAO.find_one_or_none(
        session= session_with_commit,
        filters = TelegramIDModel(telegram_id=user_id)
    )
  
    vpn_key = await UserDAO.add_user_free_vpn(
        session=session_with_commit,
        user=user_info, 
        category_vpn=category_vpn, 
        until=trial_until)
    
    #Тригеры
    # delete_trigger = trial_until
    notification_trigger = datetime.now() + timedelta(days=4)
    delete_trigger = datetime.now() + timedelta(days=7)

   

    # Задачи scheduler
    # Уведолмение о том что заканчивается через 3 дня
    scheduler.add_job(
        func = send_notification,
        trigger= DateTrigger(run_date=notification_trigger),
        kwargs = {'user' : user_id, 'vpn_name': vpn_key.email},
        id=f"send_msg_{user_id}_{vpn_key.email}"
        )
    #Удаление ключа триала устанвока is_trial_used: True
    scheduler.add_job(
        func = send_message, 
        trigger = DateTrigger(run_date=delete_trigger),           
        args = [user_id, vpn_key.email],
        id=f"delete_key_{vpn_key.email}"
        )
    
    await callback.message.delete()
    await callback.message.answer(text=f'✅<b>Благодарим за использование нашего сервиса!</b>\n\n'
                                      f'Серевер успешно создан!\n<b>Ключ подключения:</b> \n\n'
                                      f'<code>{vpn_key.access_url}</code>',
                                      reply_markup=kb.key_option_trial_kb()
                                      )
    await callback.answer('Успех!')
    
@client.callback_query(F.data == 'my_profile')
async def page_about(call:CallbackQuery, session_without_commit:AsyncSession):
    await call.message.delete()
    await call.answer("Профиль")
    #Получаем статистику пользователя
    purchases = await UserDAO.get_purchase_statistic(session=session_without_commit, telegram_id=call.from_user.id)
    print(f'количество покупок {purchases}')
    if purchases is None:
        total_amount = 0
        total_purchases = 0
    else:
        total_amount = purchases.get("total_amount", 0)
        total_purchases = purchases.get("total_purchases", 0)
    #формируем сообщение в зависимости от наличия покупок
    if total_purchases ==0:
        await call.message.answer(
            text = "🔍 <b>У вас пока нет покупок.</b>\n\n"
                 "Откройте каталог и выберите что-нибудь интересное!",
            reply_markup=kb.client_main_kb(call.from_user.id)
        )
    else:
        text = (f"🛍 <b>Ваш профиль:</b>\n\n"
            f"Количество покупок: <b>{total_purchases}</b>\n"
            "Хотите просмотреть детали ваших покупок?"
            )
        
        await call.message.answer(
            text=text,
            reply_markup=kb.go_on_main()
        )


        

#Кнопка мои покупки
@client.callback_query(F.data == 'purchases')
async def my_purchases(call:CallbackQuery, session_without_commit:AsyncSession):   
    vpn_info = await UserDAO.get_user_vpns(session=session_without_commit, user_id=call.from_user.id)
    print(f"{call.from_user.id}")
    print(vpn_info)
    user_id = call.from_user.id
    user_info = await UserDAO.find_one_or_none(
         session = session_without_commit,
         filters = TelegramIDModel(telegram_id = user_id)
     )

    if not vpn_info:
        text = "У вас нет активных VPN ключей."
    else: 
        lines = []
        for i, vpn in enumerate(vpn_info, start=1):
            expiry = vpn['expiry_time']
            if isinstance(expiry, str):
                expiry_dt = datetime.fromisoformat(expiry)
            else:
                expiry_dt = expiry
            expiry_str = expiry_dt.strftime("%d.%m.%Y %H:%M")
            now = datetime.now()
            delta = expiry_dt - now
            days_left = delta.days

            lines.append(f"{i}.<code>{vpn['access_url']}</code> \n (истекает: {expiry_str}) \n ⌛Осталось дней:{days_left} \n")

        text = "\n".join(lines)
    

    await call.message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=kb.client_main_kb(user_info)
    )
    pass



#Меню выбора ключей для работы с ними в профиле пользователя (В РАБОТЕ)
# @client.callback_query(F.data == )


#Переход в каталог(ПОМЕНЯТЬ НАЗВАНИЕ КАТЕГОРИЙ)
@client.callback_query(F.data == 'catalog')
async def page_catalog(callback: CallbackQuery, session_without_commit: AsyncSession):
    await callback.answer('Загрузка каталога...')

    all_data = await VPNDAOCategory.find_all(session=session_without_commit)
    catalog_data = [c for c in all_data if c.name != "VLESS_trial"]

    await callback.message.edit_text(
        text="Выберите категорию товаров",
        reply_markup=kb.catalog_kb(catalog_data)
    )



#Выбор ключей кнопками (РАБОТАЕТ) - придумать название кнопок
@client.callback_query(F.data == 'my_keys')
async def keys_catalog(callback: CallbackQuery, session_without_commit: AsyncSession):
    await callback.answer('Загрузка каталога ключей...')
    await callback.message.delete()

    catalog_data = await VPNDAO.find_all_by_telegram_id(session=session_without_commit, telegram_id = callback.from_user.id)
    
    #ТУТ УБИРАЛИ TRIAL из списка по дате окончания
    # now = datetime.utcnow()
    # catalog_data = [vpn for vpn in catalog_data if vpn.expiry_time is None or vpn.expiry_time > now]
    if catalog_data:
        await callback.message.answer(
            text="Выберите VPN ключ",
            reply_markup=kb.catalog_key_kb(catalog_data)
        )
    else:
        all_data = await VPNDAOCategory.find_all(session=session_without_commit)
        catalog_data = [c for c in all_data if c.name != "VLESS_trial"]
        await callback.message.answer(
            text=f"У вас пока нет купленных ключей VPN \n\n Купить 👇",
            reply_markup=kb.catalog_kb(catalog_data)
        )

#Callback выбора ключей по кнопке
@client.callback_query(F.data.startswith("show_"))
async def show_key_button(call: CallbackQuery, session_without_commit:AsyncSession):
    await call.answer('Загрузка информации о ключе...')
    
    key_email = call.data.removeprefix('show_')

    #vpn_info = await UserDAO.get_user_vpns(session=session_without_commit, user_id=call.from_user.id)
    vpn_info = await VPNDAO.find_one_or_none(
        session=session_without_commit,
        filters=VPNEmailFilter(email=key_email)
        )
    if not vpn_info:
        await call.message.edit_text("❌ Ключ не найден или уже недействителен.")
        return
    expiry_str = vpn_info.expiry_time.strftime("%d.%m.%Y")  # если datetime
    expiry_dt = vpn_info.expiry_time
    access_url = vpn_info.access_url
    now = datetime.now()
    delta = expiry_dt - now
    days_left = delta.days
    if days_left <= 0:
        days_left = 0
    await call.message.delete()
    await call.message.answer(text=f"✅<b>Благодарим за использование нашего сервиса</b> \n"
                            f"Ваш ключ: \n"                            
                            f"<code>{access_url}</code> \n" 
                            f"(истекает: {expiry_str}) \n"
                            f"⌛ Осталось дней: {days_left} \n",
                        reply_markup=kb.key_options_kb(key_email))



#Переход на стартовую страницу(РАБОТАЕТ) (ВСТАВИТЬ УДАЛЕНИЕ)
@client.callback_query(F.data == 'home')
async def go_home(call:CallbackQuery, session_with_commit:AsyncSession, state:FSMContext):
    await state.clear()
    await call.message.delete()
    user_id = call.from_user.id
    user_info = await UserDAO.find_one_or_none(
        session = session_with_commit,
        filters = TelegramIDModel(telegram_id = user_id)
    )
    if user_info:
        if user_info.trial_until and user_info.trial_until > datetime.now():    
            delta = user_info.trial_until - datetime.utcnow()
            await call.message.answer(
                    text = f'🤖<b>Добро пожаловать</b> \n\n🆓Ваш пробный период действует еще {humanize_timedelta(delta)}',
                    reply_markup=kb.client_main_kb(user_info)
                    )
        else:
            await call.message.answer(
                    text=f'🤖<b>Добро пожаловать</b> \n\nПриобретайте безопасный,устойчивый высокоскоростной VPN у нас!',
                    reply_markup=kb.client_main_kb(user_info)
                )
        await state.clear()
        return
    await call.answer()

#Кнопка ИНСТРУКЦИЯ (В РАБОТЕ)
@client.callback_query(F.data == 'instructions')
async def go_support(call:CallbackQuery, session_without_commit: AsyncSession):
    await call.answer("Открываем инструкции...")
    await call.message.answer(text = f"Выберите устройство на котором вы хотите использовать ключ VPN.\n"
                              f"И мы покажем как просто его подключить...\n",                           
                              reply_markup=kb.instructions_kb()
                              )

@client.callback_query(F.data.startswith("instruction_"))
async def show_instruction(call:CallbackQuery, session_without_commit: AsyncSession):
    await call.answer("Открываем инструкцию для...")
    platform = call.data.replace("instruction_", "")

    instructions = {
         "iphone": (
        "📱 <b>Инструкция для iPhone - скачайте приложение в AppStore -> V2RayTun:</b>\n\n"
        "1️⃣ В этом телеграмм боте нажмите <b>Мои подключения</b> выберите ключ <b>payed_...</b>.\n"
        "2️⃣ Нажмите на него vless//... — ключ автоматически скопируется.\n"
        "3️⃣ Откройте приложение <b>V2RayTun</b>.\n"
        "4️⃣ Нажмите в правом углу кнопку <b>+</b> → <b>Импортировать из буфера</b>.\n"
        "5️⃣ Сохраните конфигурацию и включите подключение на большую кнопку по центру экрана.\n\n"
        "✅ Готово! VPN активен."
    ),
        "android": ("🤖 <b>Инструкция для Android - скачайте приложение в PlayMarket -> V2RayTun:</b>\n\n"
        "1️⃣ В этом телеграмм боте нажмите <b>Мои подключения</b> выберите ключ <b>payed_...</b>.\n"
        "2️⃣ Нажмите на него vless//... — ключ автоматически скопируется.\n"
        "3️⃣ Откройте приложение <b>V2RayTun</b>.\n"
        "4️⃣ Нажмите в правом углу кнопку <b>+</b> → <b>Импортировать из буфера</b>.\n"
        "5️⃣ Сохраните конфигурацию и включите подключение на большую кнопку по центру экрана.\n\n"
        "✅ Готово! VPN активен."
    ),
        "tv": "📺 Инструкция для ТВ приставки:\n1. Подключите устройство...\n2. ...",
        "windows": "💻 Инструкция для Windows:\n1. Запустите программу...\n2. ...",
    }
    # Берём нужный текст
    text = instructions.get(platform, "Инструкция не найдена 😅")

    await call.message.edit_text(text, reply_markup=kb.go_on_main())
    await call.answer()





#Кнопка ИНСТРУКЦИЯ (В РАБОТЕ)
@client.callback_query(F.data == 'instructions')
async def go_support(call:CallbackQuery, session_without_commit: AsyncSession):
    await call.answer("Открываем инструкции...")
    await call.message.delete()
    await call.message.answer(text = f"👨‍💻 Техническая поддержка: \n\n"
                              f"Обязательно приложите скриншот ошибки и настроек из вашего VPN-приложения. \n"
                              f"Это нужно чтобы мы могли понять, какое устройство вы подключаете, и в чем именно проблема."
                              f"💬 Написать в поддержку 👇",
                              reply_markup=kb.support_help_kb()
                              )



#Кнопка саппорт (В РАБОТЕ)
@client.callback_query(F.data == 'support')
async def go_support(call:CallbackQuery, session_without_commit: AsyncSession):
    await call.answer("Связываемся с технической поддержкой...")
    await call.message.delete()
    await call.message.answer(text = f"👨‍💻 Техническая поддержка: \n\n"
                              f"Обязательно приложите скриншот ошибки и настроек из вашего VPN-приложения. \n Это нужно чтобы мы могли понять, какое устройство вы подключаете, и в чем именно проблема."
                              f"💬 Написать в поддержку 👇",
                              reply_markup=kb.support_help_kb()
                              )
    
#Кнопка МОИ ПРОДУКТЫ (В РАБОТЕ) - поменять текст
@client.callback_query(F.data == 'products')
async def go_products(call:CallbackQuery, session_without_commit: AsyncSession):
    await call.message.delete()
    await call.message.answer(text = f"👨‍💻 Комплексные решения для дома: \n\n"
                              f"Все устройства на современном быстром железе и программном обеспечении настроены под ключ и готовы к работе \n \n"
                              f"📺 Приставка включает в себя самый Весь доступный в интернете контент бесплатно и без подписок. Делает из любого телевизора Android Smart TV \n \n"
                              f"🌐 Роутер на OpenWRT с разблокированным возможностями  \n \n"
                              f"💬👇",
                              reply_markup=kb.products()
                              )



#Функция покупки ()
@client.callback_query(F.data.startswith('buy_'))
async def process_about(call:CallbackQuery, session_without_commit:AsyncSession, state:FSMContext):
    await call.message.delete()
    user_info = await UserDAO.find_one_or_none(
        session=session_without_commit,
        filters=TelegramIDModel(telegram_id=call.from_user.id)
    )
    _, product_id, price = call.data.split('_')

    payload = json.dumps({
        "user_id": user_info.telegram_id,
        "product_id": product_id,
        "price": price,
        "days" : None
    })

    await bot.send_invoice(
        chat_id = call.from_user.id,
        title=f'Оплата 👉 {price}₽',
        description=f'Пожалуйста, завершите оплату в размере {price}₽, чтобы получить свой VPN ключ на 30 дней',
        payload = payload,
        provider_token=settings.TEST_PROVIDER_TOKEN,
        currency='RUB',
        prices=[LabeledPrice(
            label=f'Оплата {price}',
            amount = int(price) * 100
        )],
        reply_markup= kb.get_product_buy_kb(price)
    ) 
    
    await call.answer()

#Функция продления (РАБОТАЕТ) по дням, категория стоит в ручную
@client.callback_query(F.data.startswith('update|'))
async def process_about(call:CallbackQuery, session_without_commit:AsyncSession, state:FSMContext):
    await call.message.delete()
    user_info = await UserDAO.find_one_or_none(
        session=session_without_commit,
        filters=TelegramIDModel(telegram_id=call.from_user.id)
    )
    callback_data = call.data.removeprefix("update|")
    
    
    email, price, days = callback_data.split('|')
    email = str(email)
    price = int(price)
    days = int(days)
    # key_email = callback_data.split("|")[0]
    payload = json.dumps({
                        "price": int(price),
                        "days": int(days),
                        "email": email,
                        })

    await bot.send_invoice(
        chat_id = call.from_user.id,
        title=f'Оплата 👉 {price}₽',
        description=f'Пожалуйста, завершите оплату в размере {price}₽, чтобы продлить свой VPN ключ.',
        payload = payload,
        provider_token=settings.TEST_PROVIDER_TOKEN,
        currency='RUB',
        prices=[LabeledPrice(
            label=f'Оплата {price}',
            amount = int(price) * 100
        )],
        reply_markup= kb.get_product_buy_kb(price)
    ) 
    await call.answer()




#РАБОТАЕТ -проверить клавиатуру которая возвращается с ключом)
@client.message(F.successful_payment)
async def successful_paymant(message:Message, session_with_commit:AsyncSession, state:FSMContext, bot:Bot):
    
    category_vpn = 2
    data = json.loads(message.successful_payment.invoice_payload)

    price = int(data.get("price"))
    try:
        days = int(data.get("days"))
    except (TypeError, ValueError):
        days = None
    key_email = str(data.get("email"))
    
   

    if message.successful_payment.total_amount != price * 100:
        await message.edit_text("❌ Ошибка: сумма оплаты не совпадает.")
        return
    
    if days: 
        user_id = int(data.get("email").split("_")[1])
        user = await UserDAO.find_one_or_none(
                                                session=session_with_commit,
                                                filters=TelegramIDModel(telegram_id=user_id)
                                            )
        vpn_data = await UserDAO.update_vpn(session=session_with_commit, user = user, key_email = key_email, days=days)
        expiry_str = vpn_data.expiry_time.strftime("%d.%m.%Y")
        expiry_dt = datetime.strptime(expiry_str, "%d.%m.%Y")
        access_url = vpn_data.access_url
        now = datetime.now()
        delta = expiry_dt - now
        days_left = delta.days
        await message.answer(text=f"✅<b>Благодарим за использование нашего сервиса</b> \n"
                             f"🔁 <b>Ваш ключ продлён на {days} </b>\n"                            
                             f"🗓 Новый срок окончания: {expiry_str}\n"
                             f"⌛ Осталось дней: {days_left}\n",
                            reply_markup=kb.go_on_main())
    else:
        user_id = int(data.get("user_id"))
        user = await UserDAO.find_one_or_none(
                                                session=session_with_commit,
                                                filters=TelegramIDModel(telegram_id=user_id))
        vpn_data = await UserDAO.add_user_payed_vpn(session=session_with_commit, user= user, category_vpn=category_vpn)
        expiry_str = vpn_data.expiry_time.strftime("%d.%m.%Y")
        expiry_dt = datetime.strptime(expiry_str, "%d.%m.%Y")
        access_url = vpn_data.access_url
        now = datetime.now()
        delta = expiry_dt - now
        days_left = delta.days
        await message.answer(text=f"✅<b>Благодарим за использование нашего сервиса</b> \n"
                             f"Ваш ключ: \n"                            
                             f"<code>{access_url}</code> \n" 
                             f"(истекает: {expiry_str}) \n"
                             f"⌛ Осталось дней: {days_left}\n",
                            reply_markup=kb.go_on_main())



#Проверка заказ перед завершением покупки
@client.pre_checkout_query()
async def pre_checkout_query(query:PreCheckoutQuery):
    await query.answer(True)


    #is_vpn = await UserDAO.get_user_vpns(user, vpn)
    # if vpn.max_conn <= vpn.current_conn or is_vpn:
    #     await message.answer('🔴Произошла непредвиденная ошибка обратитесь к @')
    #     await bot.refund_star_payment(message.from_user.id, telegram_paymant_charge_id=message.successful_payment.telegram_payment_charge_id)
    #     return
            # run_time = datetime.now() + timedelta(days=30)
        # scheduler.add_job(
        #     send_message,
        #     trigger='date',
        #     run_date=run_time,
        #     args=[user.telegram_id, vpn_data['id'], vpn.server_ip, vpn.server_hash, vpn.id, vpn.name],
        #     id=f"send_msg_{user.tg_id}_{vpn_data['id']}"
        # )
        # await UserDAO.add_user_vpn(user, vpn.id, 30)



#ПРАВИЛА пользования (В РАБОТЕ)
@client.callback_query(F.data=='rules')
async def rules(call:CallbackQuery, session_without_commit: AsyncSession):
    await call.answer("Открываем правила пользования...")
    rules = f"""📋 Политика конфиденциальности и правила использования

            1️⃣ Конфиденциальность:
            • Мы не собираем персональные данные, кроме технически необходимых (Telegram ID)
            • Telegram ID используется исключительно для идентификации пользователя в сервисе
            • Данные не передаются третьим лицам, кроме случаев, предусмотренных законодательством РФ

            2️⃣ Использование сервиса:
            • Один конфиг предназначен для одного устройства
            • Передача или продажа конфига третьим лицам запрещена
            • Сервис предоставляется только для личного некоммерческого использования

            3️⃣ Запрещено использование для:
            • Нарушения законодательства Российской Федерации
            • Рассылки спама, DDoS-атак или иных действий, мешающих работе сервисов
            • Попыток взлома, мошенничества и иной противоправной деятельности

            4️⃣ Права пользователя:
            • Пользователь может запросить удаление своих данных (Telegram ID)
            • Пользователь может изменять настройки конфигурации в рамках функционала бота
            • Пользователь имеет право на получение технической поддержки

            5️⃣ Ответственность:
            • Администрация вправе ограничить или заблокировать доступ при нарушении правил
            • Средства, использованные для активации сервиса, не возвращаются
            • Информация о блокировках сохраняется для предотвращения повторных нарушений

            6️⃣ Изменения правил:
            • Правила и политика конфиденциальности могут обновляться
            • Уведомления об изменениях публикуются в боте

            ❗️ Используя сервис, вы подтверждаете, что ознакомились и соглашаетесь с настоящими правилами и политикой конфиденциальности.
            📞 По всем вопросам обращайтесь в поддержку.
            """
    await call.message.edit_text(text=rules, reply_markup=kb.support_help_kb())
    


#В РАБОТЕ 
@client.callback_query(F.data.startswith('category_'))
async def choose_country(callback:CallbackQuery, user:User):
    await callback.answer('Выбор региона')
    vpn_category_id = callback.data.split('_'[1])
    await callback.message.edit_text(f'🏳️<b>Выберите регион</b> \n\n Советуем выбирать регион поближе к вам для меньшей задержки',
                                     reply_markup=await kb.get_countries(vpn_category_id, user))

#В РАБОТЕ 
@client.callback_query(F.data=='back_to_choose_category')
async def choose_vpn_category(event: Message | CallbackQuery):
    if isinstance(event, Message):
        await event.answer('🌎<b>Выбор протокола</b> \n\n Outline - ?')

    elif isinstance(event, CallbackQuery):
        await event.answer('Выбор протокола')
        await event.message.edit_text('🌎<b>Выбор протокола</b> \n\n Outline - ?')

#В РАБОТЕ   
@client.callback_query(F.data.startswith('country_'))
async def create_connection(callback:CallbackQuery, user:User, bot:Bot, state:FSMContext):
    vpn_id = callback.data.split('_')[1]
    vpn = await db.get_vpn(vpn_id)
    is_vpn = await db.get_user_vpn(user, vpn)
    if is_vpn:
        await callback.answer('Подписка на данный VPN раннее была оформлена!')
        return
    if vpn.max_conn <= vpn.current_conn:
        await callback.answer('Мест на данный VPN больше нет!')
        return
    if vpn.price == 0:
        if user.trial_until < datetime.now():
            await callback.answer('Пробный период был окончен!')
            return
        vpn_data = await create_access_key(vpn.server_ip, vpn.server_hash)
        scheduler.add_job(
            send_message,
            trigger='date',
            run_date=user.trial_until,
            args=[user.tg_id, vpn_data['id'], vpn.server_ip, vpn.server_hash, vpn.id, vpn.name],
            id= f"{user.tg_id}{vpn_data['id']}"
        )
        await db.add_user_free_vpn(user, vpn_id, 30)
        await callback.message.answer(f'✅<b>Благодарим за использование нашего сервиса!</b>\n\n'
                                      f'Серевер успешно создан!\n<b>Ключ подключения:</b> \n\n'
                                      f'<code>{{vpn_data[\'accessUrl\']}}</code>')
        await callback.answer('Успех!')
    else:
        await state.set_state(st.BuyStars.wait)
        await state.updaet_data(vpn=vpn)
        await callback.message.answer(f'<b>{vpn.name}</b> \n Цена: {vpn.price} RUB в месяц. \n\n')

#В РАБОТЕ 
@client.callback_query(F.data == 'stars')
async def topup_stars(callback: CallbackQuery, state:FSMContext):
    await callback.answer('Произведите оплату')
    data = await state.get_data()
    await callback.message.asnwer_invoice(tittle='Покупка ключа',
    description=f'Покупка ключа {data["vpn"].name} на 30 дней.',
    payload = 'balance',
    currency= 'XTR',
    prices = [LabeledPrice(label='XTR', amount=int(data['vpn'].price / 1))]
    )


            
