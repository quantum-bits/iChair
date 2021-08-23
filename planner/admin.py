from django.contrib import admin
from planner.models import *
from planner.forms import RequirementForm

# using 'as' in order to disambiguate (saw this tip somewhere....)
from banner.models import Subject as BannerSubject
from banner.models import Course as BannerCourse
from banner.models import FacultyMember as BannerFacultyMember
from banner.models import CourseOffering as BannerCourseOffering
from banner.models import OfferingInstructor as BannerOfferingInstructor
from banner.models import ScheduledClass as BannerScheduledClass
from banner.models import CourseOfferingComment as BannerCourseOfferingComment
from banner.models import SemesterCodeToImport as BannerSemesterCodeToImport
from banner.models import SubjectToImport as BannerSubjectToImport
from banner.models import Building as BannerBuilding
from banner.models import Room as BannerRoom
from banner.models import DeliveryMethod as BannerDeliveryMethod

class MultiDBModelAdmin(admin.ModelAdmin):
    # https://docs.djangoproject.com/en/2.2/topics/db/multi-db/
    # A handy constant for the name of the alternate database.
    using = 'banner'

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'banner' database.
        obj.save(using=self.using)

    def delete_model(self, request, obj):
        # Tell Django to delete objects from the 'banner' database
        obj.delete(using=self.using)

    def get_queryset(self, request):
        # Tell Django to look for objects on the 'banner' database.
        return super().get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'banner' database.
        return super().formfield_for_foreignkey(db_field, request, using=self.using, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'banner' database.
        return super().formfield_for_manytomany(db_field, request, using=self.using, **kwargs)


class MultiDBTabularInline(admin.TabularInline):
    using = 'banner'

    def get_queryset(self, request):
        # Tell Django to look for inline objects on the 'banner' database.
        return super().get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'banner' database.
        return super().formfield_for_foreignkey(db_field, request, using=self.using, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'banner' database.
        return super().formfield_for_manytomany(db_field, request, using=self.using, **kwargs)


class BannerSubjectAdmin(MultiDBModelAdmin):
    search_fields = ('abbrev',)
    list_display = ('abbrev',)

class BannerCourseAdmin(MultiDBModelAdmin):
    search_fields = ('subject', 'number', 'title',)
    list_display = ('subject', 'number', 'title', 'credit_hours',)

class BannerBuildingAdmin(MultiDBModelAdmin):
    search_fields = ('abbrev',)
    list_display = ('abbrev', 'name',)

class BannerRoomAdmin(MultiDBModelAdmin):
    search_fields = ('number', 'building',)
    list_display = ('building', 'number', 'capacity','is_active',)

class BannerDeliveryMethodAdmin(MultiDBModelAdmin):
    search_fields = ('code', 'description',)
    list_display = ('description', 'code',)

class BannerSemesterCodeToImportAdmin(MultiDBModelAdmin):
    list_display = ('term_code', 'allow_room_requests')

class BannerFacultyMemberAdmin(MultiDBModelAdmin):
    search_fields = ('pidm', 'first_name', 'last_name', 'formal_first_name', 'middle_name',)
    list_display = ('pidm', 'first_name', 'last_name', 'formal_first_name', 'middle_name',)

class BannerOfferingInstructorInline(MultiDBTabularInline):
    model = BannerOfferingInstructor
    extra = 1

class BannerCourseOfferingCommentInline(MultiDBTabularInline):
    model = BannerCourseOfferingComment
    extra = 1

class BannerCourseOfferingAdmin(MultiDBModelAdmin):
    inlines = (BannerOfferingInstructorInline, BannerCourseOfferingCommentInline,)
    list_display = ('course', 'campus', 'crn', 'term_code', 'semester_fraction','max_enrollment', 'delivery_method')
    # https://blndxp.wordpress.com/2017/04/11/django-amdin-related-field-got-invalid-lookup-icontains/
    search_fields = ('course__title','course__number','term_code','delivery_method__description','campus',)

class BannerScheduledClassAdmin(admin.ModelAdmin):
    list_display = ('course_offering','day','begin_at','end_at')

class RequirementAdmin(admin.ModelAdmin):
    form = RequirementForm

class DeltaCourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('crn', 'course_offering', 'semester', 'requested_action', 'update_meeting_times', 'update_instructors', 'update_semester_fraction','update_max_enrollment','update_delivery_method',)

class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'banner_code',)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'department','number', 'credit_hours',)
    search_fields = ('title', 'number',)
    filter_horizontal = ('schedule_semester','prereqs','coreqs',)

class BannerTitleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course',)
    search_fields = ('title',)

class RequirementBlockAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    filter_horizontal = ('courselist',)

class MajorAdmin(admin.ModelAdmin):
    search_fields = ('name', 'department__name',)

class StudentAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'entering_year',)

class AdvisingNoteAdmin(admin.ModelAdmin):
    list_display = ('student','note',)

class NoteAdmin(admin.ModelAdmin):
    list_display = ('department','note',)

class TransferCourseAdmin(admin.ModelAdmin):
    list_display = ('name','number','student','equivalentcourse',)

class DegreeProgramAdmin(admin.ModelAdmin):
    search_fields = ('name','major__name',)

class DegreeProgramCourseAdmin(admin.ModelAdmin):
    search_fields = ('degree_program__name',)

class OfferingInstructorInline(admin.TabularInline):
    model = OfferingInstructor
    extra = 1

class OfferingInstructorAdmin(admin.ModelAdmin):
    list_display = ('instructor','load_credit','course_offering',)

class FacultyMemberAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'pidm', 'department', 'number_course_offerings', 'created_at',)
    search_fields = ('last_name','first_name', 'pidm',)

class CourseOfferingPublicCommentInline(admin.TabularInline):
    model = CourseOfferingPublicComment
    extra = 1

class CourseOfferingAdmin(admin.ModelAdmin):
    inlines = (OfferingInstructorInline, CourseOfferingPublicCommentInline,)
    list_display = ('course','crn','semester','delivery_method',)
    # https://blndxp.wordpress.com/2017/04/11/django-amdin-related-field-got-invalid-lookup-icontains/
    search_fields = ('course__title','course__number','semester__name__name', 'semester__banner_code', 'delivery_method__description',)
    
class ClassMeetingAdmin(admin.ModelAdmin):
    list_display = ('course_offering','held_on','begin_at','end_at','instructor',)

class ScheduledClassAdmin(admin.ModelAdmin):
    list_display = ('course_offering','day','begin_at','end_at','comment',)

class RoomAdmin(admin.ModelAdmin):
    list_display = ('building','number','capacity','inactive_after',)

class DeliveryMethodAdmin(admin.ModelAdmin):
    search_fields = ('code', 'description',)
    list_display = ('description', 'code',)

class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name','abbrev',)

class OtherLoadTypeAdmin(admin.ModelAdmin):
    search_fields = ('load_type',)
    list_display = ('load_type',)

class OtherLoadAdmin(admin.ModelAdmin):
    list_display = ('instructor','semester','load_credit','load_type',)

class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user','department_to_view','academic_year_to_view','permission_level',)
    filter_horizontal = ('rooms_to_view','faculty_to_view','other_load_types_to_view',)

class MessageFragmentAdmin(admin.ModelAdmin):
    list_display = ('sequence_number','indentation_level','message','fragment',)
    
class MessageAdmin(admin.ModelAdmin):
    list_display = ('message_type','updated_at','department','year','dismissed')

    # https://blndxp.wordpress.com/2017/04/11/django-amdin-related-field-got-invalid-lookup-icontains/
    search_fields = ('department','year',)
    

admin.site.register(AcademicYear)
admin.site.register(AdvisingNote)
admin.site.register(Note, NoteAdmin)
admin.site.register(Building, BuildingAdmin)
admin.site.register(ClassMeeting, ClassMeetingAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(BannerTitle, BannerTitleAdmin)
admin.site.register(CourseAttribute)
admin.site.register(CourseOfferingPublicComment)
admin.site.register(CourseOffering, CourseOfferingAdmin)
admin.site.register(DegreeProgram, DegreeProgramAdmin)
admin.site.register(DegreeProgramCourse, DegreeProgramCourseAdmin)
admin.site.register(Department)
admin.site.register(FacultyMember, FacultyMemberAdmin)
admin.site.register(Major, MajorAdmin)
admin.site.register(Minor)
admin.site.register(OfferingInstructor, OfferingInstructorAdmin)
admin.site.register(OtherLoadType, OtherLoadTypeAdmin)
admin.site.register(OtherLoad, OtherLoadAdmin)
admin.site.register(Requirement, RequirementAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(School)
admin.site.register(ScheduledClass, ScheduledClassAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(SemesterName)
admin.site.register(Student, StudentAdmin)
admin.site.register(Subject)
admin.site.register(TransferCourse)
admin.site.register(University)
admin.site.register(Constraint)
admin.site.register(UserPreferences, UserPreferencesAdmin)
admin.site.register(DeltaCourseOffering, DeltaCourseOfferingAdmin)
admin.site.register(BannerSubject, BannerSubjectAdmin)
admin.site.register(BannerCourse, BannerCourseAdmin)
admin.site.register(BannerFacultyMember, BannerFacultyMemberAdmin)
admin.site.register(BannerCourseOffering, BannerCourseOfferingAdmin)
admin.site.register(BannerScheduledClass, BannerScheduledClassAdmin)
admin.site.register(BannerSemesterCodeToImport, BannerSemesterCodeToImportAdmin)
admin.site.register(BannerSubjectToImport)
admin.site.register(MessageFragment, MessageFragmentAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(BannerBuilding, BannerBuildingAdmin)
admin.site.register(BannerRoom, BannerRoomAdmin)
admin.site.register(BannerDeliveryMethod, BannerDeliveryMethodAdmin)
admin.site.register(DeliveryMethod, DeliveryMethodAdmin)


