import pyodbc
from django.core.management import BaseCommand
from django.db.models import Q

from planner.models import *
from banner.models import CourseOffering as BannerCourseOffering




class Command(BaseCommand):
    # https://stackoverflow.com/questions/30230490/django-custom-command-error-unrecognized-arguments
    help = "Finds rooms in the iChair database that are deprecated (i.e., inactive) but still have course offerings assigned to them.  Attempts to reassign rooms correctly."

    def handle(self, *args, **options):
        
        old_room_to_new_room_map = {
            'AYRES 215': {
                'building': 'AYRES',
                'number': '214'
            },
            'READE 118': {
                'building': 'READE',
                'number': '130'
            },
            'READE 119': {
                'building': 'READE',
                'number': '132'
            },
            'READE 120': {
                'building': 'READE',
                'number': '134'
            },
            'READE 127': {
                'building': 'READE',
                'number': '140'
            },
            'READE 128': {
                'building': 'READE',
                'number': '142'
            },
            'READE 140': {
                'building': 'READE',
                'number': '137'
            },
            'READE 143': {
                'building': 'READE',
                'number': '133'
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
                                                    print('         .....looks like there are more than one banner room')
                                    else:
                                        print('       no unique match for this scheduled class in banner')

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
                                print('     no unique match found!')
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
