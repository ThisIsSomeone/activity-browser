"""
- ab_uninstaller.py
- Date of File Creation: 22/04/2024
- Contributors: Thijs Groeneweg & Ruben Visser
- Date and Author of Last Modification: 03/05/2024 - Thijs Groeneweg
- Synopsis of the File's purpose:
    This Python script first obtains the current working directory and then constructs a path for a directory named
    "ActivityBrowserEnvironment" within that directory. It then attempts to remove this directory using shutil.rmtree().
    If the directory is successfully removed, it prints a success message indicating the directory's removal.
    If the directory is not found, it prints a message indicating that the directory was not found.
"""

import shutil
import os
from ActivityBrowser import getActivityBrowserVersion

currentDirectory = os.getcwd()
directoryPath = os.path.join(currentDirectory, "ActivityBrowserEnvironment")

try:
    shutil.rmtree(directoryPath)
    print(f"Directory '{directoryPath}' successfully removed.")
except FileNotFoundError:
    print(f"Directory '{directoryPath}' not found.")

try:
    # Remove ActivityBrowser-<version> file
    os.remove("ActivityBrowser-" + getActivityBrowserVersion())
except FileNotFoundError:
    print("ActivityBrowser file not found in the directory.")