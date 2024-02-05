import json
import boto3
import os

rekognition_client = boto3.client('rekognition')
s3_client = boto3.client('s3')


def lambda_handler (event, context):
    print(event)
    if "Sns" in event["Records"][0]:
        event = event["Records"][0]["Sns"]["Message"]
        print("SNS Message")
        print(event)
        if "Records" not in event:
            print("Test message.  Halting processing")
            return

    event = json.loads(event)
    key = (event["Records"][0]["s3"]["object"]["key"])
    bucket = (event["Records"][0]["s3"]["bucket"]["name"])

    response = rekognition_client.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        }
    )

    print(response)

    prefix = os.path.dirname(key)
    obj_name = os.path.basename(key)

    savepath = "image_metadata/"
    if "/" in key:
        savepath = prefix + "/" + savepath

    saveKey = savepath + obj_name + ".rekog.json"

    S3response = s3_client.put_object(
        Body=bytes(json.dumps(response).encode('UTF-8')),
        Bucket=os.environ["OUTPUT_BUCKET"],
        Key=saveKey
    )

    print(S3response)