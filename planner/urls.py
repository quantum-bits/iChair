from django.conf.urls import include, url

from planner import views as myapp_views
from planner import api_views

urlpatterns = [
    #'planner.views',
    # https://stackoverflow.com/questions/38744285/django-urls-typeerror-view-must-be-a-callable-or-a-list-tuple-in-the-case-of-in
    url(r'^home/$', myapp_views.home, name='home'),

    url(r'^profile/$', myapp_views.profile, name='profile'),

    url(r'^deptloadsummary/$', myapp_views.department_load_summary, name='department_load_summary'),
    url(r'^coursesummary/(\d+)/$', myapp_views.course_summary, name='course_summary'),
    url(r'^allowdeletecourseconfirmation/$', myapp_views.allow_delete_course_confirmation, name='allow_delete_course_confirmation'),
    url(r'^updatecourseoffering/(\d+)/(\d+)/$', myapp_views.update_course_offering, name='update_course_offering'),
    url(r'^managecourseofferings/(\d+)/$', myapp_views.manage_course_offerings, name='manage_course_offerings'),
    url(r'^updateclassschedule/(\d+)/(\d+)/$', myapp_views.update_class_schedule, name='update_class_schedule'),
    url(r'^updatesemesterforcourseoffering/(\d+)/$', myapp_views.update_semester_for_course_offering, name='update_semester_for_course_offering'),
    url(r'^newclassschedule/(\d+)/(\d+)/$', myapp_views.new_class_schedule, name='new_class_schedule'),
    url(r'^weeklyschedule/$', myapp_views.weekly_schedule, name='weekly_schedule'),
    url(r'^weeklyscheduledeptsummary/$', myapp_views.weekly_course_schedule_entire_dept, name='weekly_course_schedule_entire_dept'),
    url(r'^dailyschedule/$', myapp_views.daily_schedule, name='daily_schedule'),
    url(r'^registrarschedule/(\d+)/$', myapp_views.registrar_schedule, name='registrar_schedule'),
    url(r'^registrarschedule/(\d+)/(\d+)/$', myapp_views.registrar_schedule, name='registrar_schedule'),
    url(r'^roomschedule/$', myapp_views.room_schedule, name='room_schedule'),
    url(r'^courseschedule/$', myapp_views.course_schedule, name='course_schedule'),
    url(r'^selectcourse/$', myapp_views.select_course, name='select_course'),
    url(r'^addcourseconfirmation/(\d+)/$', myapp_views.add_course_confirmation, name='add_course_confirmation'),
    url(r'^addcourse/(\d+)/$', myapp_views.add_course, name='add_course'),
    url(r'^addcourseoffering/(\d+)/(\d+)/$', myapp_views.add_course_offering, name='add_course_offering'),
    url(r'^updatecourse/(\d+)/$', myapp_views.update_course, name='update_course'),
    url(r'^deletecourse/(\d+)/$', myapp_views.delete_course, name='delete_course'),
    url(r'^deletecourseoffering/(\d+)/$', myapp_views.delete_course_offering, name='delete_course_offering'),
    url(r'^deletecourseconfirmation/(\d+)/$', myapp_views.delete_course_confirmation, name='delete_course_confirmation'),
    url(r'^updateotherload/(\d+)/$', myapp_views.update_other_load, name='update_other_load'),
    url(r'^updateroomstoview/(\d+)/$', myapp_views.update_rooms_to_view, name='update_rooms_to_view'),
    url(r'^updatefacultytoview/$', myapp_views.update_faculty_to_view, name='update_faculty_to_view'),
    url(r'^updatedepartmenttoview/$', myapp_views.update_department_to_view, name='update_department_to_view'),
    url(r'^updateyeartoview/(\d+)/$', myapp_views.update_year_to_view, name='update_year_to_view'),
    url(r'^updateloadstoview/(\d+)/$', myapp_views.update_loads_to_view, name='update_loads_to_view'),
    url(r'^updatefacultymember/(\d+)/$', myapp_views.update_faculty_member, name='update_faculty_member'),
    url(r'^addfacultymember/$', myapp_views.add_faculty, name='add_faculty'),
    url(r'^addfacultytoviewlist/$', myapp_views.add_faculty_to_view_list, name='add_faculty_to_view_list'),

    url(r'^bannercomparison/$', myapp_views.compare_with_banner, name='compare_with_banner'),
    url(r'^ajax/fetch-banner-comparison-data/$', api_views.banner_comparison_data, name='banner_comparison_data'),

    url(r'^copycourses/(\d+)/(\d+)/$', myapp_views.copy_courses, name='copy_courses'),
    url(r'^chooseyearforcoursecopy/$', myapp_views.choose_year_course_copy, name='choose_year_course_copy'),

    url(r'^generatepdf/$', myapp_views.generate_pdf, name='generate_pdf'),
    
    url(r'^notes/', myapp_views.display_notes, name='display_notes'),
    url(r'^addnote/', myapp_views.add_new_note, name='add_new_note'),
    url(r'^updateNote/(\d+)/$', myapp_views.update_note, name='update_note'),
    url(r'^deleteNote/(\d+)/$', myapp_views.delete_note, name='delete_note'),
    url(r'^exportdata/$', myapp_views.export_data, name='export_data'),
    url(r'^exportsummarydata/$', myapp_views.export_summary_data, name='export_summary_data'),
#    url(r'^exportcomplete/$', 'export_complete', name='export_complete')
    url(r'^search-form/$', myapp_views.search_form, name='search_form'),
    url(r'^search-form-time/$', myapp_views.search_form_time, name='search_form_time'),
    url(r'^gettingstarted/$', myapp_views.getting_started, name='getting_started'),
    url(r'^divtracker/(\d+)/$', myapp_views.open_close_div_tracker, name='open_close_div_tracker'),
    url(r'^alertregister/$', myapp_views.alert_register, name='alert_register'),
    url(r'^ajax/load-courses/$', api_views.load_courses, name='ajax_load_courses'),
    url(r'^ajax/add-faculty-view-list/$', api_views.update_view_list, name='ajax_update_view_list'),


]
