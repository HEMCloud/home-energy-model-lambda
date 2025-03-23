import boto3
import json


def trigger_hem_model_run(state_machine_arn: str, input_state: dict | None = None):
    """
    Triggers an AWS Step Function workflow.

    Parameters:
        workflow_arn (str): The ARN of the Step Function workflow to trigger.
        input_data (dict, optional): The input data to pass to the workflow. Defaults to None.

    Returns:
        dict: The response from the Step Functions StartExecution API.
    """
    # Initialize the Step Functions client
    stepfunctions_client = boto3.client("stepfunctions")

    # Prepare the input data as a JSON string
    input_json = json.dumps(input_state) if input_state else "{}"

    # Start the Step Function execution
    response = stepfunctions_client.start_execution(stateMachineArn=state_machine_arn, input=input_json)
    return response
