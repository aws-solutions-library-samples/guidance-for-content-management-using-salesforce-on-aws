FROM public.ecr.aws/lambda/python:3.9
ENV MPLCONFIGDIR=/tmp
# Copy function code
run echo -e '\n\
import os\n\
import boto3\n\
import json\n\
\n\
def handler(event, context):\n\
\n\
    print(event)\n\
    if "Sns" in event["Records"][0]:\n\
      event = event["Records"][0]["Sns"]["Message"]\n\
      print("SNS Message")\n\
      print(event)\n\
      if "Records" not in event:\n\
        print("Test message.  Halting processing")\n\
        return\n\
\n\
    event=json.loads(event)\n\
    key = (event["Records"][0]["s3"]["object"]["key"])\n\
    ifile = "/tmp/" + os.path.basename(key)\n\
    bucket = (event["Records"][0]["s3"]["bucket"]["name"])\n\
\n\
    ofile = ifile + ".docx"\n\
\n\
    s3 = boto3.client('"'"'s3'"'"')\n\
    s3.download_file(bucket, key, ifile)\n\
\n\
    cmdtorun = "( cd /tmp ; python3 " + os.environ["LAMBDA_TASK_ROOT"] + "/ts-to-word.py --inputFile " + ifile + ")"\n\
\n\
    print(cmdtorun)\n\
    os.system(cmdtorun)\n\
\n\
    savepath = os.path.dirname(key)\n\
    objname = os.path.basename(ifile)\n\
    savefile = objname.replace("-transcribed.json","") + ".docx"\n\
    print("savefile is " + savefile)\n\
    if "/" in key:\n\
      savefile = os.path.dirname(key) + "/" + savefile\n\
\n\
    with open(ofile, "rb") as f:\n\
        s3.upload_fileobj(f, os.environ["OUTPUT_BUCKET"], savefile)\n\
\n\
    return\n' >> json2word.py

run echo -e '\n\
scipy\n\
matplotlib\n\
python-docx\n' >> requirements.txt

RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
RUN curl -o ${LAMBDA_TASK_ROOT}/ts-to-word.py https://raw.githubusercontent.com/aws-samples/amazon-transcribe-output-word-document/main/python/ts-to-word.py

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "json2word.handler" ]