from typing import TypeVar, Generic, Any
from app.dao.database import Base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from loguru import logger
from app.models.models import User, UserVPN

T = TypeVar("T", bound = Base)

class BaseDAO(Generic[T]):
    model: type[T]

    @classmethod
    async def find_one_or_none(cls, session:AsyncSession, filters:BaseModel):
        # найти одну запись по фильтрам
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Поиск по одной записи {cls.model.__name__} по фильтрам {filter_dict}")
        
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f"Запись найдена по фильтрам {filter_dict}")
            else:
                logger.info(f"Запись не найдена по фильтрам{filter_dict}")
            return record
        
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиск записи по фильтрам {filter_dict}: {e}")
            raise
    
    @classmethod
    async def add(cls, session:AsyncSession, values:BaseModel, **extra_fields):
        #Добавить одну запись
        values_dict = values.model_dump(exclude_unset= True)
        values_dict.update(extra_fields)                                                # Добавляем дополнительные поля
        logger_info = (f"Добавление записи{cls.model.__name__} с параметрами {values_dict}")
        print(f"Добавляем в БД: {values_dict}")
        new_instance = cls.model(**values_dict)
        
        session.add(new_instance)
        try:
            await session.flush()
            logger.info(f"Запись {cls.model.__name__} успешно добавлена.")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка для добавления записи: {e}")
            raise e
        return new_instance
    
    @classmethod
    async def find_all(cls, session: AsyncSession, filters:BaseModel | None=None):
        #Найти все записи по фильтрам
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        logger.info(f"Поиск всех записей {cls.model.__name__} по фильтрам:{filter_dict}")
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            records = result.scalars().all()
            logger.info(f"Найдено {len(records)} записей.")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске всех записей по фильтрам {filter_dict}: {e}")
            raise

    @classmethod
    async def find_all_by_telegram_id(cls, session: AsyncSession, telegram_id: int):
        try:
            stmt = (
                select(cls.model)
                .join(UserVPN, UserVPN.vpn_id == cls.model.id)
                .join(User, User.id == UserVPN.user_id)
                .where(User.telegram_id == telegram_id)
            )
            result = await session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске всех записей по фильтру telegram id = {telegram_id}: {e}")
            raise

    
    # Обновляем таблицы в SQL
    @classmethod
    async def update(cls, session: AsyncSession, obj_id: str, values: BaseModel, **extra_fields):
        
        # Преобразуем данные
        values_dict = values.model_dump(exclude_unset=True)
        values_dict.update(extra_fields)
        print(f"Обновление записи {cls.model.__name__} с данными {values_dict}")

        try:
            filter_field = "email"

            # Выполняем запрос на поиск записи по колонке и находим строку
            stmt = select(cls.model).where(getattr(cls.model, filter_field) == obj_id)
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if not instance:
                logger.warning(f"Запись {cls.model.__name__} с {filter_field}={obj_id} не найдена.")
                return None

            # Обновляем поля
            for key, value in values_dict.items():
                setattr(instance, key, value)

            await session.flush()
            logger.info(f"Запись {cls.model.__name__} ({filter_field}={obj_id}) успешно обновлена.")
            return instance

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при обновлении {cls.model.__name__}: {e}")
            raise e
        