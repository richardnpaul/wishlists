# Generated by Django 2.1.1 on 2018-09-11 08:56

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('lists', '0006_auto_20180910_1205'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wishlist',
            name='uuid',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
