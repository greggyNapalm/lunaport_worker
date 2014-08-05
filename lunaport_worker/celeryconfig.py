CELERY_IMPORTS = (
    'lunaport_worker.tasks.check',
    'lunaport_worker.tasks.pullHosts',
    'lunaport_worker.tasks.hooks',
    'lunaport_worker.schedule',
)

BROKER_URL = 'amqp://lunaport:lunamq@localhost:5672/lunaport'

CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/2'
CELERY_TASK_RESULT_EXPIRES = 86400  # 1 day.

CELERYD_MAX_TASKS_PER_CHILD = 5

CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True

# Enables error emails.
CELERY_SEND_TASK_ERROR_EMAILS = True 

# Name and email addresses of recipients
ADMINS = (
 ("Greggy", "gregory.komissarov@gmail.com"),
)

# Email address used as sender (From field).
SERVER_EMAIL = "devnull@domain.org"

## Mailserver configuration
EMAIL_HOST = "127.0.0.1"
EMAIL_PORT = 25
