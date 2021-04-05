from celery import Celery

app = Celery('hello', broker='amqp://guest@localhost//')
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'


@app.task
def hello():
    return 'hello world'