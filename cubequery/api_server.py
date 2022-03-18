import json
import logging
import os
from os import path

from celery import Celery
from flask import Flask, request, abort, render_template, jsonify, send_file
from flask_caching import Cache
from flask_cors import CORS
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from jobtastic.cache import WrappedCache

from cubequery import get_config, users, git_packages, fetch_form_settings

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
app.url_map.strict_slashes = False
app.config.from_mapping(config)
cache = WrappedCache(Cache(app))
cors = CORS(app, resources={r"/*": {"origins": get_config("App", "cors_origin")}}, send_wildcard=True, allow_headers=['Content-Type'])

git_packages.process_repo()

logging.info(f"setting up celery connection to {redis_url}")
celery_app = Celery('tasks', backend=redis_url, broker=redis_url, methods=['GET', 'POST'], supports_credentials=True)

# celery_app.conf.update(app.config)

celery_app.conf.update(
    result_expires=60 * 60 * 24 * 10,  # ten days
    task_publish_retry=True,
    task_ignore_result=False,
    task_track_started=True,
    JOBTASTIC_CACHE=cache,
)

packages = [m['name'].replace("/", ".") for m in list_processes()]
if len(packages):
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

    :return: a JSON encoded list of task description objects.
    """

    result = list_processes()
    
    dynamic_settings = fetch_form_settings()

    return jsonify({'result':result, 'settings':dynamic_settings})


@app.route('/task/<task_id>', methods=['GET'])
def task_id(task_id):
    logging.info(f"looking up task by id {task_id}")
    i = celery_app.control.inspect()
    return jsonify(normalise_single_task(i.query_task(task_id)))


@app.route('/task/', methods=['GET'])
def all_tasks():
    # Perhaps limit this to user?
    
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


@app.route('/result/<task_id>', methods=['GET'])
def get_result(task_id):
    result_dir = get_config("App", "result_dir")
    file_name = f"{task_id}_output.zip"
    # target = path.join(result_dir, task_id, file_name)
    target = f'/home/james/Projects/cubequery/~/data/{task_id}/' + file_name
    if path.exists(target):
        return send_file(target, mimetype='application/zip', as_attachment=True)
    else:
        return abort(404)

@app.route('/task', methods=['POST'])
def create_task():
    global celery_app

    payload = request.get_json()
        
    if not is_valid_task(payload['task']):
        logging.info(f"invalid task payload {payload}")
        abort(400, "invalid task")

    thing = load_task_instance(payload['task'])
    thing.app = celery_app
    logging.info(f"found {thing.name} wanted {payload['task']}")
    logging.info(f"parms: {[p.name for p in thing.parameters]}")
    # work out the args mapping
    args = {'user': payload['userid']}

    for (k, v) in payload['args'].items():
        valid, msg = thing.validate_arg(k, v)
        if valid:
            args[k] = v
        else:
            logging.info(f"invalid request. Parameter '{k}' of task '{payload['task']}' failed validation, {msg}")
            abort(400, f"invalid parameter {k}, {msg}")

    errors = thing.standard_validation(args)
    
    if hasattr(thing, 'validate_args'):
        process_specific_validation = thing.validate_args(args)
        if process_specific_validation:
            errors += process_specific_validation

    if errors != []:
        logging.warning(f"invalid request: {errors}")
        error_message = jsonify(errors)
        error_message.status_code = 400
        return error_message
        

    param_block = json.dumps(args)

    future = thing.delay_or_fail(**{"params": param_block})
    
    return jsonify({'task_id': future.task_id})


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

if __name__ == '__main__':
    app.run(host=get_config("App", "host"))
