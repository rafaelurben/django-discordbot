# Generated by Django 3.1.2 on 2020-10-23 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discordbot", "0006_auto_20201022_1804"),
    ]

    operations = [
        migrations.AddField(
            model_name="amongusgame",
            name="p_black_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Black's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_blue_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Blue's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_brown_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Brown's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_cyan_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Cyan's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_green_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Green's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_lime_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Lime's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_orange_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Orange's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_pink_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Pink's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_purple_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Purple's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_red_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Red's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_white_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="White's Discord ID",
            ),
        ),
        migrations.AddField(
            model_name="amongusgame",
            name="p_yellow_userid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Yellow's Discord ID",
            ),
        ),
    ]
