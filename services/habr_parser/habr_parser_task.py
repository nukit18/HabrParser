import asyncio

from django.db.models import Q
from django.utils import timezone

from habr_parser_info.models import HabrHubs, StatusChoices
from services.habr_parser.habr_parser import ParseHabrHubManager


async def start_parse_hub(one_hub: HabrHubs):
    """Функция для запуска парсинга параллельно основному потоку"""
    async with ParseHabrHubManager(one_hub) as habr_parse_manager:
        await habr_parse_manager.fetch_links_from_hubs()


async def start_parse_hubs_by_interval():
    """Задача планироващика, которая запускает Хабы на сбор, у которых время с последней проверки больше, чем заданный
    интервал"""
    now = timezone.now()
    expired_hubs = HabrHubs.objects.filter(Q(next_check_at__lt=now) | Q(next_check_at__isnull=True)
                                           ).exclude(status=StatusChoices.AT_WORK)

    tasks = [asyncio.create_task(start_parse_hub(one_hub)) async for one_hub in expired_hubs]
