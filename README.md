# FSC-tools
Python scripts to support creating Campaign Cartographer 3+ Symbol Catalogs

Requires one external Python module dependency: Pillow, for PNG image dimension fetching
`pip install Pillow`

Usage example:
```
PS C:\> python .\FSC_create_symbol_catalog.py -s "C:\Users\nospa\Downloads\Here There Be Monsters PNG Pack 1.1\*Monsters*" -o SeaMonsters.FSC
--- Expanding Source Directory Wildcards ---
  + Expanded: C:\Users\nospa\Downloads\Here There Be Monsters PNG Pack 1.1\Magnus' Monsters (1539)
  + Expanded: C:\Users\nospa\Downloads\Here There Be Monsters PNG Pack 1.1\Mercator's Monsters (1569)
  + Expanded: C:\Users\nospa\Downloads\Here There Be Monsters PNG Pack 1.1\Ortelius' Monsters (1570)
  + Expanded: C:\Users\nospa\Downloads\Here There Be Monsters PNG Pack 1.1\Vrients' Monsters (1583-1608)
--- Script Configuration ---
Output File: C:\Users\nospa\source\repos\FSC-tools\SeaMonsters.FSC
Source Directory 1:
  - C:\Users\nospa\Downloads\Here There Be Monsters PNG Pack 1.1\Magnus' Monsters (1539)
        Symbols created: 28
Source Directory 2:
  - C:\Users\nospa\Downloads\Here There Be Monsters PNG Pack 1.1\Mercator's Monsters (1569)
        Symbols created: 12
Source Directory 3:
  - C:\Users\nospa\Downloads\Here There Be Monsters PNG Pack 1.1\Ortelius' Monsters (1570)

[ERROR] Incompatible filename found: 'Ophiotaurus w Dinner.png'
This file contains characters not supported by the 'ascii' standard.
Please rename the file to use only standard ASCII characters and try again.
Skipping this file.

        Symbols created: 24
        Files skipped due to incompatible filenames: 1
Source Directory 5:
  - C:\Users\nospa\Downloads\Here There Be Monsters PNG Pack 1.1\Vrients' Monsters (1583-1608)
        Symbols created: 21

FSC file written to: .\SeaMonsters.FSC
```

