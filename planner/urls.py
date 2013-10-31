from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    'planner.views',

    url(r'^home/$', 'home'),

    url(r'^register/$', 'student_registration', name='register'),
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
    url(r'^addcourse/$', 'add_course', name='add_course'),
    url(r'^updatecourse/(\d+)/$', 'update_course', name='update_course'),
    url(r'^deletecourse/(\d+)/$', 'delete_course', name='delete_course'),
    url(r'^deletecourseconfirmation/(\d+)/$', 'delete_course_confirmation', name='delete_course_confirmation'),

    url(r'^notes/', 'display_notes', name='display_notes'),
    url(r'^addnote/', 'add_new_note', name='add_new_note'),
    url(r'^updateNote/(\d+)/$', 'update_note', name='update_note'),
    url(r'^deleteNote/(\d+)/$', 'delete_note', name='delete_note'),

    url(r'^changemajor/(\d+)/$', 'update_major', name='update_major'),
    url(r'^updatesemester/(\d+)/$', 'update_student_semester', name='update_student_semester'),
    url(r'^fouryearplan/$', 'display_four_year_plan', name='four_year_plan'),
    url(r'^graduationaudit/$', 'display_grad_audit', name='grad_audit'),

    url(r'^addcreateyourowncourse/(\d+)/$', 'add_create_your_own_course', name='add_cyoc'),
    url(r'^deletecyoc/(\d+)/(\d+)/(\d+)/$', 'delete_create_your_own_course', name='delete_cyoc'),
    url(r'^updatecyoc/(\d+)/(\d+)/$', 'update_create_your_own_course', name='update_cyoc'),

    url(r'^deletecourse/(\d+)/(\d+)/(\d+)/$', 'delete_course_inside_SSCObject', name='delete_course'),
    url(r'^movecoursetonewsemester/(\d+)/(-?\d+)/(\d+)/(\d+)/$', 'move_course_to_new_SSCObject', name='move_course'),

    url(r'^changeadvisee/(\d+)/$', 'update_advisee', name='update_advisee'),
    url(r'^search/$', 'search', name='search'),
    url(r'^viewstudents/(\d+)/(\d+)/$', 'view_enrolled_students', name='view_students'),


)
