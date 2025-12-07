# ----------------------------------------------------------------------
# A script to process PNG symbol files into an FSC Symbol Catalog.
# It identifies single symbols and varicolor symbol pairs based on naming conventions,
# and groups them accordingly. The resulting symbols are then combined with InfoBlocks
# to produce a final FSC file for use in CC3+.
#
# NOTE: The original source PNGs are not moved nor are they included in the FSC file; 
# only references to their paths are stored in the FSC.
# ----------------------------------------------------------------------
# Usage example:
# python .\FSC_create_symbol_catalog.py -s "C:\Users\name\Downloads\Here There Be Monsters PNG Pack 1.1\Vrients' Monsters (1583-1608)" "C:\Users\name\Downloads\my_random_symbol_sea_monster_collection" -o SeaMonsters.FSC
# ----------------------------------------------------------------------
# Author: Brian Stormont
# Date: 2025-12-06
# Version: 0.1
# License: MIT License
# ----------------------------------------------------------------------


import os
import re
import argparse
import sys
import glob
from collections import defaultdict
from FSCtypes import *
from InfoBlocks import IB

def parse_arguments():
    """
    Sets up the argument parser and returns the parsed arguments object.
    """
    parser = argparse.ArgumentParser(
        description="Process symbol PNG files into a single FSC output file.",
        epilog="Example: python FSC_create_symbol_catalog.py -s ./dir1 ./dir2 -o output.fsc"
    )

    # Define the -s argument for source directories
    parser.add_argument(
        '-s', 
        '--source-dirs', 
        nargs='+',              # Expects one or more arguments
        required=True,          # This argument is mandatory
        help='List of source directories containing PNG files (supports wildcards like "symbol_dirs_*").'
    )

    # Define the -o argument for the output file
    parser.add_argument(
        '-o', 
        '--output-file', 
        type=str,               # Expects a string
        required=True,          # This argument is mandatory
        help='The name and path for the output .fsc file.'
    )

    # Parse the actual arguments passed to the script
    args = parser.parse_args()
    
    return args

LEGACY_ENCODING = 'ascii'
def check_filename_compatibility(filename):
    """
    Checks if a filename can be safely encoded to the legacy system's encoding.
    Returns True if compatible, False otherwise.
    """
    try:
        # Attempt to encode the filename using the legacy encoding strictly
        filename.encode(LEGACY_ENCODING, errors='strict')
        return True
    except UnicodeEncodeError:
        # If an error occurs, it means a character is incompatible
        return False

def process_symbol_images(directory_path):

    all_symbols = []

    # This regex captures: 
    # (.*?) -> The symbol name (non-greedy match for anything)
    # \s+vari_0[1-2]{1}\.png$ -> Matches the ' vari_XX.png' suffix
    variant_pattern = re.compile(r"(.*?)\s+vari_0[1-2]{1}\.png$", re.IGNORECASE)
    subgroup_pattern = re.compile(r"^(.*?)(\d+)$", re.IGNORECASE)

    # Dictionary to hold lists of files, grouped by their base name
    groups = defaultdict(list)
    subgroup_variant = defaultdict(list)  # Hold names without any number extension
    subgroup_normal = defaultdict(list)  # Hold names without any number extension
    skip_count = 0

    # 1. First pass: Identify base names and group files
    for filename in os.listdir(directory_path):
        if not filename.lower().endswith('.png'):
            continue

        # --- FILENAME COMPATIBILITY CHECK ---
        if not check_filename_compatibility(filename):
            print(f"\n[ERROR] Incompatible filename found: '{filename}'")
            print(f"This file contains characters not supported by the '{LEGACY_ENCODING}' standard.")
            print("Please rename the file to use only standard ASCII characters and try again.")
            print("Skipping this file.\n")
            skip_count += 1
            continue # Skip this file and move to the next one
        # ------------------------------------
            
        full_path = os.path.join(directory_path, filename)
        
        # Check if the file matches the variant pattern
        match = variant_pattern.match(filename)
        
        if match:
            # If it's a variant, the base name is the captured group (symbol name)
            base_symbol_name = match.group(1)
        else:
            # If it's a single file (e.g., "Walled Garden 001.png"), 
            # its base name is its filename without the .png extension
            base_symbol_name = os.path.splitext(filename)[0]

        groups[base_symbol_name].append(full_path)

        # Further process to identify subgroups without number extensions
        subgroup_match = subgroup_pattern.match(base_symbol_name)
        if subgroup_match:
            name_without_number = subgroup_match.group(1)
            if (match):
                subgroup_variant[name_without_number].append(full_path)
            else:
                subgroup_normal[name_without_number].append(full_path)

    # 2. Second pass: Process the groups based on group size
    for symbol_name, files in groups.items():
        if len(files) == 2 and all("vari_" in f for f in files):
            # Sort files by name to ensure consistent handling of _01 and _02
            files.sort()

            # Check if the file is part of the subgroup_variant.
            # If so, and if there are more than 2 files in that subgroup, set group to True
            # We need more than 2 because the current two are just a single pair of variants.
            group = False
            subname_match = subgroup_pattern.match(symbol_name)
            if subname_match:
                if subname_match.group(1) in subgroup_variant:
                    if len(subgroup_variant[subname_match.group(1)]) > 2:
                        group = True

            all_symbols.append(bytes(handle_variant_pair(symbol_name, files[0], files[1], group)))
        
        elif len(files) == 1 and "vari_" not in files[0]:
            # Check if the file is part of the subgroup_normal.
            group = False
            subname_match = subgroup_pattern.match(symbol_name)
            if subname_match:
                if subname_match.group(1) in subgroup_normal:
                    if len(subgroup_normal[subname_match.group(1)]) > 1:
                        group = True
            all_symbols.append(bytes(handle_single_symbol(symbol_name, files[0], group)))
            
        else:
            print(f"--- Warning: Unhandled group for '{symbol_name}': {files} ---")

    print(f"\tSymbols created: {len(all_symbols)}")
    if skip_count > 0:
        print(f"\tFiles skipped due to incompatible filenames: {skip_count}")

    return b"".join(all_symbols)

def handle_variant_pair(symbol_name, file_01_path, file_02_path, isGroup):
#    print(f"  File 1: {os.path.basename(file_01_path)}")
#    print(f"  File 2: {os.path.basename(file_02_path)}")
#    print(f"  Is part of subgroup: {isGroup}")

    vari_symbol = VaricolorSymbol(symbol_name, os.path.normpath(file_01_path), os.path.normpath(file_02_path), isGroup)
    return vari_symbol

def handle_single_symbol(symbol_name, file_path, isGroup):
#    print(f"  File: {os.path.basename(file_path)}")
#    print(f"  Is part of subgroup: {isGroup}")

    single_symbol = SimpleSymbol(symbol_name, os.path.normpath(file_path), isGroup)
    return single_symbol

# ----------------------------


# --- Main execution block ---
if __name__ == "__main__":
    # This is a work-in-progress script to process PNG symbol files into FSC symbol objects.
    # Eventual goal is to combine my brush extraction program with this one to produce a workflow that:
    #   1) extracts PNGs from an ABR file
    #   2) processes those PNGs into SingleSymbol and VaricolorSymbol objects
    #   3) combines those symbol objects with InfoBlocks to produce final FSC files for CC3+

    # Parse command line arguments for source directories (one or more) and an output file name
    # -s [<source_directory> <source_directory2> ...] -o <output_fsc_file>
    args = parse_arguments()

    # List to store all final, expanded directory paths
    expanded_source_dirs = []

    print("--- Expanding Source Directory Wildcards ---")

    for potential_pattern in args.source_dirs:
        # Use glob.glob() to expand the wildcard into a list of matching paths
        # glob() returns an empty list if no matches are found
        matches = glob.glob(potential_pattern)
        
        if matches:
            for match in matches:
                # Ensure we only add actual directories, not files that matched the pattern
                if os.path.isdir(match):
                    expanded_source_dirs.append(os.path.normpath(match)) # Use normpath for clean OS style
                    print(f"  + Expanded: {match}")
                else:
                    print(f"  - Skipped: {match} (is a file, not a directory)")
        else:
            # If glob found nothing, treat the input string as a literal path and check if it exists
            if os.path.isdir(potential_pattern):
                 expanded_source_dirs.append(os.path.normpath(potential_pattern))
                 print(f"  + Added literal directory: {potential_pattern}")
            else:
                 print(f"  - Warning: Source directory not found: {potential_pattern}")


    if not expanded_source_dirs:
        print("\nError: No valid source directories found after expansion.")
        sys.exit(1)

    print(f"--- Script Configuration ---")
    print(f"Output File: {os.path.abspath(args.output_file)}")
    symbol_list = []
    dir_count=1
    for directory in expanded_source_dirs:
        print(f"Source Directory {dir_count}:")
        print(f"  - {os.path.abspath(directory)}")
        symbols_from_dir = process_symbol_images(directory)
        symbol_list.append(symbols_from_dir)
        dir_count += 1
    symbols = b"".join(symbol_list)


    # Build the canned info blocks
    infoblocks = IB.assemble_info_blocks()

    # Create the symbol objects from the PNG files in the source directory
    #symbol_list = process_symbol_images("C:/Users/nospa/Downloads/Here There Be Monsters PNG Pack 1.1/Vrients' Monsters (1583-1608)")
    #symbol_list2 = process_symbol_images("C:/Users/nospa/Downloads/here-there-be-monsters-1.1/Here There Be Monsters 1.1/PNG")
    
    # Create the FSC header
    fsc_header = FileID()

    # For now, create noncompressed FSC file
    # Write out all the parts to a single file
    output_fsc_path = os.path.join(".", "output_symbols.fsc")
    with open(output_fsc_path, "wb") as fsc_file:
        fsc_file.write(bytes(fsc_header))
        fsc_file.write(bytes(infoblocks))
        fsc_file.write(symbols) 
        print(f"\nFSC file written to: {output_fsc_path}")





