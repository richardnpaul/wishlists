# Generated by Django 2.2.6 on 2019-10-09 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lists', '0006_auto_20191009_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='wishlist',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
