# Generated by Django 2.2.27 on 2022-03-08 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_auto_20220308_2337'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='ingredientreciperelation',
            constraint=models.UniqueConstraint(fields=('recipe', 'ingredient'), name='Unique ingredient for recipe'),
        ),
    ]
