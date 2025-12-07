# FSC-tools
Python scripts to support creating Campaign Cartographer 3+ Symbol Catalogs
This has no external Python module depencies.  It should work with a plain 
Python 3 installation.

## Usage
`FSC_create_symbol_catalog.py [-h] -s SOURCE_DIRS [SOURCE_DIRS ...] -o OUTPUT_FILE`

The SOURCE_DIRS argmuent supports `*` wildcarding in the pathname provided.

The script will process all the PNGs files in the supplied SOURCE_DIRS and will create a CC3+ symbol
catalog file that references them.   Each symbol will be named after the PNG file, minus the .PNG suffixx.
It will do automatic detection of "groups" of symbols based on filenames pattern matching.  The PNGs are 
not modified and are left in the source directories.  The symbol catalog will contain absolute pathnames
each symbol.

Any files that share a common prefix followed by unique numbers will be considered a group and will be marked as such in
the catalog and will also be marked for random selection within the group.   If there are pairs of files that 
follow the varicolor naming convention of "vari 01"/"vari 02" as part of the PNG file name, those will automatically 
be created as varicolor symbols within the catalog.  Varicolor symbols can also be part of a group like normal symbols.

## Usage example:
```
python .\FSC_create_symbol_catalog.py -s "C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\*Monsters*" -o SeaMonsters.FSC`
```
Output received:
```
python .\FSC_create_symbol_catalog.py -s "C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\*Monsters*" -o SeaMonsters.FSC
--- Expanding Source Directory Wildcards ---
  + Expanded: C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\Magnus' Monsters (1539)
  + Expanded: C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\Mercator's Monsters (1569)
  + Expanded: C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\Ortelius' Monsters (1570)
  + Expanded: C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\Vrients' Monsters (1583-1608)
--- Script Configuration ---
Output File: C:\Users\username\source\repos\FSC-tools\SeaMonsters.FSC
Source Directory 1:
  - C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\Magnus' Monsters (1539)
        Symbols created: 28
Source Directory 2:
  - C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\Mercator's Monsters (1569)
        Symbols created: 12
Source Directory 3:
  - C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\Ortelius' Monsters (1570)

[ERROR] Incompatible filename found: 'Ophiotaurus w Dinner.png'
This file contains characters not supported by the 'ascii' standard.
Please rename the file to use only standard ASCII characters and try again.
Skipping this file.

        Symbols created: 24
        Files skipped due to incompatible filenames: 1
Source Directory 5:
  - C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\Vrients' Monsters (1583-1608)
        Symbols created: 21

FSC file written to: .\SeaMonsters.FSC
```

