from django.contrib import admin
from .models import HabrHubs, HabrLinks


@admin.register(HabrHubs)
class MyModelAdmin(admin.ModelAdmin):
    fields = ('name', 'hub_link', 'check_interval_secs', 'next_check_at', 'max_threads', 'count_links_per_page',
              'max_pages', 'batch_size', 'last_check_at', 'status')
    readonly_fields = ('last_check_at', 'status')


@admin.register(HabrLinks)
class MyModelAdmin(admin.ModelAdmin):
    fields = ('from_hub', 'from_hub_link', 'article', 'link', 'title', 'published_at', 'author_name', 'author_link',
              'main_text', 'status', 'created_at')
    readonly_fields = ('from_hub', 'from_hub_link', 'article', 'link', 'title', 'published_at', 'author_name',
                       'author_link', 'main_text', 'status', 'created_at')

