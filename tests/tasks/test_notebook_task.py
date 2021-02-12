import unittest

import os

import io

from cubequery.tasks import Parameter, DType
from cubequery.tasks import notebook_task


class TestNoteBookTask(unittest.TestCase):

    def test_line_comment_type(self):
        tests = [
            ("#jupyteronly", "jupyteronly"),
            (" # jupyteronly ", "jupyteronly"),
            (" # parameters ", "parameters"),
            ("     #  parameters ", "parameters"),
            ("", None),
            ("#fjsdghjkesfdhgsjkl", None)
        ]
        for t in tests:
            self.assertEqual(notebook_task._line_comment_type([t[0]]), t[1], f"{t[0]} didn't return {t[1]}")

    def test_line_parameter(self):
        tests = [
            ("", False),
            ("#parameter dfhgkjsfdhgkj", True),
            ("#jupyteronly", False),
            ("     #   parameter fgsdhjhdkj=fdljghs", True),
            ("if __name__ == \"main\":", False)
        ]
        for t in tests:
            self.assertEqual(notebook_task._is_line_parameter(t[0]), t[1], f"\"{t[0]}\" didn't return {t[1]}")

    def test_extract_value(self):
        tests = [
            ("display_name=\"fish\"", 13, "fish"),
            ("display_name=[\"fish\", \"lemon\"]", 13, "[\"fish\", \"lemon\"]"),
            ("display_name = \"fish\" fkjldhajkgh", 14, "fish"),
            ("display_name = \"fish\" asdgfdg", 14, "fish"),
            ("display_name =            \"fish\" asdgfdg", 14, "fish")
        ]

        for t in tests:
            self.assertEqual(notebook_task._extract_value_string(t[0], t[1]), t[2], f"\"{t[0]}\" didn't return {t[1]}")

    def test_process_parameter(self):
        tests = [
            (
                "#parameter display_name=\"fish\" description=\"this is a test parameter\" data_type=\"string\"",
                Parameter(
                    name="",
                    display_name="fish",
                    description="this is a test parameter",
                    d_type=DType.STRING,
                    valid=[]
                )
            ),
            (
                " # parameter display_name=\"aardvark ''hello\" description=\"this is a test parameter\" data_type=\"string\" options=[\"SENTINEL_2\", \"LANDSAT_4\", \"LANDSAT_5\", \"LANDSAT_7\", \"LANDSAT_8\"]",
                Parameter(
                    name="",
                    display_name="aardvark hello",
                    description="this is a test parameter",
                    d_type=DType.STRING,
                    valid=["SENTINEL_2", "LANDSAT_4", "LANDSAT_5", "LANDSAT_7", "LANDSAT_8"]
                )
            )
        ]

        for t in tests:
            self.assertEqual(notebook_task._process_parameter_comment(t[0]), t[1], f"\"{t[0]}\" didn't return {t[1]}")


