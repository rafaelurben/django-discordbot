# Generated by Django 3.1.3 on 2020-11-10 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discordbot", "0014_auto_20201110_1826"),
    ]

    operations = [
        migrations.AddField(
            model_name="notifiersub",
            name="name",
            field=models.CharField(
                default="Unbenannte Mitteilung",
                max_length=50,
                verbose_name="Name",
            ),
        ),
    ]
