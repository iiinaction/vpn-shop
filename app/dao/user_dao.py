from sqlalchemy.orm import selectinload
from app.models.models import User, VPNCategory, VPN, UserVPN
from sqlalchemy import select, update, delete, desc, join, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import datetime
from typing import Optional, List, Dict
from uuid import uuid4
from pprint import pprint
from app.dao.base import BaseDAO

from apscheduler.triggers.date import DateTrigger
from app.bot import scheduler
from app.apsched import send_message, send_notification

from app.services.xui import create_trial, update_month
from app.bot import api


from app.services.xui import create_trial, create_month, update_month
from app.schemas.schemas import VPNCreate

# from app.outline_api import create_access_key, get_key_info



class VPNDAO(BaseDAO[VPN]):
     model = VPN

class VPNDAOCategory(BaseDAO[VPNCategory]):
     model = VPNCategory

class UserDAO(BaseDAO[User]):
    model = User
    #Создание триала для клиента

    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_user(self, telegram_id: int, name:str)->User:
            user = select(User).where(User.telegram_id==telegram_id)
            result = await self.session.execute(user)
            user = result.scalar_one_or_none()

            if not user:
                days_later = datetime.datetime.now() + datetime.timedelta(days=7)
                user = User(
                    telegram_id = telegram_id,
                    username = name, 
                    trial_until = days_later)
                self.session.add(user)
                await self.session.commit()

            return user
    
    @classmethod
    async def get_purchase_statistic(cls, session:AsyncSession, telegram_id: int) -> Optional[Dict[str, int]]:
         try:
              #Запрос для получения общего числа покупок и общей суммы
              result = await session.execute(
                   select(
                        func.count(VPN.id).label("total_purchases"),
                        func.sum(VPNCategory.price).label("total_amount")
                   )
                   .select_from(User)
                   .join(UserVPN, UserVPN.user_id == User.id)
                   .join(VPN, VPN.id == UserVPN.vpn_id)
                   .join(VPN.category)
                   .filter(User.telegram_id==telegram_id)
              )
              stats = result.one_or_none()

              if stats is None:
                   return None
              total_purchases, total_amount = stats
              
              return {
                   'total_purchases' : total_purchases,
                   'total_amount' : total_amount or 0
              }
         
         except SQLAlchemyError as e:
              #Обработка ошибок при работе с бд
              print(f'Ошибка получения статистики {e}')
              return None
        
        
        
        
    
    # Выбрать VPN по id   
    @classmethod
    async def get_vpn(self, vpn_id):
         return self.session.scalar(select(VPN).where(VPN.id == vpn_id))
    

    #Создать бесплатный VPN
    @classmethod
    async def create_trial(cls, session:AsyncSession, user:User, category_vpn:int, until:datetime):
        # Создаем ключ у сервера
        raw_key = create_trial(api=api, tg_id=f'trial_{user}')  # - метод для outline
        #Записываем его в таблицу vpns
        vpn_data = VPNCreate.model_validate(raw_key)
        
        vpn_obj = await VPNDAO.add(session, vpn_data, category_id=category_vpn)

        session.add(
                UserVPN(user_id=user.id, 
                        vpn_id=vpn_obj.id,
                        until=until,
                        status =True)
                        )       
        await session.commit()   

    #Добавить бесплатный VPN
    @classmethod
    async def add_user_free_vpn(cls, session:AsyncSession, user:User, category_vpn:int, until:datetime):
            # Создаем ключ у сервера
            await api.login()
            raw_key = await create_trial(api, tg_id=f'trial_{user.telegram_id}')  
            #Записываем его в таблицу vpns
            vpn_data = VPNCreate.model_validate(raw_key)
            vpn_obj = await VPNDAO.add(session, vpn_data, category_id=category_vpn)

            session.add(
                 UserVPN(user_id=user.id, 
                         vpn_id=vpn_obj.id,
                         until=until,
                         status =True)
                         )
            stmt = (
                 update(User)
                 .where(User.telegram_id == user.id)
                 .values(is_trial_used=True)
            )

            # Обновляем trial_until у самого объекта user
            user.trial_until = vpn_obj.expiry_time 
            # vpn_obj.current_conn += 1            
            await session.commit()
            return vpn_data


    #Добавить купленный VPN (РАБОТАЕТ)
    @classmethod
    async def add_user_payed_vpn(cls, session:AsyncSession, user:User, category_vpn:int):
        # Создаем ключ у сервера
        await api.login()
        raw_key = await create_month(api, tg_id=f'payed_{user.telegram_id}_{uuid4().hex[:8]}')  
        #Записываем его в таблицу vpns
        print(raw_key)
        vpn_data = VPNCreate.model_validate(raw_key)
        vpn_obj = await VPNDAO.add(session, vpn_data, category_id=category_vpn)
        
        session.add(
                UserVPN(user_id=user.id, 
                        vpn_id=vpn_obj.id,
                        until=vpn_obj.expiry_time,
                        status =True)
                        )
        # Обновляем trial_until у самого объекта user
        #user.trial_until = vpn_obj.expiry_time 
        # vpn_obj.current_conn += 1            
        await session.commit()
        return vpn_data
    

        #Добавить купленный VPN (РАБОТАЕТ)
    
    
    #Продлить купленный VPN (РАБОТАЕТ)
    @classmethod
    async def update_vpn (cls, session:AsyncSession, user:User, key_email, days=int):
        # Создаем ключ у сервера
        await api.login()
        raw_key = await update_month(api=api, email=key_email, days=days)
        #Записываем его в таблицу vpns
        print("🔑 Рав ключи:")
        pprint(raw_key)
        category_vpn = 1

        # Далее валидируем данные и записываем в таблицу методом update
        vpn_data = VPNCreate.model_validate(raw_key)
        
        vpn_obj = await VPNDAO.update(session, obj_id=key_email, values=vpn_data, category_id=category_vpn)           
        await session.commit()
        return vpn_data




    #Получить ВПНы пользователя 
    @classmethod
    async def get_user_vpns(cls, session, user_id: int):
        """Возвращает объект UserVPN для конкретного пользователя и VPN, если он существует."""
        result = await session.execute(
             select(VPN.access_url, VPN.expiry_time)
             .join(UserVPN, UserVPN.vpn_id== VPN.id)
             .join(User, User.id == UserVPN.user_id)
             .where(User.telegram_id == user_id)
             )
        return [{"access_url": access_url, "expiry_time": expiry_time} 
                for access_url, expiry_time in result.all()
                ]


    # Показать пользователя
    @classmethod
    async def get_all_users(cls, session:AsyncSession) -> list[User]:
            result = await session.scalars(select(User))
            users = result.all()
            return users

    #Показать категории
    async def get_vpn_categories(self):
            result = self.session.scalar(select(VPNCategory))
            categories = result.all()
            return categories


    async def get_countries(self, vpn_category_id, user):
        """
        Получить список VPN-серверов для заданной категории,
        которые доступны для подключения.

        Args:
            vpn_category_id (int): ID категории VPN.
            user (User): Объект пользователя (пока не используется).

        Returns:
            List[VPN]: Список объектов VPN, отсортированных по цене (убывание).

        TODO:
            - В будущем использовать параметр `user` для фильтрации серверов
            по региону, подписке или другим правам доступа пользователя.
            - Добавить кэширование результатов для оптимизации.
        """

        result = self.session.scalars(
                select(VPN).where(and_(
                    VPN.category_id == vpn_category_id,
                    VPN.price > 0,
                    VPN.current_conn < VPN.max_conn
                )).order_by(VPN.price.desc())
            )
        countries = result.all()
        return countries




    #Добавить пользователю VPN
    async def add_user_vpn(self, user, vpn_id, days):
        """
        Назначает пользователю VPN на указанное число дней и увеличивает счётчик подключений.
        """
        days_until = datetime.datetime.now() + datetime.timedelta(days=days)
        self.session.add(UserVPN(user_id = user.id, vpn_id = vpn_id, until = days_until))
        vpn = await self.session.scalar(select(VPN).where(VPN.id == vpn_id))
        if vpn is None:
            raise ValueError(f"VPN c id:{vpn_id} не найден!")
        vpn.current_conn += 1
        await self.session.commit()

    #Обновить статус VPN у пользователя ДЛЯ  ТРИАЛА (ПЕРЕДЕЛАТЬ)   (В РААААААБОТЕЕЕ!!!)
    @classmethod
    async def delete_user_vpn(cls, session:AsyncSession, tg_id: int, email: int) -> None:
        """
        Args:
            tg_id (int): Telegram ID пользователя.
            vpn_id (int): ID VPN сервера.
        """
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if user is None:
            raise ValueError(f'User с id{tg_id} не найден!')
        vpn = await session.scalar(select(VPN).where(VPN.email == email ))
        if vpn is None:
            raise ValueError(f'VPN {email} не найден!')

        await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(is_trial_used=False)
            )
        
        await session.delete(vpn)
        await session.commit()



    async def get_sendall_users(self, client_type:str) -> list[int]:
        """
    Возвращает список tg_id пользователей:
    - если client_type == 'free' — у которых нет платных VPN;
    - если client_type == 'paid' — у которых есть хотя бы один платный VPN.
        """
        result = await self.session.execute(
            select(User).options(
                selectinload(User.vpns).selectinload(UserVPN.vpn)
            )
        )
        users = result.scalars().all()
        tg_ids = []

        for user in users:
            has_paid = any(user_vpn.vpn.price > 0 for user_vpn in user.vpns)
        if client_type == 'free' and not has_paid:
            tg_ids.append(user.tg_id)
        elif client_type == 'paid' and has_paid:
            tg_ids.append(user.tg_id)
        return tg_ids
        
