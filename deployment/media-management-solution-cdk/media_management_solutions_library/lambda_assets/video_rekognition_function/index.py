import json
import boto3
import os
from urllib.parse import unquote_plus

rekognition_client = boto3.client('rekognition')
s3_client = boto3.client('s3')


def lambda_handler (event, context):
    print(event)
    if "Sns" in event["Records"][0]:
        event = event["Records"][0]["Sns"]["Message"]
        print("SNS Message")
        print(event)
        event = json.loads(event)
        if "Records" not in event:
            print("Test message.  Halting processing")
            return

    key = (event["Records"][0]["s3"]["object"]["key"])
    key=unquote_plus(key)

    if "audio_redacted" in key:
        print("This is a redacted file.  Halting")
        return
    bucket = (event["Records"][0]["s3"]["bucket"]["name"])

    response = rekognition_client.start_label_detection(
        Video={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        NotificationChannel={
            'SNSTopicArn': os.environ["VidRekJobCompleteArn"],
            'RoleArn': os.environ["RekognitionToSNSRole"]
        }
    )

    print(response)