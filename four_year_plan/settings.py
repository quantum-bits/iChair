# Django settings for iGrad project.

from .run_mode import RunMode
from .secret import SECRET_KEY, BANNER_DB, ICHAIR_DB, PROD_CORS_ALLOWED_ORIGINS
from django.conf import global_settings
import os.path

run_mode = RunMode('dev', debug_toolbar=False)

DEBUG = run_mode.dev
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Tom Nurkkala', 'tnurkkala@cse.taylor.edu'),
)

MANAGERS = ADMINS
#https://stackoverflow.com/questions/4919600/django-project-root-self-discovery

if run_mode.dev:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ICHAIR_DB #'ichair.db',
        },
        'banner': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BANNER_DB #'banner.db'
        }
    }
    DATABASE_ROUTERS = ['banner.banner_router.BannerRouter']
elif run_mode.prod:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'igrad',
            'USER': 'postgres',
            'PASSWORD': 'igrad',
            'HOST': 'localhost',
            'PORT': '5432',
            }
        }
else:
    raise RuntimeError("No database configured.")

# KK (6/14/21):
# Setting DEFAULT_AUTO_FIELD explicitly was added by KK when upgrading from Django 2.2.20 to Django 3.2.4.  
# The new default for auto-created primary keys is going to be BigAutoField (which maxes out at a huge integer);
# prior to this, the default was AutoField, which maxes out at a smaller, but still huge, integer.
# At some point we may want to consider switching over to BigAutoField, but it's probably fine 
# for now.  The current issue is that automatically created through-tables would need to be migrated
# somewhat manually, and it's not clear to me if that is worth the headache at the moment.
# 
# https://docs.djangoproject.com/en/3.2/releases/3.2/#customizing-type-of-auto-created-primary-keys
# https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['127.0.0.1', 'ichair.cse.taylor.edu']
# https://forum.djangoproject.com/t/cant-start-the-development-server-at-http-127-0-0-1-8000/1934
# if the development localhost address is changed at some point, need to update a conditional block in views.add_faculty(...)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Indiana/Indianapolis'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# some discussion on how SITE_ID is used: https://github.com/maxking/docker-mailman/issues/12
# the site name is saved in the database
SITE_ID = 1

# this overrides the DEFAULT_FROM_EMAIL in global_settings.py
DEFAULT_FROM_EMAIL = 'no-reply@taylor.edu'

# https://docs.djangoproject.com/en/4.0/topics/auth/passwords/#password-validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = run_mode.path_to('static_root')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    run_mode.path_to('shared'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# add request to every context
#TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
#    "django.core.context_processors.request",)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

#MIDDLEWARE_CLASSES = (
#    'django.middleware.common.CommonMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.messages.middleware.MessageMiddleware',
#    # Uncomment the next line for simple clickjacking protection:
#    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
#)

ROOT_URLCONF = 'four_year_plan.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'four_year_plan.wsgi.application'

if run_mode.dev:
    CORS_ALLOWED_ORIGINS = [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]
elif run_mode.prod:
    CORS_ALLOWED_ORIGINS = PROD_CORS_ALLOWED_ORIGINS
else:
    raise RuntimeError("CORS allowed origins not configured correctly.")


#TEMPLATE_DIRS = (
#    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
#    # Always use forward slashes, even on Windows.
#    # Don't forget to use absolute paths, not relative paths.
#    run_mode.path_to('shared/templates'),
#)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [run_mode.path_to('shared/templates'), 'planner/email/'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'planner.context_processors.add_variable_to_context',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    #'planner.models.ProxiedModelBackend',
    'django.contrib.auth.backends.ModelBackend',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'planner',
    'banner',
    'django_crontab',
    'rest_framework',
    'corsheaders',
)

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}


CRONJOBS = [
    ('0 4 * * *', 'django.core.management.call_command', ['warehouse'], {}, '>> warehouse.log')
]

# email...
# use this for production:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# use this for development:
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

if run_mode.debug_toolbar:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware') #KK: not sure about this
    INTERNAL_IPS = ('127.0.0.1',) # if this is changed at some point, need to update a conditional block in views.add_faculty(...)
    DEBUG_TOOLBAR_CONFIG = { 'INTERCEPT_REDIRECTS': False }

LOGIN_REDIRECT_URL = 'department_load_summary'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
