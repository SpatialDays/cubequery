from jobtastic import JobtasticTask
from itertools import product


# This task is a dummy task to make sure things work
from cubequery.tasks import Parameter, CubeQueryTask, DType


class DoAThing(CubeQueryTask):

    display_name = "Do A Thing"
    description = "a test task, not really good for anything."

    parameters = [
        Parameter("a", DType.STRING, "string a"),
        Parameter("b", DType.STRING, "string b"),
    ]

    CubeQueryTask.cal_significant_kwargs(parameters)

    def calculate_result(self, a, b, **kwargs):
        """
        Do A Thing
        """
        result = []

        for prod in product([a, b]):
            result.append(''.join(prod))

        return result
