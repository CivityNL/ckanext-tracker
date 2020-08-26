from celery import Celery

app = Celery('tasks', broker='redis://localhost')


@app.task
def create(resource):
    print('Create' + resource)


@app.task
def update(resource):
    print('Update' + resource)


@app.task
def delete(resource):
    print('Delete' + resource)