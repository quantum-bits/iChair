from django.conf.urls import include, url

from planner import views as myapp_views
from planner import api_views, api_viewsets
from banner import api_viewsets as banner_api_viewsets

from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy

from rest_framework import routers

router = routers.DefaultRouter()
#router.register(r'api/users', api_viewsets.UserViewSet)
router.register(r'api/delta-course-offerings', api_viewsets.DeltaCourseOfferingViewSet)
router.register(r'api/rooms', api_viewsets.RoomViewSet)

urlpatterns = [
    #'planner.views',
    # https://stackoverflow.com/questions/38744285/django-urls-typeerror-view-must-be-a-callable-or-a-list-tuple-in-the-case-of-in
    url(r'^home/$', myapp_views.home, name='home'),

    url(r'^profile/$', myapp_views.profile, name='profile'),

    url(r'^deptloadsummary/$', myapp_views.department_load_summary, name='department_load_summary'),
    url(r'^addsandboxyear/$', myapp_views.add_sandbox_year, name='add_sandbox_year'),
    url(r'^updatesandboxyear/(\d+)/$', myapp_views.update_sandbox_year, name='update_sandbox_year'),
    url(r'^managesandboxyears/$', myapp_views.manage_sandbox_years, name='manage_sandbox_years'),
    url(r'^deletesandboxyear/(\d+)/$', myapp_views.mark_sandbox_year_as_deleted, name='delete_sandbox_year'),
    url(r'^coursesummary/$', myapp_views.course_summary, name='course_summary'),
    url(r'^coursesummary/(\d+)/$', myapp_views.course_summary, name='course_summary'),
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
    url(r'^deletecourseoffering/(\d+)/$', myapp_views.delete_course_offering, name='delete_course_offering'),
    url(r'^updateotherload/(\d+)/$', myapp_views.update_other_load, name='update_other_load'),
    url(r'^updateotherloadthisfaculty/(\d+)/$', myapp_views.update_other_load_this_faculty, name='update_other_load_this_faculty'),
    url(r'^updateroomstoview/(\d+)/$', myapp_views.update_rooms_to_view, name='update_rooms_to_view'),
    url(r'^updatefacultytoview/$', myapp_views.update_faculty_to_view, name='update_faculty_to_view'),
    url(r'^updatedepartmenttoview/$', myapp_views.update_department_to_view, name='update_department_to_view'),
    url(r'^updateyeartoview/(\d+)/$', myapp_views.update_year_to_view, name='update_year_to_view'),
    url(r'^updateloadstoview/(\d+)/$', myapp_views.update_loads_to_view, name='update_loads_to_view'),
    url(r'^updatefacultymember/(\d+)/$', myapp_views.update_faculty_member, name='update_faculty_member'),
    url(r'^addfacultymember/$', myapp_views.add_faculty, name='add_faculty'),
    url(r'^addfacultytoviewlist/$', myapp_views.add_faculty_to_view_list, name='add_faculty_to_view_list'),

    url(r'^bannercomparison/$', myapp_views.compare_with_banner, name='compare_with_banner'),
    url(r'^ajax/dismiss-message/$', api_views.dismiss_message, name='dismiss_message'),
    url(r'^ajax/set-semester-to-view/$', api_views.set_semester_to_view, name='set_semester_to_view'),
    url(r'^ajax/fetch-semesters-and-extra-departmental-courses/$', api_views.fetch_semesters_and_extra_departmental_courses, name='fetch_semesters_and_extra_departmental_courses'),
    #url(r'^ajax/fetch-courses-to-be-aligned/$', api_views.fetch_courses_to_be_aligned, name='fetch_courses_to_be_aligned'),
    url(r'^ajax/get-courses/$', api_views.get_courses, name='get_courses'),
    url(r'^ajax/fetch-banner-comparison-data/$', api_views.banner_comparison_data, name='banner_comparison_data'),
    url(r'^ajax/update-class-schedule/$', api_views.update_class_schedule_api, name='update_class_schedule_api'),
    url(r'^ajax/update-public-comments/$', api_views.update_public_comments_api, name='update_public_comments_api'),
    url(r'^ajax/create-update-delete-note-for-registrar-or-self/$', api_views.create_update_delete_note_for_registrar_or_self_api, name='create_update_delete_note_for_registrar_or_self_api'),
    url(r'^ajax/create-update-courses/$', api_views.create_update_courses, name='create_update_courses'),
    url(r'^ajax/delete-course-offering/$', api_views.delete_course_offering, name='delete_course_offering'),
    url(r'^ajax/create-course-offering/$', api_views.create_course_offering, name='create_course_offering'),
    url(r'^ajax/generate-update-delta/$', api_views.generate_update_delta, name='generate_update_delta'),
    url(r'^ajax/delete-delta/$', api_views.delete_delta, name='delete_delta'),
    url(r'^ajax/copy-course-offering-data-to-ichair/$', api_views.copy_course_offering_data_to_ichair, name='copy_course_offering_data_to_ichair'),
    url(r'^ajax/update-instructors-for-course-offering/$', api_views.update_instructors_for_course_offering, name='update_instructors_for_course_offering'),
    url(r'^ajax/generate-pdf/$', api_views.generate_pdf, name='generate_pdf'),
    url(r'^scheduleeditspdf/(\d+)/$', myapp_views.view_pdf, name='view_pdf'),

    url(r'^copycourses/(\d+)/(\d+)/$', myapp_views.copy_courses, name='copy_courses'),
    url(r'^copyadminloads/(\d+)/(\d+)/$', myapp_views.copy_admin_loads, name='copy_admin_loads'),
    url(r'^copyadminloads/(\d+)/$', myapp_views.copy_admin_loads, name='copy_admin_loads'),
    url(r'^copycourseoffering/(\d+)/$', myapp_views.copy_course_offering, name='copy_course_offering'),
    url(r'^chooseyearforcoursecopy/$', myapp_views.choose_year_course_copy, name='choose_year_course_copy'),
    url(r'^chooseyearadminloadcopy/(\d+)/$', myapp_views.choose_year_admin_load_copy, name='choose_year_admin_load_copy'),
    url(r'^chooseyearadminloadcopy/$', myapp_views.choose_year_admin_load_copy, name='choose_year_admin_load_copy'),

    url(r'^generatepdf/$', myapp_views.generate_pdf, name='generate_pdf'),
    
    url(r'^notes/', myapp_views.display_notes, name='display_notes'),
    url(r'^messages/', myapp_views.display_messages, name='display_messages'),
    url(r'^deleteMessage/(\d+)/$', myapp_views.delete_message, name='delete_message'),
    url(r'^addnote/', myapp_views.add_new_note, name='add_new_note'),
    url(r'^updateNote/(\d+)/$', myapp_views.update_note, name='update_note'),
    url(r'^deleteNote/(\d+)/$', myapp_views.delete_note, name='delete_note'),
    url(r'^exportdataform/$', myapp_views.export_data_form, name='export_data_form'),
    url(r'^exportdata/$', myapp_views.export_data, name='export_data'),
    url(r'^exportsummarydata/$', myapp_views.export_summary_data, name='export_summary_data'),
    url(r'^search-form/$', myapp_views.search_form, name='search_form'),
    url(r'^search-form-time/$', myapp_views.search_form_time, name='search_form_time'),
    url(r'^gettingstarted/$', myapp_views.getting_started, name='getting_started'),
    url(r'^divtracker/(\d+)/$', myapp_views.open_close_div_tracker, name='open_close_div_tracker'),
    url(r'^alertregister/$', myapp_views.alert_register, name='alert_register'),
    url(r'^ajax/load-courses/$', api_views.load_courses, name='ajax_load_courses'),
    url(r'^ajax/add-faculty-view-list/$', api_views.update_view_list, name='ajax_update_view_list'),

    # https://ordinarycoders.com/blog/article/django-password-reset
    # https://github.com/macropin/django-registration
    path('password/reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             success_url=reverse_lazy('auth_password_reset_complete')),
         name='auth_password_reset_confirm'),
    path('password/change/',
         auth_views.PasswordChangeView.as_view(
             success_url=reverse_lazy('auth_password_change_done')),
         name='auth_password_change'),
    path('password/change/done/',
         auth_views.PasswordChangeDoneView.as_view(),
         name='auth_password_change_done'),
    path('password/reset/',
         auth_views.PasswordResetView.as_view(
             success_url=reverse_lazy('auth_password_reset_done')),
         name='auth_password_reset'),
    path('password/reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(),
         name='auth_password_reset_complete'),
    path('password/reset/done/',
         auth_views.PasswordResetDoneView.as_view(),
         name='auth_password_reset_done'),
    path(r'api/semester-code-to-imports/', banner_api_viewsets.SemesterCodeToImportView.as_view(), name='semester_code_to_imports'),
    path('api/departments/', api_viewsets.DepartmentView.as_view(), name='departments'),
    path('api/filtered-delta-course-offerings/', api_viewsets.DeltaCourseOfferingList.as_view(), name='delta_course_offerings'),
    
]

urlpatterns += router.urls