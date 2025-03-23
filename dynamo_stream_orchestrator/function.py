import json
import logging
import os

from step_function_trigger import trigger_step_function_workflow

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda function handler that processes DynamoDB Stream events.

    Args:
        event (dict): The DynamoDB Stream event containing records with NEW_AND_OLD_IMAGES
        context (LambdaContext): Lambda context object

    Returns:
        dict: Response containing processing results
    """
    try:
        logger.info("Received DynamoDB Stream event")

        # Get the state machine ARN from environment variables
        state_machine_arn = os.environ.get("STATE_MACHINE_ARN")
        if not state_machine_arn:
            raise ValueError("STATE_MACHINE_ARN environment variable is not set")

        # Track processing results
        processed_count = 0
        failed_count = 0

        # Process each record in the event
        for record in event.get("Records", []):
            try:
                # Get the DynamoDB data
                dynamodb_data = record.get("dynamodb", {})
                event_name = record.get("eventName")

                # Extract the new and old images if they exist
                new_image = dynamodb_data.get("NewImage")
                old_image = dynamodb_data.get("OldImage")

                # Process based on the event type
                if event_name == "INSERT":
                    logger.info(f"Processing INSERT event: {json.dumps(new_image)}")
                    uuid = new_image["uuid"]["S"]
                    input_state = {"uuid": uuid}
                    trigger_step_function_workflow(
                        state_machine_arn=state_machine_arn,
                        input_state=input_state,
                    )

                elif event_name == "MODIFY":
                    logger.info("Skipping MODIFY event:")
                    logger.info(f"Old image: {json.dumps(old_image)}")
                    logger.info(f"New image: {json.dumps(new_image)}")

                elif event_name == "REMOVE":
                    logger.info(f"Skipping REMOVE event: {json.dumps(old_image)}")

                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing record: {str(e)}")
                logger.error(f"Record: {json.dumps(record)}")
                failed_count += 1

        logger.info(f"Processed {processed_count} records successfully, {failed_count} failed")

        return {"statusCode": 200, "processed": processed_count, "failed": failed_count}

    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {"statusCode": 500, "error": str(e)}
