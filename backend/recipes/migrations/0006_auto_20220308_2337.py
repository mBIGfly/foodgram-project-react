# Generated by Django 2.2.27 on 2022-03-08 20:37

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_auto_20220308_1126'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredientreciperelation',
            options={'verbose_name': 'Ингредиенты для рецепта', 'verbose_name_plural': 'Ингредиенты для рецепта'},
        ),
        migrations.AlterField(
            model_name='shoppingcart',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shopping_cart', to='recipes.Recipe', verbose_name='Рецепт'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=models.CharField(help_text='Введите код цвета в шестнадцетиричном формате (#ABCDEF)', max_length=7, validators=[django.core.validators.RegexValidator(code='wrong_hex_code', message='Неправильный формат цвета', regex='^#[a-eA-E0-9]{6}$')], verbose_name='Цвет'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=150, unique=True, verbose_name='Имя тега'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(help_text='Введите slug тега', unique=True, verbose_name='Slug'),
        ),
        migrations.AddConstraint(
            model_name='ingredient',
            constraint=models.UniqueConstraint(fields=('name', 'measurement_unit'), name='Unique ingredient'),
        ),
    ]