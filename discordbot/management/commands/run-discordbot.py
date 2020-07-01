from django.core.management.base import BaseCommand, CommandError

import os

from discordbot.bot import run

class Command(BaseCommand):
    help = 'Runs the Discord bot'

    def add_arguments(self, parser):
        parser.add_argument('--token', help="Discords Bot Token", type=str)

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("[Bot] - Bot wird gestartet..."))

        if "token" in options and options["token"]:
            run(options["token"])
        elif 'DISCORD_BOTTOKEN' in os.environ:
            run(os.environ.get('DISCORD_BOTTOKEN'))
        else:
            print("[Bot] - No TOKEN found!")

        self.stdout.write(self.style.SUCCESS("[Bot] - Bot wurde beendet!"))
