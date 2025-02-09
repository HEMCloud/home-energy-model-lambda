import logging
import os
import subprocess
import json

# import sys

# Add the submodule path to sys.path
# submodule_path = os.path.join(os.path.dirname(__file__), "hem", "src")
# sys.path.append(submodule_path)

# from hem import CsvWriter

import debugpy

from convert_summary_csv_to_json import csv_to_json

debugpy.listen(("0.0.0.0", 3488))
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    file_dir = os.path.dirname(__file__)
    hem_submodule_path = os.path.join(file_dir, "hem")
    hem_main_script_path = os.path.join(hem_submodule_path, "src", "hem.py")
    temp_dir_path = "/tmp/hem-inputs"
    os.makedirs(temp_dir_path, exist_ok=True)

    """
    We have to write the event to an input file in a temp directory because the HEM module outputs CSV results to the
    same directory as the input file, which is read-only in AWS Lambda. /tmp is the only writable directory in AWS
    Lambda.
    """
    input_file_name = "demo"
    input_file_path = os.path.join(temp_dir_path, input_file_name + ".json")
    with open(input_file_path, "w") as f:
        json.dump(event, f)

    """
    When running a subprocess in AWS Lambda, the PYTHONPATH environment variable needs to be set to include the
    directory where the Lambda script is located. This is where AWS SAM stores all the dependencies.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = "/var/task"
    logger.info(f"Running HEM with input file: {input_file_path}")
    result = subprocess.run(
        [
            "python",
            hem_main_script_path,
            input_file_path,
            "--epw-file",
            file_dir + "/GBR_ENG_Eastbourne.038830_TMYx.epw",
        ],
        capture_output=True,
        env=env,
    )
    logger.info(f"HEM subprocess return result: {result}")

    if result.returncode == 0:
        # This logic is copied from the HEM module: src.hem.py, line 74 - 95
        results_folder_path = os.path.join(temp_dir_path, input_file_name + "__results", "")
        output_file_name_stub_path = results_folder_path + input_file_name + "__" + "core" + "__"
        summary_csv_filepath = output_file_name_stub_path + "results_summary.csv"
        result_data = csv_to_json(summary_csv_filepath)
        return {"statusCode": 200, "body": result_data, "headers": {"Content-Type": "application/json"}}
    else:
        return {"statusCode": 500, "error": result.stderr.decode("utf-8")}


if __name__ == "__main__":
    file_dir = os.path.dirname(__file__)
    hem_submodule_path = os.path.join(file_dir, "hem")
    demo_event = json.load(open(hem_submodule_path + "/test/demo_files/core/demo.json"))
    print(lambda_handler(demo_event, None))
