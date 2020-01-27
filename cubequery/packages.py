import pkgutil
import inspect
import sys


def find_modules(module_name):
    def _find_modules(_module_name):
        result = []
        for sub_module in pkgutil.walk_packages([_module_name]):
            _, sub_module_name, _ = sub_module
            qname = _module_name + "." + sub_module_name
            result += [qname]
            result += find_modules(qname)

        return result

    return _find_modules(module_name.replace(".", "/"))


def find_classes(module_list, root_module, matcher):
    result = []
    for m in module_list:
        target_module = m.replace("/", ".")
        mod = __import__(target_module, fromlist=[root_module])
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if matcher(name, obj):
                result += [obj]
    return result


def task_matcher(name, obj):
    # TODO: make this filter on more things when we know what they are.
    if not (hasattr(obj, 'name') and obj.name.startswith("cubequery.")):
        return False
    # Need a description to pass to the user
    if not hasattr(obj, 'description'):
        return False

    # Task must have a calculate_result method or it won't be able to do anything.
    if not hasattr(obj, 'calculate_result'):
        return False

    return True


def task_info(clazz):
    return {
        "name": clazz.name,
        "description": clazz.description,
        "args": [],  # TODO: arg handling here.
    }


if __name__ == '__main__':
    task_class_list = find_classes(find_modules("cubequery.worker"), "cubequery", task_matcher)
    for t in task_class_list:
        print(task_info(t))
