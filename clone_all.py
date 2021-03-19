import os
from finder import *
from config import *
from tqdm import tqdm
import subprocess
import pandas as pd


def clone(owner, name, directory, date=None):
    """Clone a GitHub repository and reset its state to a specific commit.

    Parameters
    ----------
    owner : string
        User name of the owner of the repository.
    name : string
        Name of the repository to clone.
    date : string
        A date used to identify the commit to which the state of the repository
        will be reset to.
    directory : string
        Absolute path of a directory to clone the repository to.

    Returns
    -------
    path : string
        Absolute path of the directory containing the repository just cloned.
    """

    path = os.path.join(directory, owner)
    if not os.path.exists(DIR_CLONED):
        os.makedirs(DIR_CLONED, exist_ok=True)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    url = 'https://github.com/{0}/{1}'.format(owner, name)

    # Clone
    command = 'git clone {0}'.format(url)
    if 'DEBUG' in os.environ:
        print(command)

    process = subprocess.Popen(
        command, cwd=path, shell=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    process.wait()

    if process.returncode != 0:
        raise Exception('Failed to execute {0}'.format(command))

    if date is not None:
        # Reset
        path = os.path.join(path, name)
        command = (
            'git log -1 --before="{0} 00:00:00" --pretty="format:%H"'.format(
                date
            )
        )
        if 'DEBUG' in os.environ:
            print(command)

        process = subprocess.Popen(
            command, cwd=path, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        (out, err) = [i.decode() for i in process.communicate()]

        if process.returncode != 0:
            raise Exception('Failed to execute {0}'.format(command))

        sha = out
        command = 'git reset --hard {0}'.format(sha)
        if 'DEBUG' in os.environ:
            print(command)

        process = subprocess.Popen(
            command, cwd=path, shell=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        process.wait()
        if process.returncode != 0:
            raise Exception('Failed to execute {0}'.format(command))


if __name__ == "__main__":
    projects = pd.read_csv(PROJECTS)
    for project in tqdm(projects):
        slug = project.split('/')
        owner = slug[0]
        name = slug[1]
        try:
            clone(owner, name, DIR_CLONED, today)
        except Exception as err:
            print(err)
