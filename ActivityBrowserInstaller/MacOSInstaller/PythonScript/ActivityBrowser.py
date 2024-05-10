"""
- ActivityBrowser.py
- Date of File Creation: 22/04/2024
- Contributors: Thijs Groeneweg & Ruben Visser
- Date and Author of Last Modification: 06/05/2024 - Thijs Groeneweg
- Synopsis of the File's purpose:
    This Python script activates the Activity Browser environment and then runs the command "activity-browser"
    within that environment. It first constructs the path to the activation script based on the operating system,
    then executes the activation command using subprocess.run(). After running the "activity-browser" command, it
    deactivates the virtual environment by running the deactivation script using another subprocess.run() call.
"""

import os
import subprocess
import re
import requests
from packaging.version import parse
import argparse

def parseArgs():
    """
    Parse command line arguments. The only argument is --skip-update-check, which skips checking for updates.
    """	
    parser = argparse.ArgumentParser(description="Run the Activity Browser.")
    parser.add_argument("--skip-update-check", action="store_true",
                        help="Skip checking for updates.")
    return parser.parse_args()

def getLatestRelease(user: str, repo: str) -> str:
    """
         Get the most recent version of the Activity Browser from the GitHub API.

        Parameters:
        - user (str): GitHub username of the repository owner.
        - repo (str): Name of the GitHub repository.

        Returns:
        - str: The latest release version.
        """
    url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    try:
        response = requests.get(url)
        data = response.json()
        return data['tag_name'] if 'tag_name' in data else None
    # Handle exceptions that may occur during the request if the user is offline or the server is down.
    except requests.exceptions.RequestException:
        return None
    
def getActivityBrowserVersion(directory: str = ".") -> str:
    """
        Get the version number of the ActivityBrowser file in the specified directory.

        Parameters:
        - directory (str): The directory to search for the ActivityBrowser file.

        Returns:
        - str: The version number of the ActivityBrowser file.
        """
    try:
        for filename in os.listdir(directory):
            match = re.match(r'ActivityBrowser-(\d+\.\d+\.\d+)', filename)
            if match:
                return match.group(1)
        print("ActivityBrowser file not found in the directory.")
        return None
    except FileNotFoundError:
        print(f"Directory '{directory}' not found.")
        return None

def isSecondIputVersionNewer(version1: str, version2: str) -> bool: 
    """
    Compare two version strings in the format 'X.Y.Z' and determine if the second version is newer than the first.

    Parameters:
    - version1 (str): The first version string to compare.
    - version2 (str): The second version string to compare.

    Returns:
    - bool: True if version2 is newer than version1, False otherwise. Returns False if either version is None.
    """
    if version1 is None or version2 is None:
        return False
    return parse(version1) < parse(version2)

def runActivityBrowser() -> None:
    """
    Activate the Activity Browser environment and run the activity-browser.
    """
    # Get the absolute path to the activate and deactivate scripts
    activate_script = os.path.join("ActivityBrowserEnvironment", "Scripts", "activate")
    deactivate_script = os.path.join("ActivityBrowserEnvironment", "Scripts", "deactivate")

    # Use the absolute paths to run the activity-browser command
    activate_cmd = f"source {activate_script}" if os.name != "nt" else f"call {activate_script}"
    deactivate_cmd = f"source {deactivate_script}" if os.name != "nt" else f"call {deactivate_script}"

    os.system(f"{activate_cmd} && activity-browser")
    os.system(f"{deactivate_cmd}")

if __name__ == "__main__":
    args = parseArgs()

    if not args.skip_update_check:
        # Check if the ActivityBrowser file is up to date
        newestVersion = getLatestRelease("ThisIsSomeone", "activity-browser")
        installedVersion = getActivityBrowserVersion()
        isOldVersion = isSecondIputVersionNewer(installedVersion, newestVersion)

        if isOldVersion:
            # Run the ActivityBrowser Updater.exe file to update the ActivityBrowser as administrator
            subprocess.run("powershell Start-Process 'ActivityBrowser Updater.exe' -Verb runAs", shell=True)
        else:
            runActivityBrowser()
    else:
        runActivityBrowser()