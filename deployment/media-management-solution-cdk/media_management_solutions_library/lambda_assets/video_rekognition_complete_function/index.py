import json
import boto3
import os

rekognition_client = boto3.client('rekognition')
s3_client = boto3.client('s3')


def lambda_handler (event, context):
    print(event)

    event = event["Records"][0]["Sns"]["Message"]

    print(event)
    event = json.loads(event)
    jobId = (event["JobId"])
    S3Bucket = (event["Video"]["S3Bucket"])
    S3ObjectName = (event["Video"]["S3ObjectName"])

    print("JobId: %s " % jobId)
    print("S3Bucket: %s " % S3Bucket)
    print("S3ObjectName: %s " % S3ObjectName)

    savefile = "video_labels/" + S3ObjectName + ".rek.json"

    if "/" in S3ObjectName:
        prefix = os.path.dirname(S3ObjectName)
        filename = os.path.basename(S3ObjectName) + ".rek.json"
        savefile = prefix + "/video_labels/" + filename

    print("Save File name is %s " % savefile)

    # For production, need to handle token in response and next segment
    rek_response = rekognition_client.get_label_detection(
        JobId=jobId,
        SortBy='TIMESTAMP'
    )

    print(rek_response)

    response = s3_client.put_object(
        Body=(bytes(json.dumps(rek_response).encode('UTF-8'))),
        Bucket=os.environ["OUTPUT_BUCKET"],
        Key=savefile
    )
    print(response)