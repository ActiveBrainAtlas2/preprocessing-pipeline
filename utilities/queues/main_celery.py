from celery import Celery

app = Celery('utilities.queues')
app.config_from_object('utilities.queues.celeryconfig')


# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)
"""
Commands:
celery multi start w1 -A utilities.queues.tasks -l INFO --pidfile=utilities/queues/pid/%n.pid --logfile=utilities/queues/log/%n%I.log
celery multi restart w1 -A utilities.queues.tasks -l INFO --pidfile=utilities/queues/pid/%n.pid --logfile=utilities/queues/log/%n%I.log
celery multi stopwait w1 -A utilities.queues.tasks -l INFO --pidfile=utilities/queues/pid/%n.pid --logfile=utilities/queues/log/%n%I.log
celery -A utilities.queues.tasks inspect active
"""

