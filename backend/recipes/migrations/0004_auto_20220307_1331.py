# Generated by Django 2.2.27 on 2022-03-07 10:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20220307_0514'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredient',
            options={'ordering': ('id',), 'verbose_name': 'ингридиент', 'verbose_name_plural': 'ингридиенты'},
        ),
        migrations.AlterModelOptions(
            name='recipe',
            options={'ordering': ('id',), 'verbose_name': 'рецепт', 'verbose_name_plural': 'рецепты'},
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'ordering': ('id',), 'verbose_name': 'тег', 'verbose_name_plural': 'теги'},
        ),
    ]
