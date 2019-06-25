from collections import namedtuple

CourseOfferingInfo = namedtuple("CourseOfferingInfo","number, name, load_hours, load_hour_list")

department = Department.objects.filter(abbrev='PEN')[0]
academic_year = 2013
#    acad_year = u'...............'
#    -> make sorted list of all courseofferings for this academic year
#    -> make sorted list of profnames
#    -> loop through courseofferings
#       -> loop through profnames
#          -> search to see if prof is offering that course
#          -> if so, add info

# the following lines select out semester objects for 2013...below we use a different approach
#    year_object=AcademicYear.objects.filter(begin_on__year='2013')[0]
#    semester_objects=year_object.semesters.all()




data_list_by_faculty=[]
for faculty in department.faculty.all():
#        faculty_name=course_data_list.append(faculty.last_name)
    for course_offering in faculty.course_offerings.all():
        if course_offering.semester.year.begin_on.year == academic_year:
            course_offering_info = CourseOfferingInfo(
                number = "{0} {1}".format(course_offering.course.subject, 
                                               course_offering.course.number),
                name = course_offering.course.title,
                load_hours = course_offering.load_available,
                load_hour_list = [1,2,3,4]
                )
            data_list_by_faculty.append([faculty.last_name, course_offering_info]) 
