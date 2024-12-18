# Generated by Django 5.1.3 on 2024-11-21 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rtchat', '0006_alter_groupchatrequest_request'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmessage',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='files/'),
        ),
        migrations.AlterField(
            model_name='groupmessage',
            name='message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
