# Generated by Django 2.1.1 on 2018-09-10 12:04

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('lists', '0004_wishlist_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wishlist',
            name='uuid',
            field=models.UUIDField(db_index=True, default=uuid.UUID('7527c8f6-7f73-4867-9026-5ea7c77379b5'), editable=False, unique=True),
        ),
    ]
