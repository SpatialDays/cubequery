import unittest


class MyTestCase(unittest.TestCase):
    def test_process_note_book(self):
        script_path = os.path.abspath(os.path.join(os.path.abspath(__file__), "../../example_notebook.ipynb"))
        notebook_task.process_notebook(script_path, "./")

        expected = "tests/expected_notebook_task.txt"
        actual = "./example_notebook.py"

        self.assertListEqual(
            list(io.open(actual)),
            list(io.open(expected)))
        # clean up the file. This shouldn't happen if the assert fails so we have something to check.
        os.remove(actual)


if __name__ == '__main__':
    unittest.main()
