from django.core.management.base import BaseCommand, CommandError
from planner.campus_models import *
from django.db.models import Q

class Command(BaseCommand):
    args = 'building_abbrev, number, capacity'
    help = 'Add a room if it does not yet exist'
#
# sample usage:
# ./manage.py create_room ESC 241 24
#
# Note: checks first to see if the room already exists
#
    
    def handle(self, *args, **options):
        building_abbrev, number, capacity = args

        print("processing: ", building_abbrev, number, capacity)

        try:
            building_object = Building.objects.get(abbrev = building_abbrev)
        except Building.DoesNotExist:
            raise CommandError(building_abbrev+' does not exist in the database.')

        try:
            room = Room.objects.get(Q(building=building_object)&Q(number=number))
            raise CommandError(building_abbrev+' '+number+' already exists in the database.')
        except Room.DoesNotExist:
            room = Room.objects.create(building = building_object,
                                       number = number,
                                       capacity = int(capacity)
                                       )
