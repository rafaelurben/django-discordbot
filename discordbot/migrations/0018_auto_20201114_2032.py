# Generated by Django 3.1.3 on 2020-11-14 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discordbot', '0017_audiosource'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audiosource',
            name='url_source',
            field=models.TextField(verbose_name='Url (Source)'),
        ),
    ]
