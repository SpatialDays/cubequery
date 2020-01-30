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
        self.assertTrue(test.validate_arg("a", "this is fine")[0])
        self.assertTrue(test.validate_arg("a", "")[0])

        self.assertFalse(test.validate_arg("a", 5493876849576)[0])
        self.assertFalse(test.validate_arg("a", 0.485635487)[0])
        self.assertFalse(test.validate_arg("a", {'foo': 'bar'})[0])
        self.assertFalse(test.validate_arg("a", {})[0])
        self.assertFalse(test.validate_arg("a", [])[0])

    def test_int_validation(self):
        test = TestParameterHandling.MockTask()

        self.assertTrue(test.validate_arg("b", 54)[0])
        self.assertTrue(test.validate_arg("b", 0)[0])
        self.assertTrue(test.validate_arg("b", "-1")[0])
        self.assertTrue(test.validate_arg("b", "0")[0])
        self.assertTrue(test.validate_arg("b", "00000")[0])
        self.assertTrue(test.validate_arg("b", -1)[0])
        self.assertTrue(test.validate_arg("b", "+1")[0])

        # Due to the way python handles bool as a sub class of int, this slightly strangely is a valid int...
        self.assertTrue(test.validate_arg("b", True)[0])
        self.assertTrue(test.validate_arg("b", False)[0])

        self.assertFalse(test.validate_arg("b", "")[0])
        self.assertFalse(test.validate_arg("b", 0.485635487)[0])
        self.assertFalse(test.validate_arg("b", "True")[0])
        self.assertFalse(test.validate_arg("b", {'foo': 'bar'})[0])
        self.assertFalse(test.validate_arg("b", "sjkhgajkdfhgkjds")[0])
        self.assertFalse(test.validate_arg("b", "0485875.35347")[0])
        self.assertFalse(test.validate_arg("b", "-10.0")[0])

    def test_unknown_param(self):
        test = TestParameterHandling.MockTask()
        self.assertFalse(test.validate_arg("missing", "doesn't matter")[0])
