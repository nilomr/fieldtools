# This script stores paths in variables and makes directories if they don't exist

# Libraries
import os
from datetime import date
import pathlib2
from pathlib2 import Path


# Define directories:

# If you want to use this folder:
# PROJECT_DIR = Path(__file__).parents[2]

# Else use any project as your data source / destination, independently of the CLI apps directory
# TODO: get this from higher level user settings
# Also change in src/plot-new-boxes.R
PROJECT_DIR = Path('/home/nilomr/projects/great-tit-song')

# Subdirs
DATA_DIR = PROJECT_DIR / "data"
FIGURE_DIR = PROJECT_DIR / "reports" / "figures"
RESOURCES_DIR = PROJECT_DIR / "resources"
EGO_DIR = Path(__file__).parents[2] / 'fieldtools' / 'src'
OUT_DIR = PROJECT_DIR / "resources" / "fieldwork" / str(date.today().year)

# ----------------------


# Make these directiories should they not currently exist:


def safe_makedir(FILE_DIR):
    """Make a safely nested directory.
    From Tim Sainburg: https://github.com/timsainb/src.avgn_paper/blob/vizmerge/src.avgn/utils/paths.py

    Args:
        FILE_DIR (str or PosixPath): Path to be created.
    """
    if type(FILE_DIR) == str:
        if "." in os.path.basename(os.path.normpath(FILE_DIR)):
            directory = os.path.dirname(FILE_DIR)
        else:
            directory = os.path.normpath(FILE_DIR)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except FileExistsError as e:
                # multiprocessing can cause directory creation problems
                print(e)
    elif type(FILE_DIR) == pathlib2.PosixPath:
        # if this is a file
        if len(FILE_DIR.suffix) > 0:
            FILE_DIR.parent.mkdir(parents=True, exist_ok=True)
        else:
            try:
                FILE_DIR.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                if e.errno != 17:
                    print("Error:", e)


for path in DATA_DIR, FIGURE_DIR, RESOURCES_DIR:
    safe_makedir(path)
