# Generated by Django 3.1.2 on 2020-10-31 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discordbot", "0010_viergewinntgame"),
    ]

    operations = [
        migrations.AlterField(
            model_name="viergewinntgame",
            name="player_2_id",
            field=models.CharField(
                default=None,
                max_length=32,
                null=True,
                verbose_name="Player 2 ID",
            ),
        ),
    ]
