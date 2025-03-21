import json
import logging

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

        # Track processing results
        processed_count = 0
        failed_count = 0

        # Process each record in the event
        for record in event.get("Records", []):
            try:
                # Make sure this is a DynamoDB record
                if record.get("eventSource") != "aws:dynamodb":
                    logger.warning(f"Skipping non-DynamoDB record: {record.get('eventSource')}")
                    continue

                # Get the DynamoDB data
                dynamodb_data = record.get("dynamodb", {})
                event_name = record.get("eventName")

                # Extract the new and old images if they exist
                new_image = dynamodb_data.get("NewImage")
                old_image = dynamodb_data.get("OldImage")

                # Process based on the event type
                if event_name == "INSERT":
                    logger.info(f"Processing INSERT event: {json.dumps(new_image)}")
                    # TODO: Add your business logic for INSERT events

                elif event_name == "MODIFY":
                    logger.info(f"Processing MODIFY event:")
                    logger.info(f"Old image: {json.dumps(old_image)}")
                    logger.info(f"New image: {json.dumps(new_image)}")
                    # TODO: Add your business logic for MODIFY events
                    # You can compare old_image and new_image to detect specific changes

                elif event_name == "REMOVE":
                    logger.info(f"Processing REMOVE event: {json.dumps(old_image)}")
                    # TODO: Add your business logic for REMOVE events

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
