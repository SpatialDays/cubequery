import os

import logging
import nbformat
import shutil

import re
from git import Repo

from cubequery import get_config
from cubequery.tasks import DType, Parameter, map_from_dtype, map_to_dtype

import markdown
from lxml import etree


def _extract_first_link(description):
    md = markdown.markdown(description)
    doc = etree.fromstring("<div>" + md + "</div>")
    for link in doc.xpath('//a'):
        return link.get('href')


def _extract_value_string(line, start):
    end_mark = " "
    start_offset = 0
    end_offset = 0
    while line[start] == " " or line[start] == "=":
        start = start + 1

    if line[start] == "\"":
        end_mark = "\""
        start_offset = 1
        end_offset = 0
    elif line[start] == "'":
        end_mark = "'"
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
            param_name = parameters[i:param_equals_index].strip()
            param_value = _extract_value_string(parameters, param_equals_index)
        except ValueError:
            break
        if param_name == "display_name":
            display_name = param_value
        if param_name == "description":
            description = param_value
        if param_name == "datatype" or param_name == "data_type":
            data_type = map_to_dtype(param_value)
        if param_name == "options":
            # decode valid values... we just exec this.
            # We pretty much have to trust this code as its going to be called later any way
            _locals = locals()
            exec(f"valid_values = {param_value}", globals(), _locals)
            valid_values = _locals['valid_values']
        # look for the next space after the length of the param_value
        i = i + len(param_name) + len(param_value) + 1
        if i >= len(parameters):
            break
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


def _setup(path):
    try:
        logging.debug(f"starting to create task from notebook {path}")
        notebook = nbformat.read(path, as_version=4)
    except:
        logging.debug("could not open notebook")
        return

    set_header = False
    function_code = ""
    name = ""
    description = ""
    img_url = ""
    info_url = ""
    parameters = []
    for cell in notebook.cells:
        if not set_header and cell.cell_type == "markdown":
            # parse out the markdown and try and grab the name as the heading and the description as the rest
            name, description, img_url, info_url = _process_markdown_description(cell.source)
            set_header = True

        if cell.cell_type == "code":
            # process the code blocks.
            function_code, parameters = _process_code(function_code, parameters, cell.source)

    function = _convert_to_function(function_code, parameters)
    parameter_code = _convert_to_parameter_def(parameters)
    return name, description, img_url, info_url, function, parameter_code


def _strip_links(description) :
    # find the first []() pair next to each other.
    found = False
    try :
        while not found:
            link_start = description.index("[")
            link_mid = description.index("](", link_start)
            end_alt_text = description.index("]", link_start)
            link_end = description.index(")", link_start)
            if link_mid == end_alt_text:
                return description[:link_start] + description[link_end+1:]
    except ValueError:
        pass


def _process_markdown_description(markdown):
    description = ""
    display_name = ""
    img_url = ""
    info_url = ""
    set_display_name = False
    for line in markdown.splitlines():
        if not set_display_name and line.startswith("#"):
            # this is the header of the first markdown thing so we can use this as the display_name
            display_name = line[1:]
            logging.debug(f"setting display_name to {display_name}")
        else:
            if description != "" or line != "":
                if "<img" in line and img_url == "":
                    # take the first image url as the img_url value for the api
                    img_start = line.index("<img")
                    img_end = line.index(">", img_start)
                    src_index = line.index("src", img_start)

                    equal_start = line.index("=", src_index)
                    img_url = _extract_value_string(line, equal_start)
                    line = line[:img_start] + line[img_end + 1:]
                description += line.strip()
                description += "\n"

    info_url = _extract_first_link(description)
    description = description.replace("\"", "\\\"")
    description = _strip_links(description)
    description = description.strip("\n")
    logging.debug(f"description set to {description}")
    return display_name, description, img_url, info_url


def _line_comment_type(code):
    # make sure we skip blank lines at the start.
    i = 0
    working = code.strip()
    if len(working) > 1 and working[0] == '#':
        comment = (working[1:]).strip()
        if comment[0:11].lower() == "jupyteronly":
            return "jupyteronly"
        if comment[0:10].lower() == "parameters":
            return "parameters"
    return None


def _process_code(function_code, parameters, code):
    if code:
        # parse the code out.
        block_type = _line_comment_type(code)
        if block_type == "jupyteronly":
            # we don't need this code so we can skip it
            return function_code, parameters
        if block_type == "parameters":
            # process parameters block
            parameters = _process_parameters(parameters, code)
            return function_code, parameters

        function_code = _append_all_code(function_code, code)
    return function_code, parameters


def _append_all_code(function_code, code, indent=2):
    for line in code.splitlines():
        if line != "" and line.strip() != "" and line.strip()[0] != "%":
            # line must have trailing spaces removed because pycharm will automatically remove trailing spaces on text
            # files. This means that the expected test file can never match with out the rstrip call
            # This is unpleasant but not really a bad thing.
            function_code += (tab() * indent) + line.rstrip() + "\n"
    return function_code


def _is_line_parameter(line):
    stripped = line.strip()
    if stripped[:1] == "#":
        comment = stripped[1:].strip()
        return comment[:9] == "parameter" and not comment[:10] == "parameters" and "display_name" in comment
    return False


def _is_a_var_def(line):
    stripped = line.strip()
    # not a comment
    if stripped[:1] == "#":
        return False
    # is a single word followed by an equals...
    try:
        equals = stripped.index("=")
        if equals:
            try:
                stripped[0:equals].strip().index(" ")
            except ValueError:
                return True
    except ValueError:
        pass
    return False


def _process_parameters(parameters, code):
    # loop over the lines
    # do this with a while loop as we sometimes need two lines at once
    i = 0
    lines = code.splitlines()
    while i < len(lines):
        line = lines[i]
        if _is_line_parameter(line):
            offset = 1
            logging.info(f"is a var def ***{lines[i+offset]}***")
            while not _is_a_var_def(lines[i+offset]):
                offset = offset + 1
                logging.info("inc offset")
            parameters = _process_parameter(parameters, line, lines[i + offset])
            i = i + offset
        i = i + 1

    return parameters


def _process_parameter(parameters, line_a, line_b):
    p = _process_parameter_comment(line_a)
    p = _process_parameter_name(p, line_b)

    if not parameters:
        parameters = []
    parameters.append(p)

    return parameters


def _convert_to_parameter_def(parameters):

    result = f"{tab()}# this will be the parameter block\n" \
             f"{tab()}parameters = [\n"

    first = True
    for p in parameters:
        if not first:
            result += ",\n"
        else:
            first = False
        result += tab() + tab() + _render_parameter(p)

    result += f"\n{tab()}]\n"
    return result


def _render_parameter(param):
    logging.info(f"{param.name} : {param.display_name}")
    if len(param.valid) > 1:
        return f"Parameter(\"{param.name}\", \"{param.display_name}\", {map_from_dtype(param.d_type)}, \"{param.description}\", {param.valid})"
    else:
        return f"Parameter(\"{param.name}\", \"{param.display_name}\", {map_from_dtype(param.d_type)}, \"{param.description}\")"


def _generate_function_parameters(parameters):
    result = "self"
    for p in parameters:
        result += ", " + p.name
    return result


def _convert_to_function(function_code, parameters):
    # we've now got to the end of all the code so we can finalise things and actually make our function
    # wrap function in header and return value
    function_text = f"{tab()}def NoteBook_Task_Generate_Product({_generate_function_parameters(parameters)}):\n"
    function_text = function_text + function_code

    last_line = function_text.rindex("\n", 0, function_text.rindex("\n"))
    # the text we need to insert is two tabs from the start of the line.
    # while this looks weird it does mean we can change the tab width in only one place.
    split_point = last_line + len(tab() + tab()) + 1
    function_text = function_text[:split_point] + "return " + function_text[split_point:]

    return function_text


def tab():
    return "    "


def _create_filename(script_path):
    return os.path.splitext(os.path.basename(script_path))[0]


def process_notebook(script_path, target_path):
    """
    Create a new copy of this python file replacing the script location pointer and name
    :param target_path: location where the output script should be created.
    :param script_path: the script this task should point at.
    :return:
    """

    root_dir = os.path.dirname(os.path.abspath(__file__))
    target_script = os.path.join(root_dir, "tasks/notebook_task.py")
    filename = _create_filename(script_path)
    out_file_path = os.path.join(target_path, f"{filename}.py")
    logging.info(f"processing {script_path} to {out_file_path}")

    name, description, img_url, info_url,  function_code, parameter_code = _setup(script_path)
    logging.info(f"processed notebook {script_path} with display name {name}")
    if not os.path.exists(target_path) or not os.path.isdir(target_path):
        os.mkdir(target_path)

    this_file = open(target_script, "r")
    target_file = open(out_file_path, "w+")

    while True:
        line = this_file.readline()
        if not line:
            break
        line = line.replace("class NoteBook_Task(", f"class {filename}_Task(")
        line = line.replace("path = \"example_notebook.ipynb\"", f"path = \"{script_path}\"")
        line = line.replace("NoteBook_Task_Generate_Product", f"{filename}_Generate_Product")
        line = line.replace("display_name = \"test\"", f"display_name = \"{name}\"")
        line = line.replace("description = \"test\"", f"description = \"\"\"{description}\"\"\"")
        line = line.replace("img_url = \"test\"", f"img_url = \"{img_url}\"")
        line = line.replace("info_url = \"test\"", f"info_url = \"{info_url}\"")
        target_file.write(line)

    target_file.write(parameter_code)

    target_file.write(f"\n\n{tab()}CubeQueryTask.cal_significant_kwargs(parameters)\n\n")
    target_file.write(function_code)

    this_file.close()
    target_file.close()
    logging.info(f"done processing {script_path}")


def process_repo():

    git_path = get_config("Git", "url")
    repo_dir = get_config("Git", "repo_dir")
    dir_of_interest = get_config("Git", "interesting_dir")
    branch = get_config("Git", "branch")
    script_dir = get_config("App", "extra_path")

    # if we have already cloned the repo make sure its gone.
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)

    logging.debug(f"cloneing {git_path} to {repo_dir}")
    repo = Repo.clone_from(git_path, repo_dir)

    if branch:
        logging.debug(f"checking out {branch}")
        repo.git.checkout(branch)

    logging.debug("done clone")
    # TODO: do we need to be able to set the branch here?

    # find the list of notebooks to process.

    target_dir = os.path.join(repo_dir, dir_of_interest)
    note_books_to_process = find_notebooks(target_dir)
    for notebook in note_books_to_process:
        process_notebook(notebook, script_dir)


def find_notebooks(path):
    result = []
    logging.debug(f"searching {path}")
    for root, dirs, files in os.walk(path):
        for name in files:
            full = os.path.join(root, name)
            logging.debug(f"checking {full} with extension {os.path.splitext(full)[1]}")
            if os.path.splitext(full)[1] == ".ipynb":
                result.append(full)
    return result
