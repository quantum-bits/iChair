import pyodbc
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
        
        connection = pyodbc.connect(
            f'DSN=warehouse;UID={DW["user"]};PWD={DW["password"]}')
        cursor = connection.cursor()
        rows = cursor.execute("select @@VERSION").fetchall()

        dw_rooms = cursor.execute("""
            SELECT dr.*
            FROM dw.dim_room dr -- use the room dimension as base.
            """).fetchall()
        
        #for dw_room in dw_rooms:
        #    print('%s: %s %s (capacity: %s)' % (dw_room.building_name, dw_room.building_code, dw_room.room_number, dw_room.room_capacity))

        num_rooms_missing_in_banner_db = 0
        num_rooms_missing_in_banner_db_but_in_dw = 0
        rooms_not_found = []
        for room in Room.objects.all():
            banner_rooms = BannerRoom.objects.filter(Q(building__abbrev=room.building.abbrev) & Q(number=room.number))
            if len(banner_rooms) > 1:
                print("More than one match in Banner for the following iChair room: ", room)
            elif len(banner_rooms) == 0:
                num_rooms_missing_in_banner_db += 1
                room_found_in_dw = False
                for dw_room in dw_rooms:
                    if (room.building.abbrev == dw_room.building_code) and (room.number == dw_room.room_number):
                        print('room is not in banner.db, but it is in the data warehouse! ', dw_room.building_code, dw_room.room_number)
                        # add the room to banner.db
                        # first check if building exists....
                        banner_building = BannerBuilding.objects.filter(abbrev=dw_room.building_code)
                        if len(banner_building) == 1:
                            print('   building exists!  creating a new room in banner.db....')
                            new_room = BannerRoom.objects.create(
                                number = dw_room.room_number,
                                building = banner_building[0],
                                capacity = dw_room.room_capacity)
                            new_room.save()
                        else:
                            print('   uh...Houston, we have a problem with the building -- creating a new one')
                            new_building = BannerBuilding.objects.create(
                                abbrev = dw_room.building_code,
                                name = dw_room.building_name)
                            new_building.save()
                            print('   ...and now creating the room')
                            new_room = BannerRoom.objects.create(
                                number = dw_room.room_number,
                                building = new_building,
                                capacity = dw_room.room_capacity)
                            new_room.save()
                        
                        print(' >>> capacities match?', room.capacity == dw_room.room_capacity)
                        if room.capacity != dw_room.room_capacity:
                            print('     ', room.capacity, dw_room.room_capacity)
                            print('...fixing the room capacity in ichair.db....')
                            # fix the capacity in ichair.db
                            room.capacity = dw_room.room_capacity
                            room.save()
                        num_rooms_missing_in_banner_db_but_in_dw += 1
                        room_found_in_dw = True
                if not room_found_in_dw:
                    rooms_not_found.append(room)
                    #print("No matches in banner.db or DW for the following iChair room: ", room)

        print("Number of rooms that are in iChair but not in banner.db: ", num_rooms_missing_in_banner_db)
        print("Number of rooms that are in iChair, are not in banner.db, but are in the DW: ", num_rooms_missing_in_banner_db_but_in_dw)
        print("No matches in banner.db or DW for the following iChair rooms: ")
        for room in rooms_not_found:
            print(room)

        



    

        



