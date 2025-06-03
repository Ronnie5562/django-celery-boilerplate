"""
Command for the app to wait until the database is available
"""
import time
from django.db.utils import OperationalError
from psycopg2 import OperationalError as Psycopg2OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command class to wait for db
    """

    def handle(self, *args, **options):
        """Handle the command"""
        self.stdout.write('Waiting for database...')
        # print('Waiting for database...')
        db_up = False

        while db_up is False:
            try:
                self.check(databases=["default"])
                db_up = True
            except (Psycopg2OperationalError, OperationalError):
                self.stdout.write(self.style.WARNING('\
                    Database unavailable, waiting 1 second...'))
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database available!'))
