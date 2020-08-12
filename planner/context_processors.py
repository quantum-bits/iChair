from .models import *

def add_variable_to_context(request):
    """
    Returns user_is_dept_scheduler, which functions more or less the same as can_edit, which is in many of the views.
    The advantage of using user_is_dept_scheduler is that it is accessible in base.html.  In principle, could
    remove can_edit in all of the views now.
    """
    # https://stackoverflow.com/questions/4642596/how-do-i-check-whether-this-user-is-anonymous-or-actually-a-user-on-my-system
    # https://stackoverflow.com/questions/34902707/how-can-i-pass-data-to-django-layouts-like-base-html-without-having-to-provi?rq=1

    user = request.user

    if user.is_anonymous:
        # in this case, the user is AnonymousUser (i.e., not logged in)
        user_is_dept_scheduler = False
    else:
        user_preferences = user.user_preferences.all()[0]
        user_is_dept_scheduler = user_preferences.permission_level == UserPreferences.DEPT_SCHEDULER

    return {
        'user_is_dept_scheduler': user_is_dept_scheduler
    }