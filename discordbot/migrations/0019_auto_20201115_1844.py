# Generated by Django 3.1.3 on 2020-11-15 17:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discordbot", "0018_auto_20201114_2032"),
    ]

    operations = [
        migrations.CreateModel(
            name="Playlist",
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
                    "title",
                    models.CharField(
                        default="Server default",
                        max_length=256,
                        verbose_name="Title",
                    ),
                ),
                (
                    "current_pos",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Current position"
                    ),
                ),
                (
                    "server",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="playlists",
                        to="discordbot.server",
                    ),
                ),
            ],
            options={
                "verbose_name": "Audio queue",
                "verbose_name_plural": "Audio queues",
            },
        ),
        migrations.CreateModel(
            name="PlaylistPosition",
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
                    "position",
                    models.PositiveSmallIntegerField(verbose_name="Position"),
                ),
                (
                    "queue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="discordbot.playlist",
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="discordbot.audiosource",
                    ),
                ),
            ],
            options={
                "verbose_name": "Audio queue position",
                "verbose_name_plural": "Audio queue positions",
            },
        ),
        migrations.AddField(
            model_name="playlist",
            name="sources",
            field=models.ManyToManyField(
                through="discordbot.PlaylistPosition",
                to="discordbot.AudioSource",
            ),
        ),
        migrations.AddField(
            model_name="server",
            name="playlist",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="discordbot.playlist",
            ),
        ),
    ]
