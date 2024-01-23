FROM public.ecr.aws/lambda/python:3.9
ENV MPLCONFIGDIR=/tmp
# Copy function code
RUN curl -o ${LAMBDA_TASK_ROOT}/ffmpeg-release-amd64-static.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
RUN yum install tar xz -y
RUN tar -xf ffmpeg-release-amd64-static.tar.xz -C ${LAMBDA_TASK_ROOT} --strip-components=1

RUN echo -e 'import json\n\
import boto3\n\
import os\n\
def handler(event, context):\n\
  print(event)\n\
  if "Sns" in event["Records"][0]:\n\
    event = event["Records"][0]["Sns"]["Message"]\n\
    if "Records" not in event:\n\
      print("Test message.  Halting processing")\n\
      return\n\
\n\
    event=json.loads(event)\n\
    print(event)\n\
\n\
\n\
\n\
  BUCKET_NAME = event["Records"][0]["s3"]["bucket"]["name"]\n\
  print("S3 bucket: " + BUCKET_NAME)\n\
  KEY = event["Records"][0]["s3"]["object"]["key"]\n\
  jsonfile = os.path.basename(KEY)\n\
  print("Transcribe output file: " + jsonfile)\n\
\n\
  if jsonfile.startswith("redacted-") == False:\n\
    print("Not a redacted file.  Ending")\n\
    return\n\
\n\
  original_audio = jsonfile.removeprefix("redacted-")\n\
\n\
  original_audio = original_audio.removesuffix("-transcribed.json")\n\
  print("Original audio file: " +  original_audio)\n\
\n\
\n\
  original_media_folder = os.path.dirname(os.path.dirname(KEY))\n\
  print("Original media folder is " + original_media_folder)\n\
  if len(original_media_folder) > 0:\n\
    print("original media folder length greater than zero; adding slash")\n\
    original_media_folder = original_media_folder + "/"\n\
  else: original_media_folder = ""\n\
  print("Bucket Root")\n\
\n\
\n\
  s3 = boto3.resource('"'"'s3'"'"')\n\
\n\
  inputBucket = os.environ["INPUT_BUCKET"]\n\
  print("Downloading " + original_audio + " from " + inputBucket)\n\
  s3.Bucket(inputBucket).download_file(original_media_folder + original_audio, "/tmp/" + original_audio)\n\
  print("Downloading " + KEY)\n\
  s3.Bucket(BUCKET_NAME).download_file(KEY, "/tmp/" + jsonfile)\n\
  print("dir contents ")\n\
  print(os.system("ls -l /tmp"))\n\
  f = open("/tmp/" + jsonfile)\n\
  transcript = json.load(f)\n\
  items = transcript['"'"'results'"'"']['"'"'items'"'"']\n\
  command_str_p1 = os.environ["LAMBDA_TASK_ROOT"] + "/ffmpeg -i "\n\
  redact_times = ""\n\
  for item in items:\n\
    if item['"'"'alternatives'"'"'][0]['"'"'content'"'"'] == '"'"'[PII]'"'"':\n\
      s = '"'"'volume=enable=\\'"'"'between(t,'"'"' + item['"'"'start_time'"'"'] + '"'"','"'"' + item['"'"'end_time'"'"'] + '"'"')\\'"'"':volume=0'"'"' + ", "\n\
      redact_times += s\n\
  redact_times = "\"" + redact_times[:-2] + "\""\n\
  os_command = command_str_p1 + "/tmp/" + original_audio + " -af " + redact_times + " /tmp/redacted-" + original_audio\n\
  print("Command Line: " + os_command)\n\
  os.system(os_command)\n\
\n\
\n\
  savefile = original_media_folder + "audio_redacted-" + original_audio\n\
  s3_client = boto3.client('"'"'s3'"'"')\n\
  s3_client.upload_file("/tmp/redacted-" + original_audio, os.environ["OUTPUT_BUCKET"], savefile)\n\
\n\
  # Clean up container temp directory\n\
  print("Temp dir contents")\n\
  print(os.system('"'"'ls -l /tmp'"'"'))\n\
  print("Deleting temp files...")\n\
  os_command = "rm /tmp/" + original_audio + "; rm /tmp/" + jsonfile + "; rm /tmp/redacted-" + original_audio\n\
  # os.system('"'"'rm -rf /tmp/..?* /tmp/.[!.]* /tmp/*'"'"')\n\
  os.system(os_command)\n\
  print("Temp dir contents")\n\
  print(os.system('"'"'ls -l /tmp'"'"'))\n'>> audio_reencoder.py

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "audio_reencoder.handler" ]