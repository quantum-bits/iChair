from django.core.management import BaseCommand
from django.db.models import Q

from planner.models import *
from banner.models import Room as BannerRoom
from banner.models import Building as BannerBuilding

from four_year_plan.secret import DATA_WAREHOUSE_AUTH as DW



class Command(BaseCommand):
    # https://stackoverflow.com/questions/30230490/django-custom-command-error-unrecognized-arguments
    help = "Compares rooms in the Banner database to those in the iChair database."

    def handle(self, *args, **options):
        
        for room in BannerRoom.objects.all():
            ichair_rooms = Room.objects.filter(Q(building__abbrev=room.building.abbrev) & Q(number=room.number))
            if len(ichair_rooms) > 1:
                print("More than one match in iChair for the following Banner room: ", room)
            elif len(ichair_rooms) == 0:
                print("No matches in iChair for the following Banner room: ", room)
            else:
                # if there is exactly one match, compare the capacities....
                ichair_room = ichair_rooms[0]
                if ichair_room.capacity != room.capacity:
                    print(room, ": iChair room capacity (", ichair_room.capacity,") is different than Banner room capacity (", room.capacity,")")
                    print("Fixing iChair room capacity....")
                    ichair_room.capacity = room.capacity
                    ichair_room.save()
        
        num_rooms_missing_in_banner = 0
        for room in Room.objects.all():
            banner_rooms = BannerRoom.objects.filter(Q(building__abbrev=room.building.abbrev) & Q(number=room.number))
            if len(banner_rooms) > 1:
                print("More than one match in Banner for the following iChair room: ", room)
            elif len(banner_rooms) == 0:
                num_rooms_missing_in_banner += 1
                #print("No matches in Banner for the following iChair room: ", room)
        print("Number of rooms that are in iChair but not in Banner: ", num_rooms_missing_in_banner)

        



