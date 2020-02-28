import logging
import os

from celery import Celery
from flask import Flask, request, abort, render_template, jsonify
from flask_caching import Cache
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from jobtastic.cache import WrappedCache

from cubequery import get_config, users
from cubequery.packages import is_valid_task, load_task_instance, list_processes


def _to_bool(input):
    return input.lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']


redis_url = get_config("Redis", "url")
config = {
    "DEBUG": _to_bool(get_config("App", "debug")),
    "CACHE_TYPE": "redis",
    "CACHE_REDIS_URL": redis_url,
}

template_dir = os.path.abspath('./webroot/templates')
static_dir = os.path.abspath('./webroot/static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config.from_mapping(config)
cache = WrappedCache(Cache(app))
logging.info(f"setting up celery connection to {redis_url}")
celery_app = Celery('tasks', backend=redis_url, broker=redis_url)

# celery_app.conf.update(app.config)

celery_app.conf.update(
    result_expires=60 * 60 * 24 * 10,  # ten days
    task_publish_retry=True,
    task_ignore_result=False,
    task_track_started=True,
    JOBTASTIC_CACHE=cache,
)

packages = [m['name'].replace("/", ".") for m in list_processes()]
celery_app.autodiscover_tasks(packages=packages, related_name="", force=True)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/describe', methods=['GET'])
def describe():
    """
    Fetch a description of the available tasks to run.
    Each result will have a name, display name, description and a list of parameters.
    Each parameter will have a name, description, type and list of valid values.
    If the list of valid values is empty then anything goes.
    If the type is "str" (a string) and there is a list of valid values, that is a complete list of acceptable values.
    If the type is "int", "date" or "float" and there are two entries in the valid values, the first is min, the second
        max
    If the type is "int", "date" or "float" and there are more than two entries then it is a complete list of possible
        values.

    :return: a JSON encodes list of task description objects.
    """
    validate_app_key()

    result = list_processes()

    return jsonify(result)


@app.route('/task/<task_id>', methods=['GET'])
def task_id(task_id):
    validate_app_key()

    logging.info(f"looking up task by id {task_id}")
    i = celery_app.control.inspect()

    return jsonify(normalise_single_task(i.query_task(task_id)))


@app.route('/task/', methods=['GET'])
def all_tasks():
    validate_app_key()

    logging.info("looking up all tasks...")
    # note there must be a worker running or this won't return...
    i = celery_app.control.inspect()
    logging.info(f"got inspected {i}")
    result = []

    result += [i.scheduled()]
    logging.info("got schedules")
    result += [i.active()]
    logging.info("got active")
    result += [i.reserved()]
    logging.info("got reserved")

    # TODO: normalise the details here. No one outside of the cluster cares about which tasks things are on
    # That should not be a top level breakdown.

    return jsonify(normalise_task_info(result))


@app.route('/token', methods=['POST'])
def get_token():
    payload = request.get_json()
    if not payload['name']:
        abort(403, "name required")

    if not payload['pass']:
        abort(403, "pass required")

    logging.info(f"log in request for {payload['name']} from {request.remote_addr}")

    if not users.check_user(payload['name'], payload['pass'], request.remote_addr):
        abort(403, "bad creds")

    s = Serializer(get_config("App", "secret_key"), expires_in=int(get_config("App", "token_duration")))
    return jsonify({'token': s.dumps({'id': payload['name']})})


@app.route('/task', methods=['POST'])
def create_task():
    user_id = validate_app_key()

    global celery_app

    payload = request.get_json()
    logging.info(payload)
    if not is_valid_task(payload['task']):
        abort(400, "invalid task")

    thing = load_task_instance(payload['task'])
    thing.app = celery_app

    # work out the args mapping
    args = {'user': user_id}
    for (k, v) in payload['args'].items():
        valid, msg = thing.validate_arg(k, v)
        if valid:
            args[k] = v
        else:
            logging.info(f"invalid request. Parameter '{k}' of task '{payload['task']}' failed validation, {msg}")
            abort(400, f"invalid parameter {k}, {msg}")

    future = thing.delay_or_fail(**args)

    return future.task_id


def normalise_single_task(info):
    result = []
    if info:
        for (server, things) in info.items():
            if things:
                for (_, tasks) in things.items():
                    (state, t) = tasks

                    result += [{
                        "id": t['id'],
                        "name": t['name'],
                        "time_start": t['time_start'],
                        "args": t['kwargs'],
                        "ack": t['acknowledged'],
                        "server": server,
                        "state": state
                    }]

    return result


def normalise_task_info(info):
    result = []

    for section in info:
        if section:
            for (server, tasks) in section.items():
                for t in tasks:
                    result += [{
                        "id": t['id'],
                        "name": t['name'],
                        "time_start": t['time_start'],
                        "args": t['kwargs'],
                        "ack": t['acknowledged'],
                        "server": server
                    }]

    return result


def validate_app_key():
    """
    Get the app key parameter from a request and check that it is a valid token.
    :return: Bool, True if and only if the requests app key is a valid token
    """

    if 'APP_KEY' in request.args:
        s = Serializer(get_config("App", "secret_key"))
        try:
            data = s.loads(request.args['APP_KEY'])
            # TODO: look up the id and make sure its a real one.
            return data['id']
        except SignatureExpired:
            abort(403, "Token expired")
        except BadSignature:
            abort(403, "Invalid token")
    abort(403, "No token")


if __name__ == '__main__':
    app.run(host=get_config("App", "host"))
