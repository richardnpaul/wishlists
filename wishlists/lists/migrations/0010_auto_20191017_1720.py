# Generated by Django 2.2.6 on 2019-10-17 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lists', '0009_auto_20191016_1654'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='delivered',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='item',
            name='ordered',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='item',
            name='wrapped',
            field=models.BooleanField(default=False),
        ),
    ]