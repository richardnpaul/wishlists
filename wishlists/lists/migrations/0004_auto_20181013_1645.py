# Generated by Django 2.1.2 on 2018-10-13 16:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("lists", "0003_auto_20181009_1715")]

    operations = [migrations.AlterModelOptions(name="item", options={"ordering": ("priority", "wishlist", "id")})]
