# Generated by Django 3.1.3 on 2020-11-08 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discordbot", "0011_auto_20201031_1721"),
    ]

    operations = [
        migrations.CreateModel(
            name="BotPermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("id_1", models.CharField(max_length=32, verbose_name="ID 1")),
                ("id_2", models.CharField(max_length=32, verbose_name="ID 2")),
                ("typ", models.CharField(max_length=32, verbose_name="Typ")),
            ],
        ),
    ]
