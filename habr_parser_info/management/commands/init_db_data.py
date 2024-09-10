from django.core.management.base import BaseCommand
from habr_parser_info.models import HabrHubs


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми хабами'

    def handle(self, *args, **kwargs):
        HabrHubs.objects.get_or_create(id=1, name='Test Career', hub_link='https://habr.com/ru/hubs/career/articles/',
                                       check_interval_secs=60, count_links_per_page=50, max_pages=50)
        HabrHubs.objects.get_or_create(id=2, name='Test Popular Since',
                                       hub_link='https://habr.com/ru/hubs/popular_science/articles/',
                                       check_interval_secs=30, count_links_per_page=50, max_pages=50)
        HabrHubs.objects.get_or_create(id=3, name='Test IT-Companies',
                                       hub_link='https://habr.com/ru/hubs/itcompanies/articles/',
                                       check_interval_secs=30, count_links_per_page=50, max_pages=50)
        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена'))
