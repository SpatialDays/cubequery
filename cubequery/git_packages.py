import os
from git import Repo

from cubequery import get_config
from cubequery.tasks import notebook_task


def process_repo():

    git_path = get_config("Git", "url")
    repo_dir = get_config("Git", "repo_dir")
    dir_of_interest = get_config("Git", "interesting_dir")
    script_dir = get_config("App", "Script_dir")

    # if we have already cloned the repo make sure its gone.
    if os.path.exists(repo_dir):
        os.rmdir(repo_dir)

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
