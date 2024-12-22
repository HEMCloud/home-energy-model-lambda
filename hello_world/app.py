import os
import subprocess
import sys

# import sys

# Add the submodule path to sys.path
# submodule_path = os.path.join(os.path.dirname(__file__), "hem", "src")
# sys.path.append(submodule_path)

# from hem import CsvWriter


def lambda_handler(event, context):
    file_dir = os.path.dirname(__file__)
    hem_submodule_path = os.path.join(file_dir, "hem")
    hem_main_script_path = os.path.join(hem_submodule_path, "src", "hem.py")


    env = os.environ.copy()
    env['PYTHONPATH'] = '/opt/python/lib/python3.9/site-packages'
    # env["LD_LIBRARY_PATH"] = "/var/lang/lib:/lib64:/usr/lib64:/var/runtime:/var/runtime/lib:/var/task:/var/task/lib:/opt/lib"
    env["PYTHONPATH"] = "/var/task"
    print(sys.executable)
    print(os.environ)
    print(os.path.dirname(__file__))
    print(os.listdir(os.path.dirname(__file__)))


    result = subprocess.run(
        [
            "python",
            hem_main_script_path,
            hem_submodule_path + "/test/demo_files/core/demo.json",
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
