'''
Script to batch convert a directory of SAS files (sas7bdat extension) to
SPSS files (sav extension).

Written by Tim Murphy <tim.murphy@canberra.edu.au> 2025
'''

import argparse
import glob
import os
import sys

import pyreadstat

def confirm_yes_no(text):
    '''
    Prompt the user to answer y or n to a question.
    @return True if the answer is y, or False otherwise.
    @param text The text displayed to the user.
    '''

    response = None

    while response not in ("y", "n"):
        response = input(text + " (y/n): ")

        # if no response was given, don't try to substring it.
        if len(response) > 0:
            response = response.lower()[0]

    return response == "y"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, required=True,
                        help="Directory containing sas7bdat files")
    parser.add_argument("--output_dir", type=str, required=True,
                        help="Directory to save converted files")
    args = parser.parse_args()

    # Error checking.
    bad_args: bool = False

    for (dir_path, can_create) in ((args.input_dir, False), (args.output_dir, True)):
        if not os.path.isdir(dir_path):
            if not can_create:
                print("ERROR: directory does not exist: '" + dir_path + "'", file=sys.stderr)
                bad_args = True # pylint: disable=invalid-name
            else:
                if confirm_yes_no("Directory does not exixt: '" + dir_path +\
                                  "'! Do you want to create it?"):
                    print("Creating directory...", end="", flush=True)
                    os.makedirs(dir_path)
                    print("done")
                else:
                    print("ERROR: not creating directory.", file=sys.stderr)
                    bad_args = True # pylint: disable=invalid-name

    if bad_args:
        print("An error occurred while parsing the command line arguments. Goodbye.")
        sys.exit(1)

    files_copied: int = 0
    failures = []   # (filename, error)
    for sas in glob.glob(os.path.join(args.input_dir, "*.sas7bdat")):
        file_root = os.path.splitext(os.path.split(sas)[1])[0]
        outfile = os.path.join(args.output_dir, file_root + ".sav")

        if os.path.exists(outfile):
            print("Skipping file as it already exists:", outfile)
            continue

        print("Copying ", sas, " to ", outfile, "...", sep="", end="", flush=True)
        try:
            df, _ = pyreadstat.read_file_multiprocessing(pyreadstat.read_sas7bdat, sas)

            # Some columns start with an underscore, which is not allowed by write_sav.
            cols_clean = []
            for col in df.columns:
                if col[0] == "_":
                    cols_clean.append("v" + col)
                else:
                    cols_clean.append(col)
            df.columns = cols_clean

            pyreadstat.write_sav(df, outfile, file_label=file_root)
            files_copied += 1
            print("done")
        except Exception as e: # pylint: disable=broad-exception-caught
            failures.append((file_root, str(e)))
            print("!!! FAILED !!!")

    print(files_copied, "files copied to", args.output_dir)
    print()

    if len(failures) > 0:
        print("The following files could not be copied:")
        for (path, err) in failures:
            print("   ", path, "::", err)

    print("All done! Have a nice day :)")

# EOF
