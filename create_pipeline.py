
from utilities.queues.progress_backend import Progress
from celery import chain
from celery.result import AsyncResult
from utilities.queues.tasks import make_meta, make_tifs, make_scenes
from time import sleep

if __name__ == '__main__':
    animal = 'DK55'
    channel = 1
    njobs = 3

    worker = chain(
        make_tifs.s(animal, channel, njobs),
        make_scenes.s(animal, njobs)
    ).apply_async()
    #worker = (create_meta.delay(animal, True))

    print(worker.status)
