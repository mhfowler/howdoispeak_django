from mhfowler.settings.common import *
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mhfowler',
        # The following settings are not used with sqlite3:
        'USER': 'mhfowler',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'mhfowler.cssrhulnfuuk.us-east-1.rds.amazonaws.com',
        'PORT': SECRETS_DICT['databases']['live']['HOST'],                      # Set to empty string for default.
    }
}