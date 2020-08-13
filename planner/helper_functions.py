from .models import *
import datetime

def load_hour_rounder(load):
    """Rounds load if the load is close to an int"""
    if abs(round(load)-load)<0.01:
        # if the load is close to an int, round it, then int it (adding 0.01 to be on the safe side)
        if load>0:
            rounded_load = int(round(load)+0.01)
        else:
            rounded_load = int(round(load)-0.01)
    else:
        rounded_load = load
    return rounded_load

def class_time_and_room_summary(scheduled_classes, include_rooms = True):
# Returns a class time summary list and an accompanying room list, such as ['MWF 9-9:50','T 10-10:50'] and ['NS 210', 'ESC 141']
# scheduled_classes is assumed to be a list of ScheduledClass objects with at least one element

    day_list = ['M','T','W','R','F']
    time_dict = dict()
    room_dict = dict()
    day_dict = dict()
    schedule_list = []
    for sc in scheduled_classes:
        time_string=start_end_time_string(sc.begin_at.hour, sc.begin_at.minute, sc.end_at.hour, sc.end_at.minute)
        if include_rooms:
            if sc.room != None:
                room = sc.room.building.abbrev+' '+sc.room.number
            else:
                room = '---'
        else:
            room = '---'
        schedule_list.append([sc.day, time_string, room])
        day_dict[time_string+room]=''
        room_dict[time_string+room] = room
        time_dict[time_string+room] = time_string

    schedule_sorted = sorted(schedule_list, key=lambda row: (row[0], row[1]))

    for item in schedule_sorted:
        day_dict[item[1]+item[2]]=day_dict[item[1]+item[2]]+day_list[item[0]]

    class_times_list = []
    room_list = []
    for key in list(day_dict.keys()):
        class_times_list.append(day_dict[key]+' '+time_dict[key])
        room_list.append(room_dict[key])

    if include_rooms:
        return class_times_list, room_list
    else:
        return class_times_list

def class_time_and_room_summary_from_dictionary(scheduled_class_dictionaries, include_rooms = True):
# Returns a class time summary list and an accompanying room list, such as ['MWF 9-9:50','T 10-10:50'] and ['NS 210', 'ESC 141']
# scheduled_class_dictionaries is assumed to be a list of the form course_offering.snaphot["scheduled_classes"] with at least one element

    day_list = ['M','T','W','R','F']
    time_dict = dict()
    room_dict = dict()
    day_dict = dict()
    schedule_list = []
    for sc in scheduled_class_dictionaries:
        time_string=start_end_time_string(sc["begin_at"].hour, sc["begin_at"].minute, sc["end_at"].hour, sc["end_at"].minute)
        if include_rooms:
            if sc["room"] != '':
                room = sc["room"]
            else:
                room = '---'
        else:
            room = '---'
        schedule_list.append([sc["day"], time_string, room])
        day_dict[time_string+room]=''
        room_dict[time_string+room] = room
        time_dict[time_string+room] = time_string

    schedule_sorted = sorted(schedule_list, key=lambda row: (row[0], row[1]))

    for item in schedule_sorted:
        day_dict[item[1]+item[2]]=day_dict[item[1]+item[2]]+day_list[item[0]]

    class_times_list = []
    room_list = []
    for key in list(day_dict.keys()):
        class_times_list.append(day_dict[key]+' '+time_dict[key])
        room_list.append(room_dict[key])

    if include_rooms:
        return class_times_list, room_list
    else:
        return class_times_list

def start_end_time_string(start_hour,start_minute,end_hour,end_minute):
# given starting and ending data, returns a string such as '9-9:50' or '9:15-10:30'

    time = str(start_hour)
    if 0<start_minute < 9:
        time = time+':0'+str(start_minute)
    elif start_minute>9:
        time = time+':'+str(start_minute)
    time = time+'-'+str(end_hour)
    if 0<end_minute < 9:
        time = time+':0'+str(end_minute)
    elif end_minute > 9:
        time = time+':'+str(end_minute)
    return time

def create_message_course_offering_update(username_other_department, user_department, course_department, year,
                                            original_co_snapshot, revised_co_snapshot, updated_fields):
    """
    Create a message informing a department that a user from a different department has updated a course offering.
        - user_department can be a Department object or None (if the user has permission level of SUPER); the reason for doing this
        (i.e., allowing None as an option) is that it looks a bit strange to get a message saying that the user 'registrar' from the 
        department CSE has made a change, or something.  It's true that SUPER users are associated with one department (at a time),
        but really they are department-less....
        - original_co_snapshot: a course_offering.snapshot dictionary or None (if None, then the user created a new course offering)
        - revised_co_snapshot: a course_offering.snapshot dictionary or None (if None, then the user deleted a course offering)
        - updated_fields: an array of snapshot dictionary keys that may have been updated
    """
    message = Message.objects.create(message_type = Message.WARNING,
                                    department = course_department,
                                    year = year,
                                    dismissed = False)
    message.save()
    # https://www.programiz.com/python-programming/datetime/current-datetime
    # https://pythontic.com/datetime/date/weekday
    
    weekdays = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
    now = datetime.datetime.now()
    datetime_string = "{0}, {1}".format(weekdays[now.weekday()], now.strftime("%B %d, %Y at %H:%M"))

    sequence_number = 0
    if (original_co_snapshot != None) and (revised_co_snapshot != None):
        # a course offering was updated
        
        if user_department != None:
            fragment_text = "The user '{0}' from the {1} department made a change to a course offering in your department on {2}.".format(
                                                username_other_department, 
                                                user_department.abbrev,
                                                datetime_string)
        else:
            fragment_text = "The user '{0}' made a change to a course offering in your department on {1}.".format(
                                                username_other_department,
                                                datetime_string)
        #print(fragment_text)
        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ZERO,
                                                        fragment = fragment_text,
                                                        sequence_number = sequence_number,
                                                        message = message)
        message_fragment.save()
        sequence_number += 1
        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ZERO,
                                                        fragment = 'Details:',
                                                        sequence_number = sequence_number,
                                                        message = message)
        message_fragment.save()                                   
        sequence_number += 1
        if "semester" in updated_fields:
            message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ONE,
                                                            fragment = original_co_snapshot["short_name"],
                                                            sequence_number = sequence_number,
                                                            message = message)
            message_fragment.save()                                   
            sequence_number += 1
        else:
            message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ONE,
                                                            fragment = original_co_snapshot["name"],
                                                            sequence_number = sequence_number,
                                                            message = message)
            message_fragment.save()                                   
            sequence_number += 1
        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ONE,
                                                        fragment = 'Changed from:',
                                                        sequence_number = sequence_number,
                                                        message = message)
        message_fragment.save()                                   
        sequence_number += 1
    elif (original_co_snapshot != None) and (revised_co_snapshot == None):
        # deleted a course offering
        if user_department != None:
            fragment_text = "The user '{0}' from the {1} department deleted a course offering from your department on {2}.".format(
                                                username_other_department, 
                                                user_department.abbrev, 
                                                datetime_string)
        else:
            fragment_text = "The user '{0}' deleted a course offering from your department on {1}.".format(
                                                username_other_department,
                                                datetime_string)
        #print(fragment_text)
        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ZERO,
                                                        fragment = fragment_text,
                                                        sequence_number = sequence_number,
                                                        message = message)
        message_fragment.save()
        sequence_number += 1
        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ZERO,
                                                        fragment = 'Details:',
                                                        sequence_number = sequence_number,
                                                        message = message)
        message_fragment.save()
        sequence_number += 1
        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ONE,
                                                        fragment = original_co_snapshot["name"],
                                                        sequence_number = sequence_number,
                                                        message = message)
        message_fragment.save()
        sequence_number += 1
    elif (original_co_snapshot == None) and (revised_co_snapshot != None):
        # created a new course offering
        if user_department != None:
            fragment_text = "The user '{0}' from the {1} department created a new course offering for your department on {2}.".format(
                                                username_other_department, 
                                                user_department.abbrev,
                                                datetime_string)
        else:
            fragment_text = "The user '{0}' created a new course offering for your department on {1}.".format(
                                                username_other_department,
                                                datetime_string)
        #print(fragment_text)
        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ZERO,
                                                        fragment = fragment_text,
                                                        sequence_number = sequence_number,
                                                        message = message)
        message_fragment.save()
        sequence_number += 1
        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ZERO,
                                                        fragment = 'Details:',
                                                        sequence_number = sequence_number,
                                                        message = message)
        message_fragment.save()
        sequence_number += 1
        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ONE,
                                                        fragment = revised_co_snapshot["short_name"],
                                                        sequence_number = sequence_number,
                                                        message = message)
        message_fragment.save()
        sequence_number += 1
    
    if original_co_snapshot != None:
        updated_sequence_number = create_message_fragments_from_snapshot(message, sequence_number, original_co_snapshot, updated_fields)
        sequence_number = updated_sequence_number
    
    if (original_co_snapshot != None) and (revised_co_snapshot != None):
        # a course offering was updated
        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_ONE,
                                                        fragment = 'Changed to:',
                                                        sequence_number = sequence_number,
                                                        message = message)
        sequence_number += 1
    
    if revised_co_snapshot != None:
        updated_sequence_number = create_message_fragments_from_snapshot(message, sequence_number, revised_co_snapshot, updated_fields)
        sequence_number = updated_sequence_number

def create_message_fragments_from_snapshot(message, sequence_number, snapshot, updated_fields):
    """
    Create a series of message fragments for the updated_fields in a course offering snapshot dictionary.
    - sequence_number is the sequence_number for the first message fragment to be written
    - updated_fields is a set of course_offering.snapshot dictionary keys for which fragments are supposed to be written
    - returns an updated sequence number, ready to use for the next message fragment 
    """
    for key in updated_fields:
        if key == "scheduled_classes":
            #sc_id_list = [sc["id"] for sc in snapshot["scheduled_classes"]]
            #sc_list = [sc for sc in ScheduledClass.objects.filter(id__in = sc_id_list)]

            if len(snapshot["scheduled_classes"]) > 0:
                meeting_times, rooms = class_time_and_room_summary_from_dictionary(snapshot["scheduled_classes"], True)
                for ii in range(len(meeting_times)):
                    message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                                fragment = "{0} ({1})".format(meeting_times[ii], rooms[ii]),
                                                                sequence_number = sequence_number,
                                                                message = message)
                    message_fragment.save()
                    sequence_number += 1
            else:
                message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                                fragment = 'no scheduled meetings',
                                                                sequence_number = sequence_number,
                                                                message = message)
                message_fragment.save()
                sequence_number += 1
        elif key == "semester":
            message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                            fragment = snapshot["semester"],
                                                            sequence_number = sequence_number,
                                                            message = message)
            message_fragment.save()
            sequence_number += 1
        elif key == "semester_fraction":
            message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                            fragment = CourseOffering.semester_frac_text(snapshot["semester_fraction"]),
                                                            sequence_number = sequence_number,
                                                            message = message)
            message_fragment.save()
            sequence_number += 1
        elif key == "offering_instructors":
            if len(snapshot["offering_instructors"]) > 0:
                for instructor in snapshot["offering_instructors"]:
                    if (len(snapshot["offering_instructors"]) == 1) or (not instructor["is_primary"]):
                        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                                fragment = "{0} [{1}/{2}]".format(instructor["instructor"]["name"], load_hour_rounder(instructor["load_credit"]), load_hour_rounder(snapshot["load_available"])),
                                                                sequence_number = sequence_number,
                                                                message = message)
                        message_fragment.save()
                        sequence_number += 1
                    else:
                        message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                            fragment = "{0} [{1}/{2}] (primary)".format(instructor["instructor"]["name"], load_hour_rounder(instructor["load_credit"]), load_hour_rounder(snapshot["load_available"])),
                                                            sequence_number = sequence_number,
                                                            message = message)
                        message_fragment.save()
                        sequence_number += 1
            else:
                message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                                fragment = 'no instructors',
                                                                sequence_number = sequence_number,
                                                                message = message)
                message_fragment.save()
                sequence_number += 1
        elif key == "load_available":
            message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                            fragment = "Load available: {0}".format(load_hour_rounder(snapshot["load_available"])),
                                                            sequence_number = sequence_number,
                                                            message = message)
            message_fragment.save()
            sequence_number += 1
        elif key == "max_enrollment":
            message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                            fragment = "Max enrollment: {0}".format(snapshot["max_enrollment"]),
                                                            sequence_number = sequence_number,
                                                            message = message)
            message_fragment.save()
            sequence_number += 1
        elif key == "comment":
            message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                            fragment = "Comment: {0}".format(snapshot["comment"]),
                                                            sequence_number = sequence_number,
                                                            message = message)
            message_fragment.save()
            sequence_number += 1
        elif key == "public_comments":
            message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_TWO,
                                                            fragment = "Public comment(s):",
                                                            sequence_number = sequence_number,
                                                            message = message)
            message_fragment.save()
            sequence_number += 1
            if len(snapshot["public_comments"]) == 0:
                message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_THREE,
                                                            fragment = "None",
                                                            sequence_number = sequence_number,
                                                            message = message)
                message_fragment.save()
                sequence_number += 1
            for public_comment in snapshot["public_comments"]:
                message_fragment = MessageFragment.objects.create(indentation_level = MessageFragment.TAB_THREE,
                                                            fragment = public_comment["text"],
                                                            sequence_number = sequence_number,
                                                            message = message)
                message_fragment.save()
                sequence_number += 1

    return sequence_number
