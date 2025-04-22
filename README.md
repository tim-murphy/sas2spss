# SAS to SPSS file converter
This script converts a directory of SAS data files (sas7bdat format) to SPSS data files (sav format).
There is some error checking though it is limited.
The script does not convert files in subdirectories.

Tested on Python version 3.13 on Windows 11.

## Install (easy version)
Run `install.bat` (Windows only).

## Install (manual version)
Install the required pip packages: `pip install -r requirements.txt`.

## Run
```
usage: import_raw.py [-h] --input_dir INPUT_DIR --output_dir OUTPUT_DIR

options:
  -h, --help            show this help message and exit
  --input_dir INPUT_DIR
                        Directory containing sas7bdat files
  --output_dir OUTPUT_DIR
                        Directory to save converted files
```

If there are any issues converting a file, it will be skipped and an error message printed at the end.
You can safely run this script multiple times as it will not overwrite any existing files.

Example:
`python import_raw.py --input_dir sas --output_dir spss`
