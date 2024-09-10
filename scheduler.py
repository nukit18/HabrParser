import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'habr_parser_app.settings')
django.setup()

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.habr_parser.habr_parser_task import start_parse_hubs_by_interval


async def main():
    scheduler = AsyncIOScheduler()

    scheduler.add_job(start_parse_hubs_by_interval, 'interval', seconds=5)

    scheduler.start()
    # чтобы процесс не завершался
    while True:
        await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
