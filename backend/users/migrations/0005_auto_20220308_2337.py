# Generated by Django 2.2.27 on 2022-03-08 20:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_remove_customuser_is_subscribed'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'ordering': ('id',), 'verbose_name': 'пользователя', 'verbose_name_plural': 'пользователи'},
        ),
    ]
