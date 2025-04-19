# import pyreadstat
import argparse
import glob
import os
import sys

def confirm_yes_no(text):
    response = None

    while response not in ("y", "n"):
        response = input(text + " (y/n): ")

        # if no response was given, don't try to substring it.
        if len(response) > 0:
            response = response.lower()[0]

    return response == "y"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, required=True, help="Directory containing sas7bdat files")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save converted files")
    args = parser.parse_args()

    # Error checking.
    bad_args = False

    for (dir_path, can_create) in ((args.input_dir, False), (args.output_dir, True)):
        if not os.path.isdir(dir_path):
            if not can_create:
                print("ERROR: directory does not exist: '" + dir_path + "'", file=sys.stderr)
                bad_args = True
            else:
                if confirm_yes_no("Directory does not exixt: '" + dir_path + "'! Do you want to create it?"):
                    print("Creating directory...", end="", flush=True)
                    os.makedirs(dir_path)
                    print("done")
                else:
                    print("ERROR: not creating directory.", file=sys.stderr)
                    bad_args = True

    if bad_args:
        print("An error occurred while parsing the command line arguments. Goodbye.")
        sys.exit(1)

    files_copied = 0
    for sas in glob.glob(os.path.join(args.input_dir, "*.sas7bdat")):
        file_root = os.path.splitext(os.path.split(sas)[1])[0]
        outfile = os.path.join(args.output_dir, file_root + ".sav")

        print("Copyting ", sas, " to ", outfile, "...", sep="", end="", flush=True)
        # df, _ = pyreadstat.read_file_multiprocessing(pyreadstat.read_sas7bdat, sas)
        # pyreadstat.write_sav(df, outfile, file_label=file_root)
        print("done")

        files_copied += 1

    print(files_copied, "files copied to", args.output_dir)
    print()
    print("All done! Have a nice day :)")

# EOF
