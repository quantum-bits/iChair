from django.contrib import admin
from planner.models import *
from planner.forms import RequirementForm


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
    search_fields = ('name', 'department',)

class StudentAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'entering_year',)

class AdvisingNoteAdmin(admin.ModelAdmin):
    list_display = ('student','note',)

class NoteAdmin(admin.ModelAdmin):
    list_display = ('department','note',)

class TransferCourseAdmin(admin.ModelAdmin):
    list_display = ('name','number','student','equivalentcourse',)


class DegreeProgramAdmin(admin.ModelAdmin):
    search_fields = ('name','major',)

class DegreeProgramCourseAdmin(admin.ModelAdmin):
    search_fields = ('degree_program',)

class OfferingInstructorInline(admin.TabularInline):
    model = OfferingInstructor
    extra = 1

class OfferingInstructorAdmin(admin.ModelAdmin):
    list_display = ('instructor','load_credit','course_offering',)

class FacultyMemberAdmin(admin.ModelAdmin):
    inlines = (OfferingInstructorInline,)

class CourseOfferingAdmin(admin.ModelAdmin):
    inlines = (OfferingInstructorInline,)
    list_display = ('course','semester',)
    search_fields = ('course','semester',)

class ClassMeetingAdmin(admin.ModelAdmin):
    list_display = ('course_offering','held_on','begin_at','end_at','room','instructor',)

class ScheduledClassAdmin(admin.ModelAdmin):
    list_display = ('course_offering','day','begin_at','end_at','room','comment',)

class RoomAdmin(admin.ModelAdmin):
    list_display = ('building','number',)

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


