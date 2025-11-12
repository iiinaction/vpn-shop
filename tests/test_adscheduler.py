from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.redis import RedisJobStore
from datetime import datetime, timedelta
import asyncio, logging
from loguru import logger
from app.bot import bot


logging.basicConfig(level=logging.INFO)

async def send_notification(user, vpn_name):
    try:
        await bot.send_message(user, f'❤️‍🩹Осталось 10 секунд дня до окончания действия вашего VPN: {vpn_name} !')
        await bot.session.close()
    except Exception as e:
        logger.exception(f'Не удалость отправить сообщение пользователю{user}: {e}')


async def main():
    # подключаем Redis как хранилище задач
    jobstores = {
        'default': RedisJobStore(
            host='localhost',
            port=6379,
            db=0
        )
    }

    scheduler = AsyncIOScheduler(jobstores=jobstores)
    scheduler.start()

    # добавляем задачу через 10 секунд
    run_date = datetime.now() + timedelta(seconds=10)

    scheduler.add_job(
        func=send_notification,
        trigger=DateTrigger(run_date=run_date),
        kwargs={'user': 433841377, 'vpn_name': 'vpn@demo.com'},
        id='redis_test_task',
        replace_existing=True
    )

    

    print("✅ Задача добавлена в RedisJobStore")
    await asyncio.sleep(15)


asyncio.run(main())
