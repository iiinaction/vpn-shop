from py3xui import AsyncApi, Client, Api, Inbound
import py3xui
import uuid
from datetime import datetime, timezone, timedelta
# from app.dao.user_dao import UserDAO, get_key_info,  VPNDAO
from app.config import Settings
import logging
from app.time import days_to_timestamp
import asyncio
from typing import List

import time
from urllib.parse import parse_qs, urljoin, urlparse

from app.dao.database import async_session_maker 
from app.models.models import User
import os

import time
import datetime
import json

from dotenv import load_dotenv  
load_dotenv()

print(os.getenv("XUI_USERNAME"))


logger = logging.getLogger(__name__)

async def main():
    print("Вывести на экран XUI_HOST =", os.getenv("XUI_HOST"))
    api = AsyncApi.from_env()
    await api.login()
        #inbounds = await api.inbound.get_list()
        # print(f"Вывести на дебаг:{type(inbounds)}")
        # # print(f"Вывести на экран входящие подключения: {await api.inbound.get_list()}")
        # inbounds: List[Inbound] = await api.inbound.get_list()
        # print(inbounds)

    # 2 Settings
    tg_id = 'Elena-Yunak'
    inbound_id = 1
    host = os.getenv("XUI_HOST")
    url=os.getenv("XUI_URL")
    port=os.getenv("XUI_PORT")
    # path=os.getenv("SUBSCRIPTION_PATH")
    settings = '?type=tcp&security=tls&fp=chrome&alpn=http%2F1.1&flow=xtls-rprx-vision'
    
    
    # 3 Get the inbound
    client = None
    inbound = await api.inbound.get_by_id(inbound_id)
    #print(f"Inbound has {len(inbound.settings.clients)} clients")
    
    # 4 Find the needed client in the inbound 
    client = None
    for c in inbound.settings.clients:
        if c.email == tg_id:
            client = c
            break

    if client:
        print(f"Found client with ID: {client.id}")  # ⬅️ The actual Client UUID.
    else:
        raise ValueError(f"Client with email {tg_id} not found")

    cliend_uuid = client.id

    # 5 Get avalible url
    def make_vless_link(host: str, port: int, client_uuid: str, settings:str) -> str:

        return f"{'vless'}://{client_uuid}@{host}:{port}{settings}"
    # link = make_vless_link(host = host, port = port, client_uuid= cliend_uuid, settings= settings)
    # print(link)
    
    # 6 Create Trial url
    async def create_trial2(api, tg_id, host: str, port = port, settings= settings):
        expiry_timestamp = int(time.time()) + 7 * 24 * 60 * 60  # 7 дней в секундах
        inbound_id = 1
        new_trial_client = py3xui.Client(
            id=str(uuid.uuid4()), 
            email=tg_id, 
            expiryTime=int(time.time()) + 7 * 24 * 60 * 60,
            inboundId=inbound_id,
            enable=True
            )
        
        # проверим, что реально уйдёт в API
        print("Что отправляем в API:", new_trial_client.model_dump(by_alias=True, exclude_defaults=True))

        await api.client.add(inbound_id, [new_trial_client])

        inbound = await api.inbound.get_by_id(inbound_id)
        cliend_uuid = next(c.id for c in inbound.settings.clients if c.email == tg_id)

  
        print("Что отправляем в API:", new_trial_client.model_dump(by_alias=True))
        print("Дата окончания (UTC):", datetime.datetime.utcfromtimestamp(expiry_timestamp))
        return f"vless://{cliend_uuid}@{host}:{port}?type=tcp&security=tls"
    
    #link = await create_trial2(api=api, tg_id = "test_trial", host = host, port = port, settings= settings)

    #РАБОЧИЙ !!! ВЫДАТЬ ТРИАЛ НА 7 ДНЕЙ
    async def create_trial(api, tg_id, host: str, port: int, inbound_id: int = 1):
    # 👉 timestamp через 7 дней (в миллисекундах!)
        expiry_timestamp = (int(time.time()) + 1 * 1 * 5 * 60) * 1000  

        new_trial_client = py3xui.Client(
            id=str(uuid.uuid4()),
            email=tg_id,
            expiryTime=expiry_timestamp,
            inboundId=inbound_id,
            enable=True,
            total=10 * 1024 * 1024 * 1024,  # лимит трафика (10 ГБ для теста)
            reset=0,
            flow="xtls-rprx-vision"
        )

        # печать того, что реально уходит в API
        print("Что отправляем в API:", new_trial_client.model_dump(by_alias=True, exclude_defaults=True))
        print("Дата окончания (UTC):", datetime.datetime.utcfromtimestamp(expiry_timestamp / 1000))

        await api.client.add(inbound_id, [new_trial_client])

        inbound = await api.inbound.get_by_id(inbound_id)
        client_uuid = next(c.id for c in inbound.settings.clients if c.email == tg_id)

        return f"vless://{client_uuid}@{host}:{port}?type=tcp&security=tls"   
        
    #link = await create_trial(api=api, tg_id = "test_trial", host = host, port = port)

    # РАБОЧИЙ!!! обновление срока действия ключа (установка на 30 дней)
    async def update_month(api, email) -> None:
       

        # Берём inbound
        inbound_id = 1
        inbound = await api.inbound.get_by_id(inbound_id)
        # Ищем клиента по email
        client = next((c for c in inbound.settings.clients if c.email == email), None)
        
        if not client:
            raise ValueError(f"Клиент {email} не найден")
        
        now_ms = int(time.time()) * 1000
        month_ms = 30 * 24 * 60 * 60 * 1000

        if client.expiry_time < now_ms:
            client.expiry_time = now_ms + month_ms
        else:
            client.expiry_time +=month_ms

        await api.client.update(client.id, client)
        
        print(f"✅ Клиент {email} продлён на {int(month_ms / 1000 / 60 /60 /24)} дней")
    
    update_client = await update_month(api=api, email = "test_trial")



  



    async def get_client_expiry(api, inbound_id: int, tg_id: str):
        # получаем inbound
        inbound = await api.inbound.get_by_id(inbound_id)

        # ищем клиента по email
        client = next((c for c in inbound.settings.clients if c.email == tg_id), None)
        if not client:
            raise ValueError(f"Клиент с email={tg_id} не найден в inbound {inbound_id}")

        # достаём expiryTime
        expiry_ts = getattr(client, "expiryTime", None)
        if not expiry_ts or expiry_ts == 0:
            return f"У клиента {tg_id} нет ограничения по времени (∞)"

        expiry_date = datetime.datetime.utcfromtimestamp(expiry_ts)
        return f"Клиент {tg_id} истекает {expiry_date} UTC"

    # expiry_info = await get_client_expiry(api, inbound_id=1, tg_id="test_trial")
    # print(expiry_info)
    

    async def debug_inbounds(api):
        inbounds = await api.inbound.get_by_id(1)
        # посмотрим на структуру первого inbound
        clients = inbounds.settings.clients
        for client in clients:
            print(json.dumps(client.model_dump(by_alias=True), indent=2, ensure_ascii=False))

        #print(json.dumps(inbounds[0].model_dump(by_alias=True), indent=2, ensure_ascii=False))
    
    # await debug_inbounds(api)

    

    

    # async def get_key(user) -> str | None:
    #     user = tg_id 

    #         # await User.get(session=session, tg_id=user.tg_id)

    #     # if not user.server_id:
    #     #     logger.debug(f"Server ID for user {user.tg_id} not found.")
    #     #     return None

    #     subscription = extract_base_url(
    #         url=user.server.host,
    #         port=self.config.xui.SUBSCRIPTION_PORT,
    #         path=self.config.xui.SUBSCRIPTION_PATH,
    #     )
    #     key = f"{subscription}{user.vpn_id}"
    #     logger.debug(f"Fetched key for {user.tg_id}: {key}.")
        # return key
    
    #Формирование ссылки ключа
    def extract_base_url(url: str, port: int, path: str) -> str:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.hostname}:{port}"
        return urljoin(base_url, path)
    

if __name__ == "__main__":
    asyncio.run(main())


# async def main():
#     async with async_session_maker() as session:
#         trial_until = datetime.now(timezone.utc) + timedelta(days=7)
        

#         user = await UserDAO.add_user_free_vpn(session, user = 433841377, category_vpn= 3, until=trial_until)

#         print("Пользователь добавлен:", user)

#         result = await UserDAO.get_all_users(session)
#         print(f'Все пользователи{result}')




# class VPNService:
#     def __init__(
#         self,
#         config: Settings,
#         session: async_session_maker,
#         # server_pool_service: ServerPoolService,
#     ) -> None:
#         self.config = config
#         self.session = session
#         # self.server_pool_service = server_pool_service
#         logger.info("VPN Service initialized.")

#     async def create_client(
#         self,
#         user: User,
#         devices: int,
#         duration: int,
#         enable: bool = True,
#         flow: str = "xtls-rprx-vision",
#         total_gb: int = 0,
#         inbound_id: int = 1,
#     ) -> bool:
#         logger.info(f"Creating new client {user.tg_id} | {devices} devices {duration} days.")

#         await self.server_pool_service.assign_server_to_user(user)
#         connection = await self.server_pool_service.get_connection(user)

#         if not connection:
#             return False

#         new_client = Client(
#             email=str(user.tg_id),
#             enable=enable,
#             id=user.vpn_id,
#             expiry_time=days_to_timestamp(duration),
#             flow=flow,
#             limit_ip=devices,
#             sub_id=user.vpn_id,
#             total_gb=total_gb,
#             )
#         inbound_id = await self.server_pool_service.get_inbound_id(connection.api)


#         try:
#             await connection.api.client.add(inbound_id=inbound_id, clients=[new_client])
#             logger.info(f"Successfully created client for {user.tg_id}")
#             return True
#         except Exception as exception:
#             logger.error(f"Error creating client for {user.tg_id}: {exception}")
#             return False
        

