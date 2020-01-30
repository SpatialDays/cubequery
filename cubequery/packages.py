import importlib
import inspect
import logging
import pkgutil


def find_modules(module_name):
    def _inner_find(_module_name):
        result = []
        for sub_module in pkgutil.walk_packages([_module_name]):
            _, sub_module_name, _ = sub_module
            qname = _module_name + "." + sub_module_name
            result += [qname]
            result += _inner_find(qname)

        return result

    return _inner_find(module_name.replace(".", "/"))


def _find_classes(module_list, root_module, matcher):
    result = []
    for m in module_list:
        target_module = m.replace("/", ".")
        mod = __import__(target_module, fromlist=[root_module])
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if matcher(name, obj):
                result += [obj]
    return result


def _task_matcher(name, obj):
    # TODO: make this filter on more things when we know what they are.
    if not (hasattr(obj, 'name') and obj.name.startswith("cubequery.")):
        return False

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
        params += [{"name": e.name, "type": e.d_type, "description": e.description}]

    return {
        "name": clazz.name,
        "display_name": clazz.display_name,
        "description": clazz.description,
        "args": params,
    }


def find_available_tasks():
    """
    Work out which tasks are available and return the metadata for those tasks.

    :return: a list of available task metadata
    """
    task_class_list = _find_classes(find_modules("cubequery.tasks"), "cubequery", _task_matcher)
    result = []
    for t in task_class_list:
        result += [_task_info(t)]
    return result


def is_valid_task(name):
    """
    Is the provided task name one of the tasks that we can find?
    :param name: name of the class to check.
    :return: True if and only if the provided name is one we can find.
    """
    possible = find_available_tasks()
    for p in possible:
        if p['name'] == name:
            return True
    logging.info(f"Could not find {name} in {possible}")
    return False


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
    print(find_available_tasks())
