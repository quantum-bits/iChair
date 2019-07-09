import pyodbc
from django.core.management import BaseCommand

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW


class Command(BaseCommand):
    help = "Manage data warehouse information"

    def handle(self, *args, **options):
        connection = pyodbc.connect(f'DSN=warehouse;UID={DW["user"]};PWD={DW["password"]}')
        cursor = connection.cursor()
        rows = cursor.execute("select @@VERSION").fetchall()
        cursor.close()
        connection.close()

        print(rows[0][0])
