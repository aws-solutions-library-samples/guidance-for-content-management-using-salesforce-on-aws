import json
import os
import re
import boto3

def lambda_handler(event, context):
    print("Entering Lambda handler.  Printing Event")
    print(event)

    s3 = boto3.client("s3")

    if "Sns" in event["Records"][0]:
      event = event["Records"][0]["Sns"]["Message"]
      print("SNS Message")
      print(event)
      event=json.loads(event)
      if "Records" not in event:
        print("Test message.  Halting processing")
        return

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    file_name = os.path.basename(key)

    print(bucket)
    print(key)

    match = re.search(r"([^/]+)/transcribed_files", key)

    if match:
      object_id = match.group(1)
      output_file = key + ".metadata.json"
      metadata = {
          "Attributes": {
              "object_id": object_id
          }
      }

      s3.put_object(Bucket=bucket, Key=output_file, Body=json.dumps(metadata))

    return