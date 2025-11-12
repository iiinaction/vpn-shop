#from app.outline_api import delete_access_key
from app.dao.database import async_session_maker
from app.bot import api
from loguru import logger

from app.bot import bot

# ДЛЯ ПЕРВОГО INBOUND УДАЛЕНИЕ
async def send_message(user_id: int, email: str):
    try:
        await bot.send_message(user_id, f'❤️‍🩹Закончилось действие вашего VPN ключа: {email}')
    except Exception as e:
        logger.exception(f'Не удалость отправить сообщение пользователю{user_id}: {e}')
    #await delete_access_key(key)
    client = await api.client.get_by_email(email=email)
    print(client)
    if client:
        inbound = await api.inbound.get_by_id(inbound_id=1)
        client_uuid = next(c.id for c in inbound.settings.clients if c.email == email)
        result = await api.client.delete(inbound_id=1, client_uuid=client_uuid)
    else:
        print(f"Клиент с email {email} не найден в py3xui")
    async with async_session_maker() as session:
        from app.dao.user_dao import UserDAO
        await UserDAO.delete_user_vpn(session, tg_id=user_id, email=email)
        print(f"Удалён {email} у пользователя {user_id}")

        await session.commit()



async def send_notification(user, vpn_name):
    try:
        await bot.send_message(user, f'❤️‍🩹Осталось 3 дня до окончания действия вашего VPN ключа: {vpn_name} !')
    except Exception as e:
        logger.exception(f'Не удалость отправить сообщение пользователю{user}: {e}')

    