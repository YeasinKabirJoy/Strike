# Generated by Django 5.1.3 on 2024-11-12 06:32

import rtchat.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rtchat', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupmessage',
            name='id',
            field=models.CharField(default=rtchat.models.generate_short_uuid, editable=False, max_length=18, primary_key=True, serialize=False, unique=True),
        ),
    ]
