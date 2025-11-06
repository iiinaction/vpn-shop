from py3xui import AsyncApi, Client, Api, Inbound
import py3xui
import uuid
from datetime import datetime, timezone, timedelta
# from app.dao.user_dao import UserDAO, get_key_info,  VPNDAO
from app.config import Settings, XUIConfig
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
from pprint import pprint
# from app.bot import api
from dotenv import load_dotenv  

#Подгружаем настройки
xui_config = XUIConfig()

#Логи
logger = logging.getLogger(__name__)

#РАБОЧИЙ !!! ВЫДАТЬ ТРИАЛ НА 7 ДНЕЙ
async def create_trial(api, tg_id):
    expiry_timestamp = (int(time.time()) + 7 * 24 * 60 * 60) * 1000 
    inbound_id=xui_config.INBOUND_ID 
    new_trial_client = py3xui.Client(
            id=str(uuid.uuid4()),
            email=tg_id,
            expiryTime=expiry_timestamp,
            inboundId=inbound_id,
            enable=True,
            flow=xui_config.FLOW
        )
    await api.client.add(inbound_id, [new_trial_client])
    inbound = await api.inbound.get_by_id(inbound_id)
    client_uuid = next(c.id for c in inbound.settings.clients if c.email == tg_id)
    return {
          "id": new_trial_client.id,
          "email": tg_id,
          "expiryTime":expiry_timestamp,
          "inboundId": inbound_id,
          "enable": True,
          "flow": xui_config.FLOW,
          "access_url": f"vless://{client_uuid}@{xui_config.URL}:{xui_config.PORT}{xui_config.SETTINGS}"  
    }   
#data = await create_trial(api=api, tg_id = "test_trial", host = host, port = port)
#print(data["assecc_url"]) 


# (В РАБОТЕ)!!! Создание ключа на 30 дней)
async def create_month(api, tg_id ) -> None:
    #👉 timestamp через 30 дней (в миллисекундах!)
    expiry_timestamp = (int(time.time()) + 30 * 24 * 60 * 60) * 1000  
    inbound_id = 1
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

    return {
          "id": new_payed_client.id,
          "email": tg_id,
          "expiryTime":expiry_timestamp,
          "inboundId": inbound_id,
          "enable": True,
          "flow": xui_config.FLOW,
          "access_url": f"vless://{client_uuid}@{xui_config.URL}:{xui_config.PORT}{xui_config.SETTINGS}" }

#create_client_month = await create_month(api=api, email = tg_id)


# РАБОЧИЙ!!! обновление срока действия ключа ()
async def update_month(api, email, days) -> None:
    # Берём inbound
    inbound_id = 1
    inbound = await api.inbound.get_by_id(inbound_id)
    client = next((c for c in inbound.settings.clients if c.email == email), None)
        
    if not client:
            raise ValueError(f"Клиент {email} не найден")
    

    now_ms = int(time.time()) * 1000
    month_ms = int(days) * 24 * 60 * 60 * 1000

    if client.expiry_time < now_ms:
            client.expiry_time = now_ms + month_ms
    else:
            client.expiry_time +=month_ms

    client.inbound_id = inbound_id
    await api.client.update(client.id, client)
    
    return             {
          "id": client.id,
          "email": email,
          "expiryTime":client.expiry_time,
          "inboundId": inbound_id,
          "enable": True,
          "flow": xui_config.FLOW,
          "access_url": f"vless://{client.id}@{xui_config.URL}:{xui_config.PORT}{xui_config.SETTINGS}" 
          }
    #print(f"✅ Клиент {email} продлён на {int(month_ms / 1000 / 60 /60 /24)} дней")  - так работает

 

# 5 Get avalible url
def make_vless_link(host: str, port: int, client_uuid: str, settings:str) -> str:
    return f"{'vless'}://{client_uuid}@{host}:{port}{settings}"
    

#Работа с API Outline
# client = OutlineVPN(api_url=settings.API_URL, cert_sha256=settings.CERT_SHA)
# def create_access_key(key_id:str = None, name: str = None, data_limit_gb: float = None):
#     return client.create_key(key_id = key_id, name=name, data_limit=gb_to_bytes(data_limit_gb))
