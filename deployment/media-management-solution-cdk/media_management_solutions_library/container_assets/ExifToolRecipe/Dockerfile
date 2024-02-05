FROM public.ecr.aws/lambda/python:3.9
ENV MPLCONFIGDIR=/tmp
# Copy function code
run echo -e '\n\
import os\n\
import boto3\n\
import json\n\
import hashlib\n\
\n\
def handler(event, context):\n\
\n\
    print(event)\n\
    if "Sns" in event["Records"][0]:\n\
      event = event["Records"][0]["Sns"]["Message"]\n\
      print("SNS Message")\n\
      print(event)\n\
      event=json.loads(event)\n\
      if "Records" not in event:\n\
        print("Test message.  Halting processing")\n\
        return\n\
\n\
    key = (event["Records"][0]["s3"]["object"]["key"])\n\
    if "audio_redacted" in key:\n\
      print("This is a redacted copy.  Halting")\n\
      return\n\
    ifile = "/tmp/" + os.path.basename(key)\n\
    bucket = (event["Records"][0]["s3"]["bucket"]["name"])\n\
    outputBucket = os.environ["OUTPUT_BUCKET"]\n\
\n\
    ofile = ifile + ".json"\n\
\n\
    s3 = boto3.client('"'"'s3'"'"')\n\
    s3.download_file(bucket, key, ifile)\n\
\n\
    with open(ifile, "rb") as f:\n\
      file_hash = hashlib.md5(f.read())\n\
\n\
    print("The md5 hash of " + ifile + " is " + file_hash.hexdigest())\n\
\n\
    cmdtorun = "( cd /tmp ; /var/task/exiftool-12.45/exiftool " + ifile + " -json > " + ofile + ")"\n\
\n\
    print(cmdtorun)\n\
    os.system(cmdtorun)\n\
\n\
    savepath = os.path.dirname(key) + "image_metadata/"\n\
    if "/" in key:\n\
      savepath = os.path.dirname(key) + "/image_metadata/"\n\
    savefile = savepath + os.path.basename(ifile) + ".json"\n\
    print("savefile is " + savefile)\n\
\n\
    with open(ofile, "rb") as f:\n\
      print(f.read())\n\
    s3.upload_file(ofile, outputBucket, savefile)\n\
\n\
    return\n' >> exifextract.py

RUN yum install -y tar gzip gunzip perl
RUN curl -o ${LAMBDA_TASK_ROOT}/exif.tar.gz https://codeload.github.com/exiftool/exiftool/tar.gz/refs/tags/12.45
RUN tar -xvf ${LAMBDA_TASK_ROOT}/exif.tar.gz
# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "exifextract.handler" ]