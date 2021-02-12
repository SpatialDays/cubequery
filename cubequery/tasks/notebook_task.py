import logging
from types import MethodType

import nbformat
import os

from cubequery.tasks import Parameter, CubeQueryTask, DType


def _line_comment_type(code):
    # make sure we skip blank lines at the start.
    i = 0
    while i < len(code) and code[i].strip() == "":
        i = i + 1

    if i == len(code):
        return None

    line = code[i]
    working = line.strip()
    if len(working) > 1 and working[0] == '#':
        comment = (working[1:]).strip()
        if comment[0:11] == "jupyteronly":
            return "jupyteronly"
        if comment[0:10] == "parameters":
            return "parameters"
    return None


def _is_line_parameter(line):
    stripped = line.strip()
    if stripped[:1] == "#":
        return stripped[1:].strip()[:9] == "parameter"
    return False


def _extract_value_string(line, start):
    end_mark = " "
    start_offset = 0
    end_offset = 0
    while line[start] == " ":
        start = start + 1

    if line[start] == "\"":
        end_mark = "\""
        start_offset = 1
        end_offset = 0
    elif line[start] == "[":
        end_mark = "]"
        start_offset = 0
        end_offset = 1

    end_index = line.index(end_mark, start + 1)
    return line[start + start_offset: end_index + end_offset]


def _process_parameter_comment(line):
    # we don't know the order that the parameters are going to appear.
    # to make things nicer to use we can work this out
    # #paramter display_name="satellite" description="Satellite to use." datatype="string" options=["SENTINEL_2", "LANDSAT_4", "LANDSAT_5", "LANDSAT_7", "LANDSAT_8"],
    parameters = line.strip()[1:].strip()[10:]
    display_name = ""
    description = ""
    data_type = DType.STRING
    valid_values = None
    done = False
    i = 0
    while not done:

        try:
            param_equals_index = parameters.index("=", i)
        except ValueError:
            break
        param_name = parameters[i:param_equals_index]
        param_value = _extract_value_string(line, param_equals_index)
        if param_name == "display_name":
            display_name = param_value
        if param_name == "description":
            description = param_value
        if param_name == "data_type":
            data_type = DType[param_value]
        if param_name == "options":
            # decode valid values... we just exec this.
            # We pretty much have to trust this code as its going to be called later any way
            valid_values = exec(param_value)

        # look for the next space after the length of the param_value
        i = i + len(param_value)
        while parameters[i] != " ":
            i = i + 1
            if i == len(parameters):
                done = True
                break

    return Parameter(
        name="",
        display_name=display_name,
        d_type=data_type,
        description=description,
        valid=valid_values
    )


def _process_parameter_name(parameter, line):
    stripped = line.strip()
    split = stripped.index("=")
    parameter.name = stripped[:split].strip()
    return parameter


class NoteBook_Task(CubeQueryTask):

    def __init__(self):
        path = "example_notebook.ipynb"
        try:
            logging.debug(f"starting to create task from notebook {path}")
            notebook = nbformat.read(path, as_version=4)
        except:
            logging.debug("could not open notebool")
            return

        set_header = False
        self.function_code = ""
        self.parameters = []
        for cell in notebook.cells:
            if not set_header and cell.cell_type == "markdown":
                # parse out the markdown and try and grab the name as the heading and the description as the rest
                self._process_markdown_description(cell.source)
                set_header = True

            if cell.cell_type == "code":
                # process the code blocks.
                self._process_code(cell.source)
                pass

        self._convert_to_function()

    def _process_markdown_description(self, markdown):
        description = ""
        set_display_name = False
        for line in markdown:
            if not set_display_name and line.startswith("#"):
                # this is the header of the first markdown thing so we can use this as the display_name
                self.display_name = line[1:]
                logging.debug(f"setting display_name to {self.display_name}")
            else:
                description += line

        self.description = description

    def _process_code(self, code):
        if code:
            # parse the code out.
            block_type = _line_comment_type(code)
            if block_type == "jupyteronly":
                # we don't need this code so we can skip it
                return
            if block_type == "parameters":
                # process parameters block
                return self._process_parameters(code)

            self._append_all_code(code)

    def _append_all_code(self, code, indent=1):
        print("line: ", code)
        for line in code:

            if line != "" and line.strip() != "" and line.strip()[0] != "%":
                self.function_code += ("\t" * indent) + line + "\n")

    def _process_parameters(self, code):
        # loop over the lines
        # do this with a while loop as we sometimes need two lines at once
        i = 0
        while i < len(code):
            line = code[i]
            if _is_line_parameter(line):
                # TODO: should we handle blank lines here?
                self._process_parameter(line, code[i + 1])
                i = i + 1
            i = i + 1

    def _process_parameter(self, line_a, line_b):
        p = _process_parameter_comment(line_a)
        p = _process_parameter_name(p, line_b)

        if not self.parameters:
            self.parameters = []
        self.parameters.append(p)

    def _generate_function_parameters(self):
        result = "self"
        for p in self.parameters:
            result += ", " + p.name
        return result

    def _convert_to_function(self):

        # make sure that the code returns something.

        # we've now got to the end of all the code so we can finalise things and actually make our function
        # wrap function in header and return value
        function_text = "def generate_product(" + self._generate_function_parameters() + "):\n"
        function_text = function_text + self.function_code

        # now to create the function and add it to the class

        print(function_text)
        function = exec(function_text)
        self.generate_product = MethodType(function, self)
