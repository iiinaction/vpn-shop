#from app.outline_api import delete_access_key
from app.dao.user_dao import UserDAO
from loguru import logger

from app.bot import bot

async def send_message(user: int, key: str, vpn_id:int, vpn_name:str):
    try:
        await bot.send_message(user, f'❤️‍🩹Закончилось действие вашего VPN: {vpn_name}')
    except Exception as e:
        logger.exception(f'Не удалость отправить сообщение пользователю{user}: {e}')
    #await delete_access_key(key)
    await UserDAO.delete_user_vpn(user, vpn_id)


async def send_notification(user, vpn_name):
    try:
        await bot.send_message(user, f'❤️‍🩹Осталось 3 дня до окончания действия вашего VPN: {vpn_name} !')
    except Exception as e:
        logger.exception(f'Не удалость отправить сообщение пользователю{user}: {e}')

    