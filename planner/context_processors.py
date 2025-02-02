from .models import *

def add_variable_to_context(request):
    """
    Returns user_is_dept_scheduler, which functions more or less the same as can_edit, which is in many of the views.
    The advantage of using user_is_dept_scheduler is that it is accessible in base.html.  In principle, could
    remove can_edit in all of the views now.

    Also returns is_sandbox_year.  In principle could probably use this in place of accessing it via the year in some of the pages.
    """
    # https://stackoverflow.com/questions/4642596/how-do-i-check-whether-this-user-is-anonymous-or-actually-a-user-on-my-system
    # https://stackoverflow.com/questions/34902707/how-can-i-pass-data-to-django-layouts-like-base-html-without-having-to-provi?rq=1

    user = request.user

    is_sandbox_year = False

    if user.is_anonymous:
        # in this case, the user is AnonymousUser (i.e., not logged in)
        user_is_dept_scheduler = False
        user_is_super = False
    else:
        if len(user.user_preferences.all()) == 1: # have to be careful here, or can crash the admin site...!
            user_preferences = user.user_preferences.all()[0]
            user_is_dept_scheduler = user_preferences.permission_level == UserPreferences.DEPT_SCHEDULER
            user_is_super = user_preferences.permission_level == UserPreferences.SUPER
            is_sandbox_year = user_preferences.academic_year_to_view.is_sandbox
        else:
            user_is_dept_scheduler = False
            user_is_super = False

    return {
        'can_edit': user_is_dept_scheduler,
        'is_super': user_is_super,
        'is_sandbox_year': is_sandbox_year
    }