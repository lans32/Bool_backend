# Generated by Django 4.2.4 on 2024-10-09 04:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_remove_askoperation_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ask',
            name='ask_number',
        ),
    ]
