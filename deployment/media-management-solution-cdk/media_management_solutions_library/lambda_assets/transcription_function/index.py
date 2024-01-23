import json
import boto3
import os
import random
import string

transcribe_client = boto3.client('transcribe')

def lambda_handler(event, context):
    print("Entering Lambda handler.  Printing Event")
    print(event)

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

    if file_name.startswith('audio_redacted-') == True:
      print("This audio file is redacted.  Ending to avoid a loop.")
      print(key)
      return
    if "/" in key:
      savepath = os.path.dirname(key) + "/transcribed_files/"
    else:
      savepath = os.path.dirname(key) + "transcribed_files/"

    file_uri = 's3://' + bucket + '/' + key
    output_name = savepath + file_name + "-transcribed.json"
    job_name = file_name + "-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=5))


    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name, # this was causing some errors sinc it was not following the regex ^[0-9a-zA-Z._-]+
        Media={'MediaFileUri': file_uri},
        IdentifyLanguage=True,
        OutputBucketName=os.environ["TRANSCRIPTION_BUCKET"],
        OutputKey=output_name,# this was causing some errors sinc it was not following the regex [a-zA-Z0-9-_.!*'()/]{1,1024}$
        Settings={
  'ShowSpeakerLabels': True,
  'MaxSpeakerLabels': 10
        },
        ContentRedaction={
            'RedactionType': 'PII',
            'RedactionOutput': 'redacted_and_unredacted'
        }
    )

    print(bucket)
    print(key)
    print(file_uri)
    print(job_name)
    return {
        'statusCode': 200,
        'body': json.dumps('Audio File Found.  Submitted for transcription.')
    }