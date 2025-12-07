# FSC-tools
Python scripts to support creating Campaign Cartographer 3+ Symbol Catalogs
This has no external Python module depencies.  It should work with a standard, 
plain Python 3 installation on Windows.

## Usage
### Syntax
`FSC_create_symbol_catalog.py [-h] -s SOURCE_DIRS [SOURCE_DIRS ...] -o OUTPUT_FILE`

### Arguments
*   **`-s SOURCE_DIRS` / `--source-dirs`**: One or more paths to directories containing your PNG symbol files. This argument supports `*` wildcard expansion (globbing) internally within the script for easy use on Windows. Ensure you quote arguments that contain wildcards (e.g., `-s "C:\path\*Monsters*"`).
*   **`-o OUTPUT_FILE` / `--output-file`**: The filename and path for the output `.FSC` catalog file that the script will create.

## Description

The script processes all PNG files in the supplied `SOURCE_DIRS` and creates a CC3+ 
symbol catalog file that references them using absolute pathnames. The original PNG 
files are not modified.

*   Each symbol is named after its PNG filename (minus the `.PNG` extension).
*   **Automatic Grouping:** Files sharing a common prefix followed by unique numbers will be considered a group and marked for random selection within the catalog.
*   **Varicolor Support:** Pairs of files following the `vari_01`/`vari_02` naming convention automatically become varicolor symbols in the catalog.

**⚠️ Important Note on Filenames:**

The CC3+ Symbol Catalog requires filenames and file paths to use standard **ASCII** characters. If any of your PNG files include non-ASCII characters (e.g., specific accented letters or unusual symbols), the script will skip those files and print an error message. Please rename affected files to use only standard English letters, numbers, and symbols.


## Usage example:
To run the script, open your Windows command shell (Command Prompt or Powershell).

**Command:**
```
python .\FSC_create_symbol_catalog.py -s "C:\Users\username\Downloads\Here There Be Monsters PNG Pack 1.1\*Monsters*" -o SeaMonsters.FSC`
```
**Output Received:**
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

