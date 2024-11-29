# myapp/management/commands/run_admin.py
from django.core.management.base import BaseCommand
from subprocess import Popen


class Command(BaseCommand):
    help = 'Run the administrative GUI'

    def handle(self, *args, **options):
        Popen(['python', 'admin_management/main.py'])
