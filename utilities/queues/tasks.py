from utilities.queues.main_celery import app



@app.task
def creation():
    return 'Starting creation'


@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y


@app.task
def xsum(numbers):
    return sum(numbers)
