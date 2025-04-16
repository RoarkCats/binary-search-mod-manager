# Binary Search Mod Manager
Modpack tool for finding incompatabilities between mods via dynamic binary searches supporting toggling mods, exclusions, dependencies, and more!

## Installation
- Install/Use Python 3.12 - 3.13
- Place the [mod manager script](binary_search_mod_manager.py) in your modpack directory (in the folder that holds your `mods` folder)
- Run the script and provide input as suggested

## Settings
Settings can be modified by editing the script at the top of the file
```py
MODS_DIR = './mods/'
JAR = '.jar'
DISABLED = '.disabled'
COMPACT_LEN = 16            # str len for mods compact display
COMPACT_PER_LINE = 5        # number of mods to show per line compact display
STATE_FILE_DIR = './'       # dir for state files
STATE_FILE_EXT = '.bsmm'    # file extension for state import/exports
```
