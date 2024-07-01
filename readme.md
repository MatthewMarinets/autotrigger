# Autotrigger
A script library for handling sc2 GUI triggers for the Archipelago project.

Basic functions:
* Read Triggers xml files
* Modify Triggers with scripts
* Generate .galaxy files from Triggers xml
* Offer an interactive console for navigating the element hierarchy and adding some basic functions

This is very much a WIP / hacked-together project focused on getting something that works well enough for particular use-cases rather than being robust to all situations.

## Configuration / Setup
Autotrigger needs the paths to a few key files extracted from the sc2 game data. The game data is in CASC format, and can be extracted with a tool like [Zezula's CascView](http://www.zezula.net/en/casc/main.html). The files in question are nativelib.triggerlib and triggerstrings.txt, both in core.sc2mod mod archive (`core.sc2mod/base.sc2data/triggerlibs/native.triggerlib` and `core.sc2mod/enus.sc2data/localizeddata/triggerstrings.txt`). Autotrigger then needs a `config.json` file containing the following keys:

| key                   | value                           |
| --------------------- | ------------------------------- |
| native                | path to nativelib.triggerlib    |
| native_triggerstrings | path to core triggerstrings.txt |

An example config.json might look like:
```json
{
    "$schema": "./at/config-schema.json",
    "native": "E:/Code/archipelago/sc2_icon_data/core/data/triggerlibs/nativelib.triggerlib",
    "native_triggerstrings": "E:/Code/archipelago/sc2_icon_data/core/data/triggerstrings.txt"
}
```

## Usage
Autotrigger assumes that it is placed in a subdirectory autotrigger/ within a Archipelago-SC2-Data repository clone. Running autotrigger/autotrigger.py currently just loads the ArchipelagoPlayer and ArchipelagoTriggers trigger data and generates .galaxy files to the out/ directory.

Run autotrigger.py with the `-i` flag to enter interactive mode within the ArchipelagoTriggers trigger library, which offers a simple shell for navigating around the library's element hierarchy, querying some basic information, and adding some simple functions.
