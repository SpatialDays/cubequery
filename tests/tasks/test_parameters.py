import unittest

from cubequery.tasks import CubeQueryTask, Parameter, DType


class TestParameterHandling(unittest.TestCase):

    class MockTask(CubeQueryTask):
        display_name = "A Test Task"
        description = "A test task that shouldn't do anything."

        parameters = [
            Parameter("a", DType.STRING, "string a"),
            Parameter("b", DType.INT, "int b"),
        ]

        CubeQueryTask.cal_significant_kwargs(parameters)

        def calculate_result(self, *args, **kwargs):
            # Do nothing we are only using this for param validation.
            pass

    def test_string_validation(self):
        test = TestParameterHandling.MockTask()
        self.assertTrue(test.validate_arg("a", "this is fine"))
        self.assertTrue(test.validate_arg("a", ""))

        self.assertFalse(test.validate_arg("a", 5493876849576))


