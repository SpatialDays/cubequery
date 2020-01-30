import logging
import os

from celery import Celery
from celery.result import AsyncResult
from celery.states import PENDING
from flask import Flask, request, abort, render_template, jsonify

from cubequery import validate_app_key, get_config
from cubequery.packages import find_available_tasks, is_valid_task, load_task_instance, find_modules

config = {
    "DEBUG": True,  # TODO: change for prod deployments
}

template_dir = os.path.abspath('./webroot/templates')
static_dir = os.path.abspath('./webroot/static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config.from_mapping(config)

redis_url = get_config("Redis", "url")
celery_app = Celery('tasks', backend=redis_url, broker=redis_url)
celery_app.conf.JOBTASTIC_CACHE = redis_url

packages = [m.replace("/", ".") for m in find_modules("cubequery.tasks")]
celery_app.autodiscover_tasks(packages=packages, related_name="", force=True)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/describe', methods=['GET'])
def describe():
    if not validate_app_key(request):
        abort(403)

    result = find_available_tasks()

    return jsonify(result)


@app.route('/task/<task_id>', methods=['GET'])
def task_id(task_id):
    if not validate_app_key(request):
        abort(403)

    logging.info(f"looking up task by id {task_id}")
    entry = AsyncResult(task_id, app=celery_app)

    # weirdly tasks can expire from the celery queue.
    # Unknown ids return a status of pending but also not ready and not failed. So ...
    if entry.status == PENDING and not entry.ready() and not entry.failed():
        return abort(404)
    # TODO: change this around to have a useful structure.
    return entry.__dict__


@app.route('/task/', methods=['GET'])
def all_tasks():
    if not validate_app_key(request):
        abort(403)

    logging.info("looking up all tasks...")
    # note there must be a worker running or this won't return...
    i = celery_app.control.inspect()
    logging.info(f"got inspecter {i}")
    result = []

    result += [i.scheduled()]
    logging.info("got schedules")
    result += [i.active()]
    logging.info("got active")
    result += [i.reserved()]
    logging.info("got reserved")

    # TODO: normalise the details here. No one outside of the cluster cares about which tasks things are on
    # That should not be a top level breakdown.

    return jsonify(result)


@app.route('/task', methods=['POST'])
def create_task():
    if not validate_app_key(request):
        abort(403)

    payload = request.get_json()
    logging.info(payload)
    if not is_valid_task(payload['task']):
        abort(400, "invalid task")

    thing = load_task_instance(payload['task'])
    thing.app = celery_app

    # work out the args mapping
    args = {}
    for (k, v) in payload['args'].items():
        valid, msg = thing.validate_arg(k, v)
        if valid:
            args[k] = v
        else:
            logging.info(f"invalid request. Parameter '{k}' of task '{payload['task']}' failed validation, {msg}")
            abort(400, f"invalid parameter {k}, {msg}")

    future = thing.delay_or_fail(**args)

    return future.task_id


if __name__ == '__main__':
    app.run()
