import json
import os
import subprocess
import sys

# import requests

# Add the submodule path to sys.path
# submodule_path = os.path.join(os.path.dirname(__file__), "hem", "src")
# sys.path.append(submodule_path)

# from hem import CsvWriter


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)

    #     raise e

    # return {
    #     "statusCode": 200,
    #     "body": json.dumps(
    #         {"message": "hello world", "location": ip.text.replace("\n", ""), "test_hem": str(CsvWriter)}
    #     ),
    # }

    file_dir = os.path.dirname(__file__)
    hem_submodule_path = os.path.join(file_dir, "hem")
    hem_main_script_path = os.path.join(hem_submodule_path, "src", "hem.py")

    result = subprocess.run(
        [
            "python",
            hem_main_script_path,
            hem_submodule_path + "/test/demo_files/core/demo.json",
            "--display-progress",
            # "--epw-file",
            file_dir + "/GBR_ENG_Eastbourne.038830_TMYx.epw",
        ],
        capture_output=True,
    )
    if result.returncode == 0:
        return {"statusCode": 200}
    else:
        return {"statusCode": 500, "error": result.stderr.decode('utf-8')}


if __name__ == "__main__":
    print(lambda_handler(None, None))
