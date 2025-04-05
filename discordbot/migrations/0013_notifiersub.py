# Generated by Django 3.1.3 on 2020-11-10 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discordbot", "0012_botpermission"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotifierSub",
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
                (
                    "where_type",
                    models.CharField(
                        choices=[
                            ("channel", "Kanal"),
                            ("member", "Mitglied (DM)"),
                        ],
                        max_length=8,
                    ),
                ),
                (
                    "where_id",
                    models.CharField(max_length=32, verbose_name="ID 1"),
                ),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("hour", "Stündlich"),
                            ("minute", "Minütlich"),
                        ],
                        max_length=8,
                        verbose_name="Häufigkeit",
                    ),
                ),
                ("url", models.URLField(verbose_name="URL")),
                (
                    "must_contain_regex",
                    models.CharField(
                        default="",
                        max_length=32,
                        verbose_name="Muss Regex enthalten",
                    ),
                ),
                (
                    "last_hash",
                    models.CharField(
                        max_length=32, verbose_name="Letzter Hash"
                    ),
                ),
            ],
        ),
    ]
