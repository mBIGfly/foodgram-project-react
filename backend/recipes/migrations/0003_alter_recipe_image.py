# Generated by Django 3.2.12 on 2022-03-05 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(null=True, upload_to='recipes/', verbose_name='Картинка'),
        ),
    ]