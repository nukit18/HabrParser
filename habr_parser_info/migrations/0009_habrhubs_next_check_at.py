# Generated by Django 5.1.1 on 2024-09-10 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('habr_parser_info', '0008_rename_check_interval_habrhubs_check_interval_secs_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='habrhubs',
            name='next_check_at',
            field=models.DateTimeField(null=True),
        ),
    ]
