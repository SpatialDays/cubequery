from jobtastic import JobtasticTask
from itertools import product


# This task is a dummy task to make sure things work
class DoAThing(JobtasticTask):

    description = "a test task, not really good for anything."

    significant_kwargs = [
        ('a', str),
        ('b', str),
    ]

    herd_avoidance_timeout = 60
    cache_duration = 0

    def calculate_result(self, a, b, **kwargs):
        """
        Do A Thing
        """
        result = []

        for prod in product([a, b]):
            result.append(''.join(prod))

        return result
