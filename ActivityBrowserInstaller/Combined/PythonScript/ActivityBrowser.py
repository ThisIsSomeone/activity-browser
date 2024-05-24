import os
import sys
import subprocess
import argparse
import platform
import re
import requests
from packaging.version import parse

def parseArgs():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Activity Browser.")
    parser.add_argument("--skip-update-check", action="store_true", help="Skip checking for updates.")
    return parser.parse_args()

def getLatestRelease(user: str, repo: str) -> str:
    """Get the most recent version of the Activity Browser from the GitHub API."""
    url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    try:
        response = requests.get(url)
        data = response.json()
        return data['tag_name'] if 'tag_name' in data else None
    except requests.exceptions.RequestException:
        return None

def getActivityBrowserVersion(directory: str = ".") -> str:
    """Get the version number of the ActivityBrowser file in the specified directory."""
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
    """Compare two version strings and determine if the second version is newer than the first."""
    if version1 is None or version2 is None:
        return False
    return parse(version1) < parse(version2)

def runActivityBrowserWindows(skipUpdateCheck) -> None:
    """Activate the Activity Browser environment and run the activity-browser on Windows."""
    if not skipUpdateCheck:
        newestVersion = getLatestRelease("ThisIsSomeone", "activity-browser")
        installedVersion = getActivityBrowserVersion()
        isOldVersion = isSecondIputVersionNewer(installedVersion, newestVersion)

        if isOldVersion:
            runUpdaterWindows()
            
        else:
            runActivityBrowserCommandsWindows()
    else:
        runActivityBrowserCommandsWindows()

def runActivityBrowserCommandsWindows() -> None:
    activate_script = os.path.join("ActivityBrowserEnvironment", "Scripts", "activate")
    deactivate_script = os.path.join("ActivityBrowserEnvironment", "Scripts", "deactivate")

    activate_cmd = f"call {activate_script}"
    deactivate_cmd = f"call {deactivate_script}"

    os.system(f"{activate_cmd} && activity-browser")
    os.system(f"{deactivate_cmd}")

def resourcePath(relativePath: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller on Mac."""
    try:
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.abspath(".")

    return os.path.join(basePath, relativePath)

def runUpdaterWindows() -> None:
    try:
        subprocess.run(
            "powershell Start-Process 'ActivityBrowser Updater.exe' -Verb runAs",
            shell=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("Failed to run the updater. Error code:", e.returncode)
        runActivityBrowserCommandsWindows()
    except Exception as e:
        print("An unexpected error occurred:", str(e))
        runActivityBrowserCommandsWindows()

def runUpdaterMac() -> None:
    try:
        updaterPath = resourcePath('ActivityBrowser Updater.py')
        # Running the updater script using os.system and capturing the return code
        return_code = os.system(f'python "{updaterPath}"')
        if return_code != 0:
            print("Can not open the updater, did you decline the admin privileges?")
            openActivityBrowserMac(skipUpdateCheck=True)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        openActivityBrowserMac(skipUpdateCheck=True)

def openActivityBrowserMac(skipUpdateCheck: bool) -> None:
    baseDir = os.path.dirname(__file__)
    scriptPath = os.path.join(baseDir, 'openActivityBrowser.sh')

    command = [scriptPath]
    if skipUpdateCheck:
        try:
           subprocess.Popen(command)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
        except FileNotFoundError:
            print(f"Error: The script '{scriptPath}' does not exist or is not accessible.")
    else:
        runUpdaterMac()

def main() -> None:
    args = parseArgs()

    if platform.system() == "Windows":
        runActivityBrowserWindows(args.skip_update_check)
    elif platform.system() == "Darwin":  # macOS
        openActivityBrowserMac(args.skip_update_check)
    else:
        print("Unsupported operating system.")

if __name__ == "__main__":
    main()
