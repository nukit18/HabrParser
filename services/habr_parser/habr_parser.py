import asyncio
import logging
import random
import re
from datetime import datetime, timedelta

import aiohttp as aiohttp
from aiohttp import ClientConnectionError, ClientTimeout
from django.utils import timezone

from habr_parser_info.models import HabrLinks, StatusChoices, HabrHubs


class ParseHabrHubManager:
    """Класс менеджера для парсинга ссылок для заданного Хаба"""
    def __init__(self, habr_hub: HabrHubs):
        """:param habr_hub: HabrHubs - объект HabrHubs по которому запускается сбор

        new_habr_hub_status - какой статус поставить хабу после сбора

        count_links_per_page  количество ссылок на одной страницу (для апи хабра, query - page = ???)

        task_queue - очередь задач

        max_threads - количество паралльельных задач

        results - результаты

        batch_size  - с каким шагом записывать данные в базу

        max_pages - максимальное количество страниц для сбора
        """
        self.habr_hub = habr_hub
        self.new_habr_hub_status = StatusChoices.PROCESSED  # какой статус поставить хабу после сбора
        self.count_links_per_page = habr_hub.count_links_per_page  # количество ссылок на одной страницу (для апи хабра)
        self.task_queue = asyncio.Queue()
        self.max_threads = habr_hub.max_threads
        self.results = []
        self.batch_size = habr_hub.batch_size
        self.max_pages = habr_hub.max_pages

    async def __aenter__(self):
        # Отмечаем статус Хаба как "в работе"
        self.habr_hub.status = StatusChoices.AT_WORK
        await self.habr_hub.asave()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.habr_hub.status = self.new_habr_hub_status
        self.habr_hub.next_check_at = timezone.now() + timedelta(seconds=self.habr_hub.check_interval_secs)
        self.habr_hub.last_check_at = timezone.now()
        await self.habr_hub.asave()

    async def _worker(self):
        """Рабочий, который берет задачу из очереди и выполняет ее"""
        while True:
            func, *args = await self.task_queue.get()
            try:
                await func(*args)
            except Exception as e:
                logging.error(f"Error: {e} {args}")
            finally:
                self.task_queue.task_done()

    async def _save_results(self):
        """Функция для сохранения результатов в базу данных пачками (запущенна параллельно рабочим)"""
        while True:
            results_to_save = []
            try:
                await asyncio.sleep(5)
                if self.results and len(self.results) > self.batch_size:
                    [results_to_save.append(self.results.pop(0)) for _ in range(min(self.batch_size, len(self.results)))]

                    if results_to_save:
                        await HabrLinks.objects.abulk_create(results_to_save, batch_size=self.batch_size,
                                                             ignore_conflicts=True)
                        logging.info(f"Сохранено {len(results_to_save)} записей")
            except asyncio.CancelledError:
                logging.info("Save task was cancelled. Saving remaining results...")
                self.results += results_to_save
                if self.results:
                    await HabrLinks.objects.abulk_create(self.results, batch_size=self.batch_size,
                                                         ignore_conflicts=True)
                    logging.info(f"Сохранено {len(self.results)} записей")
                break

    async def fetch_links_from_hubs(self):
        """Функция для старта сбора, создает рабочих и задачу на сохранение, добавляет первый запрос в очередь и
        ждет выполнения"""
        logging.info(f'Start parse {self.habr_hub}')
        # Запускаем задачу для параллельного сохранения данных
        save_task = asyncio.create_task(self._save_results())
        await self.task_queue.put((self._fetch_links_from_hub,))

        # Запускаем задачи с ограничением на количество потоков
        workers = [asyncio.create_task(self._worker()) for _ in range(self.max_threads)]
        await self.task_queue.join()

        # Останавливаем рабочие задачи, когда все задачи закончатся
        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

        # Останавливаем задачу сохранения данных
        save_task.cancel()
        await save_task

    async def _fetch_links_from_hub(self, page: int = 1):
        """Получение ссылок на посты пользовтелей для заданного хаба.

        :param page: int - текущая страница на хабе

        Функция делает запрос на хаб на переданную страницу и создает задачи на сбор статей по полученным артикулам.
        При сборе первой страницы создает задачи на сбор остальных страниц.
        """
        # достаем из ссылки на хаб название этого хаба и формируем ссылки для обращения к апи
        hub_name_match = re.search(r'hubs/([^/]+)/articles', self.habr_hub.hub_link)
        if hub_name_match:
            hub_name = hub_name_match.group(1)
            habr_api_link = f"https://habr.com/kek/v2/articles/?hub={hub_name}&sort=all&fl=ru&hl=ru&page={page}" \
                            f"&perPage={self.count_links_per_page}"

            # делаем запрос к апи хабра и сохраняем ссылки в базу
            # в случае ошибки или неудачи пробуем еще n-раз
            for _ in range(3):
                try:
                    async with aiohttp.ClientSession(timeout=ClientTimeout(total=30)) as session:
                        await asyncio.sleep(random.randint(1, 3))
                        async with session.get(habr_api_link) as response:
                            if response.status == 200:
                                data = await response.json()
                                if page is None or page <= 1:
                                    count_pages = data.get('pagesCount', 0)
                                    for page in range(2, min(count_pages + 1, self.max_pages + 1)):
                                        await self.task_queue.put((self._fetch_links_from_hub, page))

                                publications_info = data.get('publicationRefs', {})
                                for publication_id in publications_info.keys():
                                    await self.task_queue.put((
                                        self._fetch_info_from_post_article, publication_id, self.habr_hub))
                            else:
                                self.new_habr_hub_status = StatusChoices.ERROR
                    break
                except ClientConnectionError as e:
                    logging.error(f"Connection error [{self.habr_hub}]: {e}")
                    continue
                except asyncio.TimeoutError:
                    logging.error(f"Request timed out [{self.habr_hub}]")
                    continue
                except Exception as e:
                    logging.error(f"An unexpected error occurred [{self.habr_hub}]: {e}")
                    continue
        else:
            self.new_habr_hub_status = StatusChoices.ERROR

    async def _fetch_info_from_post_article(self, post_article: str, from_hub: HabrHubs):
        """Функия для сбора данных о статье и добавление результата в self.results для дальнейшего сохранения

        :param post_article: str - артикул статьи
        :param from_hub: HabrHub
        """
        post_url = f"https://habr.com/kek/v2/articles/{post_article}/?fl=ru&hl=ru"
        for _ in range(3):
            try:
                async with aiohttp.ClientSession(timeout=ClientTimeout(total=30)) as session:
                    await asyncio.sleep(random.randint(1, 3))
                    async with session.get(post_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            published_at = data.get('timePublished')
                            if published_at:
                                published_at = datetime.fromisoformat(published_at)
                            else:
                                published_at = None
                            author_info = data.get('author')
                            if not author_info:
                                author_info = {}
                            self.results.append(
                                HabrLinks(
                                    from_hub=from_hub,
                                    from_hub_link=from_hub.hub_link,
                                    article=post_article,
                                    link=f"https://habr.com/ru/articles/{post_article}/",
                                    title=data.get('titleHtml', ''),
                                    published_at=published_at,
                                    author_name=author_info.get('fullname', ''),
                                    author_link=f"https://habr.com/ru/users/{author_info.get('alias')}/",
                                    main_text=data.get('textHtml'),
                                    status=StatusChoices.PROCESSED
                                )
                            )
                        else:
                            self.results.append(
                                HabrLinks(
                                    from_hub=from_hub,
                                    from_hub_link=from_hub.hub_link,
                                    article=post_article,
                                    link=f"https://habr.com/ru/articles/{post_article}/",
                                    status=StatusChoices.ERROR
                                )
                            )
                break
            except ClientConnectionError as e:
                logging.error(f"Connection error [article {post_article}]: {e}")
                continue
            except asyncio.TimeoutError:
                logging.error(f"Request timed out [article {post_article}]")
                continue
            except Exception as e:
                logging.error(f"An unexpected error occurred [article {post_article}]: {e}")
                continue
