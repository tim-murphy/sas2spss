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

def format_to_ext(output_format: str):
    if output_format == "spss":
        return ".sav"
    elif output_format == "csv":
        return ".csv"
    else:
        raise ValueError("No extension for format: " + output_format)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, required=True,
                        help="Directory containing sas7bdat files")
    parser.add_argument("--output_dir", type=str, required=True,
                        help="Directory to save converted files")
    parser.add_argument("--single_file", type=str, required=False,
                        help="If set, will also (outer) merge into one file with this filename")
    parser.add_argument("--merge_keys", default=["ID"], nargs="+",
                        help="If merging, use this as the merge key")
    parser.add_argument("--prefix_vars", default=False, action="store_true",
                        help="Add the filename as a prefix to variables")
    parser.add_argument("--merge_type", type=str, default="outer",
                        choices=("inner", "outer", "left", "right"),
                        help="The type of merge / join")
    parser.add_argument("--output_format", type=str, default="spss",
                        choices=("csv", "spss"),
                        help="The output format")
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
    merge_failures = []   # (filename, error)
    merged = None # pylint: disable=invalid-name

    datfiles = glob.glob(os.path.join(args.input_dir, "*.sas7bdat"))
    for i, sas in enumerate(datfiles):
        print("[", i+1, " / ", len(datfiles), "] ", sep="", end="", flush=True)

        file_root = os.path.splitext(os.path.split(sas)[1])[0]
        outfile = os.path.join(args.output_dir, file_root + format_to_ext(args.output_format))

        skip: bool = False
        if os.path.exists(outfile):
            print("Skipping file as it already exists:", outfile)
            skip = True # pylint: disable=invalid-name
        else:
            print("Copying ", sas, " to ", outfile, "...", sep="", end="", flush=True)

        if skip and args.single_file is None:
            continue

        try:
            df, _ = pyreadstat.read_file_multiprocessing(pyreadstat.read_sas7bdat, sas)

            # Some columns start with an underscore, which is not allowed by write_sav.
            cols_clean = []
            for col in df.columns:
                clean = col

                # Variables cannot start with an underscore.
                if col[0] == "_":
                    clean = "v" + col

                # Data cleaning: merge keys are case sensitive.
                iskey: bool = False
                for key in args.merge_keys:
                    if clean.casefold() == key.casefold():
                        clean = key
                        iskey = True # pylint: disable=invalid-name

                # Some variable names may be duplicated between files.
                if args.prefix_vars and not iskey:
                    clean = file_root + "_" + clean

                cols_clean.append(clean)

            df.columns = cols_clean

            # Merge the dataframes.
            if args.single_file is not None:
                if merged is None:
                    merged = df.copy(deep=True)
                else:
                    try:
                        merged = merged.merge(df, on=args.merge_keys, sort=True,
                                              validate="one_to_one", how=args.merge_type)
                    except Exception as e: # pylint: disable=broad-exception-caught
                        merge_failures.append((file_root, str(e)))
                        print("!!! FAILED TO MERGE !!!")

            if not skip:
                if args.output_format == "spss":
                    pyreadstat.write_sav(df, outfile, file_label=file_root)
                elif args.output_format == "csv":
                    df.to_csv(outfile, encoding="utf-8", index=False, header=True)
                else:
                    # This should never happen.
                    raise ValueError("Could not save file: invalid output format " + args.output_format)

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
        print()

    # Write the merged file to disk. This may take some time...
    if merged is not None:
        try:
            merged_outfile = os.path.join(args.output_dir, args.single_file)
            print("Writing merged file to ", merged_outfile, "...", end="", sep="", flush=True)
            pyreadstat.write_sav(merged, merged_outfile)
            print("done")
        except Exception as e: # pylint: disable=broad-exception-caught
            print()
            print("Error creating merged file: " + str(e), file=sys.stderr)
            print(merged)

        print()

    if len(merge_failures) > 0:
        print("The following files could not be merged:")
        for (path, err) in merge_failures:
            print("   ", path, "::", err)
        print()

    print("All done! Have a nice day :)")

# EOF
