#!/usr/bin/python

import sys,re

def remove_space(my_string):
    return ''.join(i for i in my_string if not i.isspace())

def format_course_numbers(course_numbers):
    """
    Returns a the list of coure_numbers with each space removed.
    and uppercase. Makes comparing course numbers easier.
    """
    return [remove_space(course_number).upper() for course_number in course_numbers]    

def meet_one_of(courses, reqs, courses_meeting_reqs, req_name):
    reqs = format_course_numbers(reqs)
    need_message = "Need a {} requirement.".format(req_name)
    course_reqs = list(set(reqs).intersection(courses))
    if not course_reqs:
        print need_message
    else:
        course_reqs = list(course_reqs)
        # remove reqs that are already meeting some other course req. 
        num_courses_meeting_reqs = len(courses_meeting_reqs)

        for req in filter(lambda req: req not in courses_meeting_reqs, course_reqs):
            courses_meeting_reqs.append(req)

        if len(courses_meeting_reqs) == num_courses_meeting_reqs: 
            print need_message
        else:
            print "{} requirement met.".format(req_name)

def course_prefix(course_name):
    match = re.search(r'^(?P<prefix>.+?)\d+$', course_name)
    if match:
        return match.group('prefix')
    else:
        return None

ORIENTATION = ['IAS 101']
SPIRITUAL_FOUNDATION = ['IAS 110', 'BIB 110', 'BIB 210', 'REL 313', 'PHI 413', 'IAS 495']
STEWARDSHIP_REQUIRED = ['PHP 100']
WRITING = ['ENG 110']

STEWARDSHIP_ONE_OF = (['PHP 200x', 'PHP 250', 'PHP 280', 'PHP 300', 
                       'PHP 302', 'PHP 333', 'PHP 334', 'PHP 345'])

SPEAKING_ONE_OF = (['CAS 110', 'CAS 120'])
COMPUTER_SCIENCE_ONE_OF = (['COS 104', 'COS 106'])

MATH_ONE_OF = (['MAT 110', 'MAT 120', 'MAT 140', 'MAT 145', 'MAT 151', 
                                     'MAT 180', 'MAT 210', 'MAT 220', 'SOC 355'])

LITERATURE_ONE_OF = (['CAT 200', 'ENG 230', 'ENG 240', 'ENG 250'])

LIFE_SCIENCE = format_course_numbers(['BIO 100', 'BIO 101', 'BIO 103', 'BIO 104', 'BIO 200',
                                      'BIO 205', 'BIO 243', 'BIO 244', 'CHE 120', 'ENS 200'])

PHYSICAL_SCIENCE = format_course_numbers(['CHE 100', 'CHE 120', 'CHE 201', 'CHE 211',
                                          'PHY 120', 'PHY 203', 'PHY 211'])

EARTH_SCIENCE = format_course_numbers(['ENP 345', 'ENS 241', 'ENS 242', 
                                       'GEO 210', 'GEO 240', 'PHY 201'])

CIVIC_ENGAGE = format_course_numbers(['ECO 190', 'ECO 201', 'ECO 202', 'GEO 230',
                                      'PHP 346', 'POS 100', 'POS 150', 'POS 213',
                                      'POS 331', 'SOC 100', 'SOC 200', 'SOC 210', 
                                      'SOC 220', 'SOC 410', 'SWK 200', 'SWK 320'])

GENERAL_SOCIAL = format_course_numbers(['GEO 220', 'HIS 211', 'HIS 311', 'HIS 213', 'HIS 313',
                                        'IAS 330', 'POS 222', 'POS 312', 'POS 321', 'PSY 110',
                                        'PSY 200', 'PSY 240', 'PSY 250', 'PSY 340', 'PSY 350',
                                        'SOC 310', 'SOC 330', 'SOC 361', 'SOC 381'])



REQUIRED_COURSES = format_course_numbers(ORIENTATION + 
                                         SPIRITUAL_FOUNDATION + 
                                         STEWARDSHIP_REQUIRED + 
                                         WRITING)



if __name__ == '__main__':

#remove whitespace so and uppercase to make comparison easy
    data = open('planned_courses.txt', 'r').read()
    courses = format_course_numbers(data.split(','))
    unmet_courses = list(set(REQUIRED_COURSES) - set(courses))
    courses_meeting_reqs = []

    if unmet_courses:
        print "Missing required courses."
        print "Unmet courses:\n{}".format("\n".join(unmet_courses))
    else:
        print "All required courses met."


    meet_one_of(courses, MATH_ONE_OF, courses_meeting_reqs, "Math")
    meet_one_of(courses, LITERATURE_ONE_OF, courses_meeting_reqs, "Literature")
    meet_one_of(courses, COMPUTER_SCIENCE_ONE_OF, courses_meeting_reqs, "Computer Science")
    meet_one_of(courses, SPEAKING_ONE_OF, courses_meeting_reqs, "Speaking")
    meet_one_of(courses, STEWARDSHIP_ONE_OF, courses_meeting_reqs, "Stewardship")

    meet_life_sci = []
    meet_phy_sci  = []
    meet_earth_sci = []
    for course in courses:
        if course in LIFE_SCIENCE:
            meet_life_sci.append(course)
        if course in PHYSICAL_SCIENCE:
            meet_phy_sci.append(course)
        if course in EARTH_SCIENCE:
            meet_earth_sci.append(course)

    if (len(meet_life_sci) +  len(meet_phy_sci)  + len(meet_earth_sci)) >= 2:
        # If we have duplicates appending the lists and changing them to a set 
        # should remove them. This is for when one class meets multiple reqs. 
        all_sci = set(meet_life_sci + meet_phy_sci + meet_earth_sci)
        if len(all_sci) >= 2:
            print "Science Requirement met."
        else:
            print "Does not meet science requirement."
    else:
        print "Does not meet science requirement."


    meet_civic_eng   = []
    meet_general_soc = []
    for course in courses:
        if course in CIVIC_ENGAGE:
            meet_civic_eng.append(course)
        if course in GENERAL_SOCIAL:
            meet_general_soc.append(course)

    if meet_civic_eng:
        soc_courses = meet_civic_eng + meet_general_soc

        prefixes = [course_prefix(course) for course in soc_courses]
        if len(set(prefixes)) >= 2:
            print "Meets Social Science Requirement."
        else:
            print "Does not meet social science requirement."
    else:
        print "Does not meet social science requirement."
