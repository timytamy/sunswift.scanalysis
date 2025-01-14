import sys
import os.path
import imp

#disabled = ["__init__.py", "CanBridgeDriver.py"]
disabled = ["__init__.py", "CanBridgeDriver.py", "CourseProfile.py", "Strategy.py", "Testpage.py", "Calibrator.py"]
#disabled = ["__init__.py"]
#disabled = ["__init__.py", "Calibrator.py"]

# Adds all real python files to this module -- we want to import all drivers
# Loads all modules in "Drivers" which haven't been loaded yet. 
__all__=[]
files = os.listdir("Drivers")
for file in files:
    if file[-3:] == ".py":
        if file not in disabled:
            name = file[0:-3]
            __all__.append(file[0:-3])
