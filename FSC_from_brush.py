import argparse
import os
import sys
import subprocess

def main():
    # 1. Initialize the parser and set the program description
    parser = argparse.ArgumentParser(
        prog="FSC_from_brush",
        description="A utility to extract PNGs from Adobe brush (ABR) files and create a CC3+ symbol catalog referencing them."
    )

    parser.add_argument(
        '-p', '--png-create',
        action='store_true',
        help="Enable PNG file creation (flag)."
    )

    parser.add_argument(
        '-v', '--varicolor',
        action='store_true',
        help="Enable varicolor PNG creation (flag)."
    )
    
    parser.add_argument(
        '-b', '--brush-file',
        type=str,
        required=True,
        help="Path to the input Adobe brush (.abr) file."
    )

    parser.add_argument(
        '-d', '--output-dir',
        type=str,
        required=True,
        help="Destination directory for output symbols (e.g., C:\\mysymbols)."
    )

    args = parser.parse_args()

    # Verify that the brush file exists
    if not os.path.isfile(args.brush_file):
        print(f"Error: The specified brush file does not exist: {args.brush_file}")
        sys.exit(1)

    # You can now use these values in your script logic:
    if args.png_create or args.varicolor:
        print("Processing initiated...")

        # Save existing working directory to return later
        original_dir = os.getcwd()

        # Change working directory to output directory, create if it doesn't exist
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
            output_dir = os.path.abspath(args.output_dir)
        else:
            output_dir = os.path.abspath(args.output_dir)
        os.chdir(output_dir)

        if args.png_create:
            command = ["abr2png"]
            command.extend(["-png", args.brush_file])
            subprocess.run(command) 
        if args.varicolor:
            command = ["abr2png"]
            command.extend(["-cc3", args.brush_file])
            subprocess.run(command)

        # Return to the original directory where we started
        os.chdir(original_dir)

        # Run FSC_create_symbol_catalog.py to create the catalog
        # Use the output directory name as the catalog name, appended with ".FSC" extension
        catalog_name = os.path.basename(output_dir) + ".FSC"
        command = [
            "python", "FSC_create_symbol_catalog.py",
            "-s", output_dir,
            "-o", catalog_name
        ]
        subprocess.run(command)
    else:
        print("No operation flags specified (-p or -v). Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    main()

