def class_time_summary(scheduled_classes):
# Returns a class time summary list, such as ['MWF 9-9:50','T 10-10:50']
# scheduled_classes is assumed to be a list of ScheduledClass objects with at least one element

    day_list = ['M','T','W','R','F']
    time_dict = dict()
    schedule_list = []
    for sc in scheduled_classes:
        time_string=start_end_time_string(sc.begin_at.hour, sc.begin_at.minute, sc.end_at.hour, sc.end_at.minute)
        schedule_list.append([sc.day, time_string])
        time_dict[time_string]=''

    schedule_sorted = sorted(schedule_list, key=lambda row: (row[0], row[1]))

    for item in schedule_sorted:
        time_dict[item[1]]=time_dict[item[1]]+day_list[item[0]]

#    print time_dict

    class_times = ''
    ii = len(time_dict.keys())
    for key in time_dict.keys():
        class_times = class_times+time_dict[key]+' '+key
        ii = ii-1
        if ii > 0:
            class_times = class_times + "; "

    class_times_list = []
    for key in time_dict.keys():
        class_times_list.append(time_dict[key]+' '+key)

#    print class_times_list
# Note: class_times could be sent as well; it is a string of meeting times separated by semi-colons
#       ===> if this is done, need to edit the template a bit and also the "---" case, to make it
#            a simple string instead of a list
    return class_times_list

def class_time_and_room_summary(scheduled_classes):
# Returns a class time summary list and an accompanying room list, such as ['MWF 9-9:50','T 10-10:50'] and ['NS 210', 'ESC 141']
# scheduled_classes is assumed to be a list of ScheduledClass objects with at least one element

    day_list = ['M','T','W','R','F']
    time_dict = dict()
    room_dict = dict()
    day_dict = dict()
    schedule_list = []
    for sc in scheduled_classes:
        time_string=start_end_time_string(sc.begin_at.hour, sc.begin_at.minute, sc.end_at.hour, sc.end_at.minute)
        room = sc.room.building.abbrev+' '+sc.room.number
        schedule_list.append([sc.day, time_string, room])
        day_dict[time_string+room]=''
        room_dict[time_string+room] = room
        time_dict[time_string+room] = time_string

    schedule_sorted = sorted(schedule_list, key=lambda row: (row[0], row[1]))

    for item in schedule_sorted:
        day_dict[item[1]+item[2]]=day_dict[item[1]+item[2]]+day_list[item[0]]

    class_times_list = []
    room_list = []
    for key in day_dict.keys():
        class_times_list.append(day_dict[key]+' '+time_dict[key])
        room_list.append(room_dict[key])

    return class_times_list, room_list


        day_schedules = {0:[], 1:[], 2:[], 3:[], 4:[]}

                for time_block in day_schedules[day]:
                    if (begin_time_decimal < time_block[1] and begin_time_decimal > time_block[0]
                        ) or (end_time_decimal < time_block[1] and end_time_decimal > time_block[0]
                        ) or (begin_time_decimal <= time_block[0] and end_time_decimal >= time_block[1]):
                        raise forms.ValidationError("Time blocks for a given day within a course offering cannot overlap.")

                day_schedules[day].append([begin_time_decimal, end_time_decimal])
