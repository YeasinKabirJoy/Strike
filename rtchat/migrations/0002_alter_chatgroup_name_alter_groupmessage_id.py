# Generated by Django 5.1.3 on 2024-11-16 05:28

import functools
import shortuuid.main
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rtchat', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatgroup',
            name='name',
            field=models.CharField(blank=True, default=functools.partial(shortuuid.main.ShortUUID.random, *(), **{'length': 10}), max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='groupmessage',
            name='id',
            field=models.CharField(default=functools.partial(shortuuid.main.ShortUUID.random, *(), **{'length': 18}), editable=False, max_length=18, primary_key=True, serialize=False, unique=True),
        ),
    ]