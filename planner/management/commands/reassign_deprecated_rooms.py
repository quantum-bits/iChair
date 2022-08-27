import pyodbc
from django.core.management import BaseCommand
from django.db.models import Q

from planner.models import *
from banner.models import CourseOffering as BannerCourseOffering

"""
This command can be run after a room number becomes deprecated for some reason (either 
the physical room disappears or it is assigned a new number).

Do the following before running this script:
- change the semesters to copy to be only for the year in question (to avoid possible mix-ups with distinct rooms that have the same room number in the old and new systems)
- run the warehouse command to update banner.db
- assign an inactive_after date for the room(s) in iChair that have been deprecated; this date should be 
  before the beginning of the term when the room first becomes unusable (mid-summer if the room 
  can no longer be used in the fall, for example)
- create new rooms as needed in iChair (for example, if READE 222 becomes READE 223, first add the inactive_after 
  to READE 222, then create the new READE 223 with the same room capacity)
- if there is an obvious mapping between old room numbers and new ones, fill in the dictionary 
  old_room_to_new_room_map (below) as appropriate; don't include anything for rooms that simply get deleted
- in banner.db, can delete unused (deprecated) rooms
- in banner.db, if any room numbers are recycled (but now refer to different physical rooms), need to be
  sure to fix the capacities(!)
Then the command can be run...!
"""


class Command(BaseCommand):
    # https://stackoverflow.com/questions/30230490/django-custom-command-error-unrecognized-arguments
    help = "Finds rooms in the iChair database that are deprecated (i.e., inactive) but still have course offerings assigned to them.  Attempts to reassign rooms correctly."

    def handle(self, *args, **options):
        
        old_room_to_new_room_map = {
            'READE 211': {
                'building': 'READE',
                'number': '220'
            },
            'READE 212': {
                'building': 'READE',
                'number': '222'
            },
            'READE 218': {
                'building': 'READE',
                'number': '240'
            },
            'READE 220': {
                'building': 'READE',
                'number': '246'
            },
            'READE 221': {
                'building': 'READE',
                'number': '248'
            },
            'READE 234': {
                'building': 'READE',
                'number': '247'
            },
            'READE 235': {
                'building': 'READE',
                'number': '245'
            },
            'READE 238': {
                'building': 'READE',
                'number': '227'
            },
            'READE 239': {
                'building': 'READE',
                'number': '225'
            },
            'READE 240': {
                'building': 'READE',
                'number': '223'
            },
            'READE 241': {
                'building': 'READE',
                'number': '221'
            },
        }

        perfect_matches = 0 #number of times that the scheduled class in Banner exactly matches the dictionary above
        not_perfect_match_but_switched_to_banner_room = 0
        number_sc = 0
        multiple_room_error = 0
        number_changed_manually = 0
        number_rooms_dropped_manually = 0
        for room in Room.objects.all():
            if room.inactive_after is not None:
                for sc in room.scheduled_class_objects.all():
                    if sc.course_offering.semester.begin_on > room.inactive_after:
                        print(sc, room)
                        number_sc += 1
                        if not ((sc.course_offering.crn is None) or sc.course_offering.crn == ''):
                            print('  ',sc.course_offering.crn)
                            bco = BannerCourseOffering.objects.filter(Q(term_code = sc.course_offering.semester.banner_code) & Q(crn = sc.course_offering.crn))
                            if len(bco) == 1:
                                print('     found a banner match!')
                                key = room.building.abbrev+' '+room.number
                                if key in old_room_to_new_room_map.keys():
                                    print(old_room_to_new_room_map[key])
                                    banner_sc = bco[0].scheduled_classes.filter(Q(day = sc.day) & Q(begin_at = sc.begin_at) & Q(end_at = sc.end_at))
                                    if len(banner_sc) == 1:
                                        if len(banner_sc[0].rooms.all()) == 0:
                                            print('No room assigned for this scheduled class in banner...')
                                            proceed = input("assign room according to dictionary? new room will be {} (y/n)".format(old_room_to_new_room_map[key]["building"]+' '+old_room_to_new_room_map[key]["number"]))
                                            if proceed == 'y':
                                                success = add_room_according_to_dictionary(sc, room, old_room_to_new_room_map[key]["building"], old_room_to_new_room_map[key]["number"])
                                                if success:
                                                    number_changed_manually += 1
                                        
                                        for banner_room in banner_sc[0].rooms.all():
                                            if (len(banner_sc[0].rooms.all()) == 1) and (old_room_to_new_room_map[key]["building"] == banner_room.building.abbrev) and (old_room_to_new_room_map[key]["number"] == banner_room.number):
                                                print('        >>> found a perfect match!  Updating iChair....')
                                                new_room = Room.objects.filter(Q(building__abbrev = banner_room.building.abbrev) & Q(number = banner_room.number) & Q(inactive_after = None))
                                                if len(new_room) == 1:
                                                    sc.rooms.remove(room)
                                                    sc.rooms.add(new_room[0])
                                                    sc.save()
                                                    print('          > new room:', sc.rooms.all())
                                                    perfect_matches += 1
                                                else:
                                                    print('zero or multiple rooms?!? ', new_room)
                                                    multiple_room_error +=1
                                            else:
                                                if len(banner_sc[0].rooms.all()) == 1:
                                                    print('        >>> there is 1 banner room, but it does not match the look-up dictionary; banner room: ', banner_room, '...updating....')
                                                    new_room = Room.objects.filter(Q(building__abbrev = banner_room.building.abbrev) & Q(number = banner_room.number) & Q(inactive_after = None))
                                                    if len(new_room) == 1:
                                                        sc.rooms.remove(room)
                                                        sc.rooms.add(new_room[0])
                                                        sc.save()
                                                        print('          > new room:', sc.rooms.all())
                                                        not_perfect_match_but_switched_to_banner_room += 1
                                                    else:
                                                        print('zero or multiple rooms?!? ', new_room)
                                                        multiple_room_error +=1
                                                else:
                                                    print('         .....looks like there are more than one banner room:')
                                                    for br in banner_sc[0].rooms.all():
                                                        print('         ...', br)
                                    else:
                                        print('       no unique match for this scheduled class in banner; number of banner scheduled classes: ', len(banner_sc))
                                        delete_room = input('Drop the room? (y/n)')
                                        if delete_room == 'y':
                                            success = drop_room(sc, room)
                                            number_rooms_dropped_manually += 1
                                        elif key in old_room_to_new_room_map.keys():
                                            proceed = input("assign room according to dictionary? new room will be {} (y/n)".format(old_room_to_new_room_map[key]["building"]+' '+old_room_to_new_room_map[key]["number"]))
                                            if proceed == 'y':
                                                success = add_room_according_to_dictionary(sc, room, old_room_to_new_room_map[key]["building"], old_room_to_new_room_map[key]["number"])
                                                if success:
                                                    number_changed_manually += 1


                                else:
                                    print('          looks like the room has been deleted...?')
                                    proceed = input('do you wish to enter a room number manually? (y/n)')
                                    if proceed == 'y':
                                        success = add_room_manually(sc, room)
                                        if success:
                                            number_changed_manually += 1
                                    if proceed == 'n':
                                        delete_room = input('Drop the room instead? (y/n)')
                                        if delete_room == 'y':
                                            success = drop_room(sc, room)
                                            number_rooms_dropped_manually += 1
                            else:
                                print('     no unique match found! number banner course offerings: ', len(bco))
                                delete_room = input('Drop the room? (y/n)')
                                if delete_room == 'y':
                                    success = drop_room(sc, room)
                                    number_rooms_dropped_manually += 1
                                elif key in old_room_to_new_room_map.keys():
                                    proceed = input("assign room according to dictionary? new room will be {} (y/n)".format(old_room_to_new_room_map[key]["building"]+' '+old_room_to_new_room_map[key]["number"]))
                                    if proceed == 'y':
                                        success = add_room_according_to_dictionary(sc, room, old_room_to_new_room_map[key]["building"], old_room_to_new_room_map[key]["number"])
                                        if success:
                                            number_changed_manually += 1
                        else:
                            print('   course offering has no CRN')
                            key = room.building.abbrev+' '+room.number
                            if key in old_room_to_new_room_map.keys():
                                proceed = input("assign room according to dictionary? new room will be {} (y/n)".format(old_room_to_new_room_map[key]["building"]+' '+old_room_to_new_room_map[key]["number"]))
                                if proceed == 'y':
                                    success = add_room_according_to_dictionary(sc, room, old_room_to_new_room_map[key]["building"], old_room_to_new_room_map[key]["number"])
                                    if success:
                                        number_changed_manually += 1
                            else:
                                proceed = input('no obvious new room...do you wish to enter a room number manually? (y/n)')
                                if proceed == 'y':
                                    success = add_room_manually(sc, room)
                                    if success:
                                        number_changed_manually += 1
                                if proceed == 'n':
                                    delete_room = input('Drop the room instead? (y/n)')
                                    if delete_room == 'y':
                                        success = drop_room(sc, room)
                                        number_rooms_dropped_manually += 1
        print('number of perfect matches: ', perfect_matches)
        print('number of times switched to Banner room: ', not_perfect_match_but_switched_to_banner_room)
        print('number of scheduled classes to deal with: ', number_sc)
        print('number multiple room errors: ', multiple_room_error)
        print('number of rooms updated manually: ', number_changed_manually)
        print('number of rooms dropped manually: ', number_rooms_dropped_manually)
        

def add_room_manually(sc, old_room):
    building_abbrev = input('Enter building abbreviation: ')
    room_number = input('Enter room number: ')
    new_room = Room.objects.filter(Q(building__abbrev = building_abbrev) & Q(number = room_number) & Q(inactive_after = None))
    if len(new_room) == 1:
        sc.rooms.remove(old_room)
        sc.rooms.add(new_room[0])
        sc.save()
        print('          > new room:', sc.rooms.all())
        return True
    return False

def drop_room(sc, old_room):
    sc.rooms.remove(old_room)
    sc.save()
    print('          > new room:', sc.rooms.all())
    return True

def add_room_according_to_dictionary(sc, old_room, new_building, new_number):
    new_room = Room.objects.filter(Q(building__abbrev = new_building) & Q(number = new_number) & Q(inactive_after = None))
    if len(new_room) == 1:
        sc.rooms.remove(old_room)
        sc.rooms.add(new_room[0])
        sc.save()
        print('          > new room:', sc.rooms.all())
        return True
    return False
