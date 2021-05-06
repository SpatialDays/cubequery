import unittest

import os

import io

from cubequery import git_packages, tasks


class GitPackagesTestCases(unittest.TestCase):
    def test_process_note_book(self):
        script_path = os.path.abspath(os.path.join(os.path.abspath(__file__), "../../example_notebook.ipynb"))
        git_packages.process_notebook(script_path, "./")

        expected = "tests/expected_notebook_task.txt"
        actual = "./example_notebook.py"

        self.assertListEqual(
            list(io.open(actual)),
            list(io.open(expected)))
        # clean up the file. This shouldn't happen if the assert fails so we have something to check.
        os.remove(actual)

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
            self.assertEqual(git_packages._line_comment_type(t[0]), t[1], f"{t[0]} didn't return {t[1]}")

    def test_line_parameter(self):
        tests = [
            ("", False),
            ("#parameter display_name=dfhgkjsfdhgkj", True),
            ("#jupyteronly", False),
            ("     #   parameter fgsdhjhdkj=fdljghs display_name=fsdjghdkjfhkj", True),
            ("if __name__ == \"main\":", False),
            ("#parameters", False)
        ]
        for t in tests:
            self.assertEqual(git_packages._is_line_parameter(t[0]), t[1], f"\"{t[0]}\" didn't return {t[1]}")

    def test_extract_value(self):
        tests = [
            ("display_name=\"fish\"", 13, "fish"),
            ("display_name=[\"fish\", \"lemon\"]", 13, "[\"fish\", \"lemon\"]"),
            ("display_name = \"fish\" fkjldhajkgh", 14, "fish"),
            ("display_name = \"fish\" asdgfdg", 14, "fish"),
            ("display_name =            \"fish\" asdgfdg", 14, "fish")
        ]

        for t in tests:
            self.assertEqual(git_packages._extract_value_string(t[0], t[1]), t[2], f"\"{t[0]}\" didn't return {t[1]}")

    def test_process_parameter(self):
        tests = [
            (
                "#parameter display_name=\"fish\" description=\"this is a test parameter\" data_type=\"string\"",
                tasks.Parameter(
                    name="",
                    display_name="fish",
                    description="this is a test parameter",
                    d_type=tasks.DType.STRING,
                    valid=[]
                )
            ),
            (
                " # parameter display_name=\"aardvark ''hello\" description=\"this is a test parameter\" data_type=\"string\" options=[\"SENTINEL_2\", \"LANDSAT_4\", \"LANDSAT_5\", \"LANDSAT_7\", \"LANDSAT_8\"]",
                tasks.Parameter(
                    name="",
                    display_name="aardvark hello",
                    description="this is a test parameter",
                    d_type=tasks.DType.STRING,
                    valid=["SENTINEL_2", "LANDSAT_4", "LANDSAT_5", "LANDSAT_7", "LANDSAT_8"]
                )
            )
        ]

        for t in tests:
            self.assertEqual(git_packages._process_parameter_comment(t[0]), t[1], f"\"{t[0]}\" didn't return {t[1]}")

    def test__is_a_var_def(self):
        tests = [
            ("", False),
            ("#parameter display_name=dfhgkjsfdhgkj", False),
            ("     #   parameter fgsdhjhdkj=fdljghs display_name=fsdjghdkjfhkj", False),
            ("if __name__ == \"main\":", False),
            ("#parameters", False),
            ("aoi = \"foo\"", True),
            ("aoi=\"foo\"", True),
            ("#aoi=\"foo\"", False)
        ]
        for t in tests:
            self.assertEqual(git_packages._is_a_var_def(t[0]), t[1], f"\"{t[0]}\" didn't return {t[1]}")

if __name__ == '__main__':
    unittest.main()
