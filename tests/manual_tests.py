import os
import sys

# Добавляем корневую директорию проекта в sys.path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from app.dao.database import async_session_maker  # фабрика сессий
from app.dao.user_dao import UserDAO, get_key_info,  VPNDAO
from app.models.models import User
from app.dao.schemas import VPNCreate
from datetime import datetime, timezone, timedelta

async def main():
    async with async_session_maker() as session:
        trial_until = datetime.now(timezone.utc) + timedelta(days=7)
        # print(trial_until) работает!

        user = await UserDAO.add_user_free_vpn(session, user = 433841377, category_vpn= 3, until=trial_until)

        print("Пользователь добавлен:", user)

        result = await UserDAO.get_all_users(session)
        print(f'Все пользователи{result}')

if __name__ == "__main__":
    asyncio.run(main())
    
