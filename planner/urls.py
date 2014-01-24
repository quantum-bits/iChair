from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    'planner.views',

    url(r'^home/$', 'home'),

    url(r'^profile/$', 'profile', name='profile'),

    url(r'^deptloadsummary/$', 'department_load_summary', name='department_load_summary'),
    url(r'^coursesummary/$', 'course_summary', name='course_summary'),
    url(r'^updatecourseoffering/(\d+)/$', 'update_course_offering', name='update_course_offering'),
    url(r'^managecourseofferings/(\d+)/$', 'manage_course_offerings', name='manage_course_offerings'),
    url(r'^updateclassschedule/(\d+)/$', 'update_class_schedule', name='update_class_schedule'),
    url(r'^newclassschedule/(\d+)/$', 'new_class_schedule', name='new_class_schedule'),
    url(r'^weeklyschedule/$', 'weekly_schedule', name='weekly_schedule'),
    url(r'^dailyschedule/$', 'daily_schedule', name='daily_schedule'),
    url(r'^registrarschedule/$', 'registrar_schedule', name='registrar_schedule'),
    url(r'^roomschedule/$', 'room_schedule', name='room_schedule'),
    url(r'^courseschedule/$', 'course_schedule', name='course_schedule'),
    url(r'^addcourse/$', 'add_course', name='add_course'),
    url(r'^updatecourse/(\d+)/$', 'update_course', name='update_course'),
    url(r'^deletecourse/(\d+)/$', 'delete_course', name='delete_course'),
    url(r'^deletecourseconfirmation/(\d+)/$', 'delete_course_confirmation', name='delete_course_confirmation'),
    url(r'^updateotherload/(\d+)/$', 'update_other_load', name='update_other_load'),
    url(r'^updateroomstoview/(\d+)/$', 'update_rooms_to_view', name='update_rooms_to_view'),
    url(r'^updatefacultytoview/(\d+)/$', 'update_faculty_to_view', name='update_faculty_to_view'),
    url(r'^updateyeartoview/(\d+)/$', 'update_year_to_view', name='update_year_to_view'),
    url(r'^updateloadstoview/(\d+)/$', 'update_loads_to_view', name='update_loads_to_view'),

    url(r'^copycourses/(\d+)/(\d+)/$', 'copy_courses', name='copy_courses'),
    url(r'^chooseyearforcoursecopy/$', 'choose_year_course_copy', name='choose_year_course_copy'),

    url(r'^notes/', 'display_notes', name='display_notes'),
    url(r'^addnote/', 'add_new_note', name='add_new_note'),
    url(r'^updateNote/(\d+)/$', 'update_note', name='update_note'),
    url(r'^deleteNote/(\d+)/$', 'delete_note', name='delete_note'),
    url(r'^exportdata/$', 'export_data', name='export_data'),
#    url(r'^exportcomplete/$', 'export_complete', name='export_complete')

)
