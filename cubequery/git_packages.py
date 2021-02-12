import os

import logging
from git import Repo

from cubequery import get_config
from cubequery.tasks import notebook_task


def _create_filename(script_path):
    return os.path.splitext(os.path.basename(script_path))[0]


def process_notebook(script_path, target_path):
    """
    Create a new copy of this python file replacing the script location pointer and name
    :param target_path: location where the output script should be created.
    :param script_path: the script this task should point at.
    :return:
    """

    this_script = os.path.abspath(__file__)
    target_script = os.path.join(this_script, "tasks/notebook_task.py")
    filename = _create_filename(script_path)
    out_file_path = os.path.join(target_path, f"{filename}.py")

    this_file = open(target_script, "r")
    target_file = open(out_file_path, "w")

    while True:
        line = this_file.readline()
        if not line:
            break
        line = line.replace("class NoteBook_Task(", f"class {filename}Task(")
        line = line.replace("path = \"example_notebook.ipynb\"", f"path = \"{script_path}\"")
        target_file.write(line)

    this_file.close()
    target_file.close()



def process_repo():

    git_path = get_config("Git", "url")
    repo_dir = get_config("Git", "repo_dir")
    dir_of_interest = get_config("Git", "interesting_dir")
    script_dir = get_config("App", "extra_path")

    # if we have already cloned the repo make sure its gone.
    if os.path.exists(repo_dir):
        os.rmdir(repo_dir)
    logging.debug(f"cloneing {git_path} to {repo_dir}")
    Repo.clone_from(git_path, repo_dir)

    # TODO: do we need to be able to set the branch here?

    # find the list of notebooks to process.

    target_dir = os.path.join(repo_dir, dir_of_interest)
    note_books_to_process = find_notebooks(target_dir)
    for notebook in note_books_to_process:
        notebook_task.process_notebook(notebook, script_dir)


def find_notebooks(path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            full = os.path.join(root, name)
            if os.path.splitext(full)[1] == "ipynb":
                result.append(full)
    return result
