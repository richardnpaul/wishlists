# Generated by Django 2.1.2 on 2018-10-16 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("lists", "0004_auto_20181013_1645")]

    operations = [migrations.AddField(model_name="item", name="notes", field=models.TextField(null=True))]
