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

class BannerFacultyMemberAdmin(MultiDBModelAdmin):
    search_fields = ('pidm', 'first_name', 'last_name', 'formal_first_name', 'middle_name',)
    list_display = ('pidm', 'first_name', 'last_name', 'formal_first_name', 'middle_name',)

class BannerOfferingInstructorInline(MultiDBTabularInline):
    model = BannerOfferingInstructor
    extra = 1

class BannerCourseOfferingAdmin(MultiDBModelAdmin):
    inlines = (BannerOfferingInstructorInline,)
    list_display = ('course', 'crn', 'term_code', 'semester_fraction','max_enrollment', 'banner_comment',)
    search_fields = ('course__title','course__number','term_code',)

class BannerScheduledClassAdmin(admin.ModelAdmin):
    list_display = ('course_offering','day','begin_at','end_at',)

class RequirementAdmin(admin.ModelAdmin):
    form = RequirementForm

class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'year')

class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'department','number', 'credit_hours',)
    search_fields = ('title', 'number',)
    filter_horizontal = ('schedule_semester','prereqs','coreqs',)

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

class CourseOfferingAdmin(admin.ModelAdmin):
    inlines = (OfferingInstructorInline,)
    list_display = ('course','crn','semester',)
    # https://blndxp.wordpress.com/2017/04/11/django-amdin-related-field-got-invalid-lookup-icontains/
    search_fields = ('course__title','course__number','semester__name__name', 'semester__banner_code',)

class ClassMeetingAdmin(admin.ModelAdmin):
    list_display = ('course_offering','held_on','begin_at','end_at','room','instructor',)

class ScheduledClassAdmin(admin.ModelAdmin):
    list_display = ('course_offering','day','begin_at','end_at','room','comment',)

class RoomAdmin(admin.ModelAdmin):
    list_display = ('building','number','capacity',)

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

admin.site.register(AcademicYear)
admin.site.register(AdvisingNote)
admin.site.register(Note, NoteAdmin)
admin.site.register(Building, BuildingAdmin)
admin.site.register(ClassMeeting, ClassMeetingAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseAttribute)
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
admin.site.register(BannerSubject, BannerSubjectAdmin)
admin.site.register(BannerCourse, BannerCourseAdmin)
admin.site.register(BannerFacultyMember, BannerFacultyMemberAdmin)
admin.site.register(BannerCourseOffering, BannerCourseOfferingAdmin)
admin.site.register(BannerScheduledClass, BannerScheduledClassAdmin)


