CELERY_IMPORTS = ('lunaport_worker.tasks.check', )

BROKER_URL = 'amqp://lunaport:lunamq@localhost:5672/lunaport'

CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/2'
CELERY_TASK_RESULT_EXPIRES = 86400  # 1 day.

CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True

# Enables error emails.
CELERY_SEND_TASK_ERROR_EMAILS = True 

# Name and email addresses of recipients
ADMINS = (
 ("Greggy", "gregory.komissarov@gmail.com"),
)

# Email address used as sender (From field).
SERVER_EMAIL = "lunaport@domain.org"

## Mailserver configuration
EMAIL_HOST = "127.0.0.1"
EMAIL_PORT = 25
