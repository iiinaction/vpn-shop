from py3xui import AsyncApi, Client, Api, Inbound
import py3xui
import uuid
from datetime import datetime, timezone, timedelta
from app.dao.user_dao import UserDAO
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
from uuid import uuid4
from pprint import pprint

from dotenv import load_dotenv  
load_dotenv()

print(os.getenv("XUI_USERNAME"))


logger = logging.getLogger(__name__)

async def main():
    api = AsyncApi.from_env()
    await api.login()
        #inbounds = await api.inbound.get_list()
        # print(f"Вывести на дебаг:{type(inbounds)}")
        # # print(f"Вывести на экран входящие подключения: {await api.inbound.get_list()}")
        # inbounds: List[Inbound] = await api.inbound.get_list()
        # print(inbounds)

    # 2 Settings
    tg_id = '433841377'
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

    # if client:
    #     print(f"Found client with ID: {client.id}")  # ⬅️ The actual Client UUID.
    # else:
    #    raise ValueError(f"Client with email {tg_id} not found")

    # cliend_uuid = client.id

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






    # (В РАБОТЕ)!!! Создание ключа на 30 дней)
    async def create_month(api, email) -> None:
        #👉 timestamp через 30 дней (в миллисекундах!)
        expiry_timestamp = (int(time.time()) + 30 * 24 * 60 * 60) * 1000  
  
        new_payed_client = py3xui.Client(
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
        print("Что отправляем в API:", new_payed_client.model_dump(by_alias=True, exclude_defaults=True))
        print("Дата окончания (UTC):", datetime.datetime.utcfromtimestamp(expiry_timestamp / 1000))

        await api.client.add(inbound_id, [new_payed_client])

        inbound = await api.inbound.get_by_id(inbound_id)
        client_uuid = next(c.id for c in inbound.settings.clients if c.email == tg_id)

        return f"vless://{client_uuid}@{host}:{port}?type=tcp&security=tls" 
    
    #create_client_month = await create_month(api=api, email = tg_id)








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
    
    #test_trial = 'test_trial'
    #update_client = await update_month(api=api, email = test_trial)



    async def update_month(api, email) -> None:
        inbound_id = 1
        inbound = await api.inbound.get_by_id(inbound_id)
        client = next((c for c in inbound.settings.clients if c.email == email), None)

        if not client:
            raise ValueError(f"Клиент {email} не найден")

        # === DEBUG INFO START ===
        print("\n🔎 DEBUG INFO:")
        print("--------------------------------------------------")
        print(f"➡️ client.id: {getattr(client, 'id', None)}")
        print(f"➡️ client.email: {getattr(client, 'email', None)}")
        print(f"➡️ client.inbound_id: {getattr(client, 'inbound_id', None)}")
        print(f"➡️ client.inboundd_id: {getattr(client, 'inboundd_id', None)}")
        print("\n📦 client.model_dump(by_alias=True):")
        try:
            pprint(client.model_dump(by_alias=True))  # pydantic v2
        except Exception:
            pprint(client.dict(by_alias=True))        # fallback pydantic v1
        print("--------------------------------------------------")

        print("\n🧩 Проверяем alias модели Client:")
        for field_name, field in Client.model_fields.items():
            if "inbound" in field_name:
                print(f"{field_name} -> alias: {field.alias}")
        print("--------------------------------------------------")
        # === DEBUG INFO END ===

        # Обновляем срок
        now_ms = int(time.time()) * 1000
        month_ms = 30 * 24 * 60 * 60 * 1000
        if client.expiry_time < now_ms:
            client.expiry_time = now_ms + month_ms
        else:
            client.expiry_time += month_ms

        # Исправляем возможную опечатку inboundd_id → inbound_id
        if hasattr(client, "inboundd_id"):
            client.inbound_id = inbound_id
            delattr(client, "inboundd_id")
            print("⚙️ Исправлено: заменён inboundd_id → inbound_id")

        print("\n🚀 Перед отправкой на сервер:")
        pprint(client.model_dump(by_alias=True))
        print("--------------------------------------------------\n")

        client.inbound_id = 1
        # Отправляем обновление
        await api.client.update(client.id, client)
        print(f"✅ Клиент {email} продлён на 30 дней")

    test_trial = 'test_trial'
    update_client = await update_month(api=api, email = test_trial)




    #ТЕСТ на получение ВПНов пользователя 
    async with async_session_maker() as session:
        
        user = await session.get(User, 1)
        vpn_info = await UserDAO.get_user_vpns(session, user.id)
        # print(f"У пользователя: {user.id} Вот такие ключи:{vpn_info}")
        for vpn in vpn_info:
            print(f"URL: {vpn['access_url']}  истекает: {vpn['expiry_time']}")
    
       
  



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

    

    
    

if __name__ == "__main__":
    asyncio.run(main())

