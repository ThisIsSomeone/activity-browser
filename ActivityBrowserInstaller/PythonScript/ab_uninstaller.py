#ab_uninstaller.py
#Made on 22/04/2024
#Contributed by Thijs Groeneweg and Ruben Visser
#Documented by Arian Farzad
#Last edited on 05/06/2024 by Arian Farzad

#Obtain the working directory and construct a path to the nested environment directory
#Once it succeeds it then attempts to remove this directory using shutil.rmtree()
#Prints whether or not the directory is found and succesfully removed

#Imports
import shutil
import os

def getActivityBrowserFilename() -> str:
        """
        Get the filename of the ActivityBrowser executable in the current directory.

        Returns:
        - str: The filename of the ActivityBrowser executable.
        """
        for filename in os.listdir("."):
            if filename.startswith("ActivityBrowser-"):
                return filename
        return None

if __name__ == "__main__":
    currentDirectory = os.getcwd()
    directoryPath = os.path.join(currentDirectory, "ActivityBrowserEnvironment")

    try:
        shutil.rmtree(directoryPath)
        print(f"Directory '{directoryPath}' successfully removed.")
    except FileNotFoundError:
        print(f"Directory '{directoryPath}' not found.")

    try:
        os.remove(getActivityBrowserFilename())
    except FileNotFoundError:
        print("ActivityBrowser file not found in the directory.")