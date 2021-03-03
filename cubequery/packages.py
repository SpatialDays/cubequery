import importlib
import inspect
import logging
import os
import sys

from importlib.util import spec_from_file_location, module_from_spec

from cubequery import get_config

logger = logging.getLogger("packages")


def _task_matcher(name, obj):
    # Need a description to pass to the user
    if not hasattr(obj, 'description'):
        return False

    # must have a display name for the user.
    if not hasattr(obj, 'display_name'):
        return False

    # Task must have a calculate_result method or it won't be able to do anything.
    if not hasattr(obj, 'calculate_result'):
        return False

    # Every task should have parameters...
    # If this turns out to be a problem we can hack around this with a dummy argument.
    if not hasattr(obj, 'parameters'):
        return False

    return True


def _task_info(clazz):
    """
    from a provided class instance extract task metadata.
    This will error if any of the expected fields of the task are missing.
    :param clazz: class object you need metadata for
    :return: a metadata dictionary
    """
    params = []
    for e in clazz.parameters:
        params += [{
            "name": e.name,
            "display_name": e.display_name,
            "type": e.d_type,
            "description": e.description,
            "valid_values": e.valid
        }]

    return {
        "name": clazz.name,
        "display_name": clazz.display_name,
        "description": clazz.description,
        "args": params,
    }


def is_valid_task(name):
    """
    Is the provided task name one of the tasks that we can find?
    :param name: name of the class to check.
    :return: True if and only if the provided name is one we can find.
    """
    possible = list_processes()
    for p in possible:
        if p['name'] == name:
            return True
    logging.info(f"Could not find {name} in {possible}")
    return False


def load_module(root, file, package_root):
    full_path = os.path.join(root, file)
    mod_name = (os.path.join(root, file)[len(package_root):-3]).replace(os.sep, '.')
    spec = spec_from_file_location(mod_name, full_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[mod_name] = module
    logger.debug(f"checking module {mod_name}")
    result = []
    for name, obj in inspect.getmembers(module):
        logger.debug(f"> checking {mod_name}.{name}")
        if _task_matcher(name, obj):
            logger.debug(f"MATCHED {mod_name}.{name}")
            result += [_task_info(obj)]
    return result


_process_cache = None  # TODO: some way of resetting this...

def list_processes():
    global _process_cache

    if _process_cache:
        return _process_cache

    added = False
    result = []
    dir_list = get_config("App", "extra_path")
    if dir_list != "":
        parts = dir_list.split(';')
        for p in parts:
            if p not in sys.path:
                logger.info(f"adding {p} to python path")
                sys.path.append(p)
            for (root, dirs, files) in os.walk(p, topdown=True):
                for f in files:
                    if f.endswith(".py"):
                        try:
                            result += load_module(root, f, p)
                        except Exception as e:
                            logger.warning(f"could not load {root}/{f} due to {e} skipping")

    if added:
        importlib.invalidate_caches()

    _process_cache = result
    logging.info(f"found {[f['name'] for f in result]}")
    return result


def load_task_instance(name):
    """
    Create an instance of the provided task name.

    Note: this will not validate that the task is actually a task object. Be careful with this.
    You are required to validate that the task name is valid and this is not going to load some
    random class that you haven't expected.

    :param name: fully qualified name of the class to create an instance of.
    :return: an instance of the class requested or a exception in case of problems.
    """
    parts = name.split('.')
    class_name = parts[-1]
    package_name = '.'.join(parts[:-1])
    mod = importlib.import_module(name=package_name)
    clazz = getattr(mod, class_name)
    return clazz()


if __name__ == '__main__':
    print(list_processes())
