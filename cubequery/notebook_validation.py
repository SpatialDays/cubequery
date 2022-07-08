import sys

from cubequery.packages import list_processes, add_extra_lib_path, load_task_instance
from cubequery.git_packages import process_repo

import inspect
import socket

def validate_notebooks():
    process_repo()

    add_extra_lib_path()
    result = 0

    procs = [m['name'].replace("/", ".") for m in list_processes()]
    for p in procs:

        t = load_task_instance(p)
        f = t.generate_product
        try:
            f(**create_args(f))
        except OSError as e:
            if str(e) == "Timed out trying to connect to tcp://dask-scheduler.dask.svc.cluster.local:8786 after 10 s":
                pass
            else:
                result = result + 1
                raise e
        except ValueError as e:
            if str(e) == "No ODC environment, checked configurations for ['default', 'datacube']":
                pass
            else:
                result = result + 1
        except Exception:
            result = result + 1
    if result > 0:
        sys.exit(result)


def create_args(func):
    result = {}
    for i, arg in enumerate(inspect.signature(func).parameters):
        result[arg] = None

    return result


if __name__ == '__main__':
    validate_notebooks()
