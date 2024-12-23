import os
import shutil
import subprocess
import sys

# import sys

# Add the submodule path to sys.path
# submodule_path = os.path.join(os.path.dirname(__file__), "hem", "src")
# sys.path.append(submodule_path)

# from hem import CsvWriter

import debugpy

debugpy.listen(("0.0.0.0", 3488))
debugpy.wait_for_client()


def lambda_handler(event, context):
    file_dir = os.path.dirname(__file__)
    hem_submodule_path = os.path.join(file_dir, "hem")
    hem_main_script_path = os.path.join(hem_submodule_path, "src", "hem.py")
    source_file_path = os.path.join(hem_submodule_path, "test/demo_files/core/demo.json")
    temp_dir_path = "/tmp/hem-inputs"
    os.makedirs(temp_dir_path, exist_ok=True)

    """
    We have to copy the input file to a temp directory because the HEM module
    outputs CSV results to the same directory as the input file, which is
    read-only in AWS Lambda. /tmp is the only writable directory in AWS Lambda.
    """
    temp_file_path = os.path.join(temp_dir_path, "demo.json")
    shutil.copy(source_file_path, temp_file_path)

    """
    When running a subprocess in AWS Lambda, the PYTHONPATH environment variable
    needs to be set to include the directory where the Lambda script is located.
    This is where AWS SAM stores all the dependencies.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = "/var/task"
    result = subprocess.run(
        [
            "python",
            hem_main_script_path,
            temp_file_path,
            "--display-progress",
            "--epw-file",
            file_dir + "/GBR_ENG_Eastbourne.038830_TMYx.epw",
        ],
        capture_output=True,
        env=env,
    )

    if result.returncode == 0:
        return {"statusCode": 200}
    else:
        return {"statusCode": 500, "error": result.stderr.decode("utf-8")}


if __name__ == "__main__":
    print(lambda_handler(None, None))
