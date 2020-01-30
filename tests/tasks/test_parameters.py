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
        self.assertFalse(test.validate_arg("a", 0.485635487))
        self.assertFalse(test.validate_arg("a", {'foo': 'bar'}))
        self.assertFalse(test.validate_arg("a", {}))
        self.assertFalse(test.validate_arg("a", []))

    def test_int_validation(self):
        test = TestParameterHandling.MockTask()

        self.assertTrue(test.validate_arg("b", 54))
        self.assertTrue(test.validate_arg("b", 0))
        self.assertTrue(test.validate_arg("b", "-1"))
        self.assertTrue(test.validate_arg("b", "0"))
        self.assertTrue(test.validate_arg("b", "00000"))
        self.assertTrue(test.validate_arg("b", -1))
        self.assertTrue(test.validate_arg("b", "+1"))

        # Due to the way python handles bool as a sub class of int, this slightly strangely is a valid int...
        self.assertTrue(test.validate_arg("b", True))
        self.assertTrue(test.validate_arg("b", False))

        self.assertFalse(test.validate_arg("b", ""))
        self.assertFalse(test.validate_arg("b", 0.485635487))
        self.assertFalse(test.validate_arg("b", "True"))
        self.assertFalse(test.validate_arg("b", {'foo': 'bar'}))
        self.assertFalse(test.validate_arg("b", "sjkhgajkdfhgkjds"))
        self.assertFalse(test.validate_arg("b", "0485875.35347"))
        self.assertFalse(test.validate_arg("b", "-10.0"))

    def test_unknown_param(self):
        test = TestParameterHandling.MockTask()
        self.assertFalse(test.validate_arg("missing", "doesn't matter"))
