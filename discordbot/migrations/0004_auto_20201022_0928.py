# Generated by Django 3.1.2 on 2020-10-22 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discordbot", "0003_amongusgame"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="amongusgame",
            name="tracker_connected",
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="tracker_connected",
            field=models.BooleanField(
                default=False, verbose_name="Tracker connected"
            ),
        ),
    ]
