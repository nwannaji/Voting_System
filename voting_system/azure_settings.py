"""
Azure App Service specific settings overlay.
This file is loaded when running on Azure App Service.

To enable Azure settings, set the environment variable:
    AZURE_SETTING = 1
Or add this to your Azure App Service Configuration.

Alternatively, use Azure's "ConfiguationManager" to auto-detect Azure environment.
"""

import os
from decouple import config

def if_azure(setting, fallback):
    """Helper to use Azure app setting or fallback to local/env value."""
    return os.environ.get(setting, fallback)

# Azure-specific BASE_URL
BASE_URL = if_azure('BASE_URL', 'https://nba-idecide.azurewebsites.net')

# Azure App Service provides HTTPS through ARR cookie
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Trust Azure's reverse proxy
ALLOWED_HOSTS = ['*']  # Azure handles this via the custom domain/SSL binding

# For Azure Database for PostgreSQL - use environment variables set in Azure
# These will be set in Azure App Settings
# DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT are loaded from .env or Azure Config

# Azure File Storage for media files (optional)
# For production, consider using Azure Blob Storage
# AZURE_STORAGE_ACCOUNT_NAME = config('AZURE_STORAGE_ACCOUNT_NAME', default='')
# AZURE_STORAGE_ACCOUNT_KEY = config('AZURE_STORAGE_ACCOUNT_KEY', default='')
# AZURE_STORAGE_CONTAINER = 'media'

# Use Redis Cache on Azure Cache for Redis (optional)
# For production with multiple instances, use Azure Cache for Redis
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': f"redis://{config('REDIS_HOST')}:{config('REDIS_PORT')}",
#         'OPTIONS': {
#             'PASSWORD': config('REDIS_PASSWORD'),
#         }
#     }
# }

# Azure Logging - send to Application Insights or blob storage
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.environ.get('HOME', ''), 'logfiles', 'voting_app.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'votingApp': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'voteApp': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Health check endpoint for Azure
HEALTH_CHECK_PATH = '/health/'
