# Generated by Django 5.1.1 on 2024-09-09 20:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('habr_parser_info', '0006_habrhubs_count_links_per_page_habrhubs_max_pages_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='habrhubs',
            name='count_links_per_page',
        ),
        migrations.RemoveField(
            model_name='habrhubs',
            name='max_pages',
        ),
        migrations.RemoveField(
            model_name='habrhubs',
            name='max_threads',
        ),
    ]
