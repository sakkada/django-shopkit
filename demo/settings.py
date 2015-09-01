# -*- coding:utf-8 -*-
import os

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

PROJECT_ROOT = os.path.dirname(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'dev.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': ''
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Moscow'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ru'
LANGUAGES = (
    ('en', u'English'),
    ('ru', u'Russian'),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'
STATIC_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = STATIC_URL + 'grappelli/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'm+q17zt_)tsu+-=9gi)4g%66rys*bn9rw5w*v$xxkh%dua*7_8'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
)

STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, "static"),
)


# Application definition
INSTALLED_APPS = (
    # apps required before django apps

    # contrib apps
    'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'django.contrib.sitemaps',
    #'django.contrib.webdesign',

    # project apps
    'main',

    # satchless shopkit apps

    'shopkit.product',
    'shopkit.contrib.product.category',
    #'shopkit.contrib.productset',
    #'shopkit.contact',
    'shopkit.cart',
    'shopkit.contrib.tax.flatgroups',
    'shopkit.contrib.stock.singlestore',
    'shopkit.order',
    'shopkit.contrib.checkout.multistep',
    #'shopkit.delivery',
    #'shopkit.contrib.delivery.simplepost',
    #'shopkit.payment',
    'shop.core',
    'shop.categories',
    'shop.products',
    'shop.carts',
    'shop.orders',
    'shop.checkouts',
    'shop.payments',

    # external apps
    #'versatileimagefield',
    #'babeldjango',
    'django_prices',
    #'emailit',
    'mptt',
    #'payments',
    #'selectable',
    #'materializecssform',
    #'rest_framework',
)

SATCHLESS_DEFAULT_CURRENCY = 'EUR'

SATCHLESS_PRODUCT_VIEW_HANDLERS = [
    'carts.handler.carts_handler',
]
SATCHLESS_ORDER_PARTITIONERS = [
    'satchless.contrib.order.partitioner.simple.SimplePhysicalPartitioner',
]
SATCHLESS_DELIVERY_PROVIDERS = [
    'satchless.contrib.delivery.simplepost.PostDeliveryProvider',
]
SATCHLESS_PAYMENT_PROVIDERS = [
    'demo_payments.PaymentsProvider',
]
SATCHLESS_DJANGO_PAYMENT_TYPES = (('dummy', _('Dummy Payment Provider')),)

INTERNAL_IPS = ['127.0.0.1']

try:
    execfile(os.path.join(PROJECT_ROOT, 'local_settings.py'))
except IOError:
    pass
