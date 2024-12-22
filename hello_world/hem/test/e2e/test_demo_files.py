import os
import subprocess

import pytest

from src.hem import CIBSE_weather_data_to_dict, run_project


def _run_command(cmd: str):
    print(f"executing cmd: {cmd}")
    # TODO: Use subprocess.run
    ret = os.system(cmd)
    assert ret == 0, f"{cmd}"


def _test_demo_file(root: str, file: str, external_conditions_dict: dict):
    # Run HEM on a demo file and check its results against the expected results
    dirs = os.path.normpath(root).split(os.path.sep)
    assert dirs[2] in ["core", "wrappers"]
    if dirs[2] == "core" and len(dirs) != 3:
        return
    if dirs[2] == "wrappers" and len(dirs) != 4:
        return
    demo_dir = dirs[2:]
    demo_base = file[:-5]  # Remove the trailing .json
    demo_file = os.path.join(root, f"{file}")
    hem_flags = ["--future-homes-standard"] if "future_homes_standard" in root else []
    # cmd = f"{python_exe} {hem_py} -w \"{weather_file}\" {' '.join(hem_flags)} {demo_file}"
    # _run_command(cmd)
    run_project(demo_file, external_conditions_dict=external_conditions_dict)
    demo_type = "FHS" if (dirs[2] == "wrappers" and dirs[3] == "future_homes_standard") else dirs[2]
    # Results will be output in test/demo_files/{*demo_dir}/{demo_base}__results/{demo_file}__{demo_type}__results.csv
    results_file = os.path.join(root, f"{demo_base}__results", f"{demo_base}__{demo_type}__results.csv")
    # Expected results are in test/e2e/expected_results/{*demo_dir}/{demo_base}__results/{demo_file}__{demo_type}__results.csv
    expected_results_file = os.path.join(
        "test", "e2e", "expected_results", *demo_dir, f"{demo_base}__results", f"{demo_base}__{demo_type}__results.csv"
    )
    # Compare the 2 files
    cmd = f"diff {results_file} {expected_results_file}"
    _run_command(cmd)


def test_all_demo_files():
    # Run HEM with all the files under the directory test/demo_files
    weather_file = os.getenv("HEM_WEATHER_FILE")
    if not weather_file:
        print("No weather file defined. Please set its filename using the env var HEM_WEATHER_FILE")
        exit(1)

    external_conditions_dict = CIBSE_weather_data_to_dict(weather_file)
    for root, dirs, files in os.walk(os.path.join("test", "demo_files")):
        for file in files:
            if file.endswith(".json"):
                _test_demo_file(root, file, external_conditions_dict)
