#ab_uninstaller.py
#Made on 22/04/2024
#Contributed by Thijs Groeneweg and Ruben Visser
#Documented by Arian Farzad
#Last edited on 05/06/2024 by Arian Farzad

#Creates a directory and extracts the contents
#of the compressed 'ActivityBrowser.tar.gz' file into this directory

#Imports
import os
import subprocess

# Define environment directory
envDir = "ActivityBrowserEnvironment"

# Create the environment directory
os.makedirs(envDir, exist_ok=True) 

# Extract the environment
subprocess.run(["tar", "-xzf", "ActivityBrowser.tar.gz", "-C", envDir])
