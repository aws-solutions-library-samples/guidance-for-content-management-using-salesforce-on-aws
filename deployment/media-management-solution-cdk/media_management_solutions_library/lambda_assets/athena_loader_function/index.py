import os
import csv
import boto3
import json, datetime

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')


def parse_transcribe_ouput (Transcribe_jsondata):
    i = 1
    print("Beginning json processing.")
    rawjsondata = Transcribe_jsondata
    data_for_athena = {"time": [], "speaker_tag": [], "comment": []}
    # Identifying speaker populating speakers into an array
    if "speaker_labels" in rawjsondata["results"].keys():
        # processing segment for building array for speaker and time duration for building csv file
        for segment in rawjsondata["results"]["speaker_labels"]["segments"]:
            # if items
            if len(segment["items"]) > 0:
                # print("Processing line " + str(i))

                if i % 20 == 0:
                    print("Processing line " + str(i) + ".")
                i += 1
                data_for_athena["time"].append(time_conversion(segment["start_time"]))
                # timesm = time_conversion(segment["start_time"])
                data_for_athena["speaker_tag"].append(segment["speaker_label"])
                data_for_athena["comment"].append("")
                # looping thru each word
                for word in segment["items"]:
                    pronunciations = list(
                        filter(
                            lambda x: x["type"] == "pronunciation",
                            rawjsondata["results"]["items"],
                        )
                    )
                    word_result = list(
                        filter(
                            lambda x: x["start_time"] == word["start_time"]
                                      and x["end_time"] == word["end_time"],
                            pronunciations,
                        )
                    )
                    if word_result[-1]["alternatives"][0]["content"] == "[PII]":
                        result = word_result[-1]["alternatives"][0]
                    else:
                        result = sorted(
                            word_result[-1]["alternatives"], key=lambda x: x["confidence"]
                        )[-1]
                    # for the word!
                    data_for_athena["comment"][-1] += " " + result["content"]
                    # Check for punctuation !!!!
                    try:
                        word_result_index = rawjsondata["results"]["items"].index(
                            word_result[0]
                        )
                        next_item = rawjsondata["results"]["items"][word_result_index + 1]
                        if next_item["type"] == "punctuation":
                            data_for_athena["comment"][-1] += next_item["alternatives"][0][
                                "content"
                            ]
                    except IndexError:
                        pass
                        # Invalid File exiting!
    else:
        print("Need to have speaker identification, Please check the file USE WAV format Audio file for better results")
        return
    return data_for_athena


def time_conversion (timeX):
    times = datetime.timedelta(seconds=float(timeX))
    times = times - datetime.timedelta(microseconds=times.microseconds)
    return str(times)


def lambda_handler (event, context):
    print(event)
    if "Sns" in event["Records"][0]:
        event = event["Records"][0]["Sns"]["Message"]
        if "Records" not in event:
            print("Test message.  Halting processing")
            return

        event = json.loads(event)
        print(event)

        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = event["Records"][0]["s3"]["object"]["key"]
        file_name = os.path.basename(key)
        prefix = os.path.dirname(key)
        audio_file = file_name.replace('-transcribed.json', '')

        print("Processing searchable text for " + file_name)
        output_file = ("/tmp/" + audio_file + ".csv")
        output_key = key.replace('-transcribed.json', '') + ".csv"
        print("event: {}".format(event))

        outputBUCKET = os.environ['PROCSDBUCKET']

        if file_name.startswith('redacted-'):
            outputBUCKET = os.environ['REDACTEDBUCKET']

        print("Output bucket is " + outputBUCKET)

        audio_transcribed_json = key
        text = s3.get_object(Bucket=bucket, Key=audio_transcribed_json)['Body']
        s3objectdata = text.read().decode()
        transcribe_json_data = json.loads(s3objectdata)

        print("Starting Parsing Transcription JSON and reformatting")
        csv_elements = parse_transcribe_ouput(transcribe_json_data)
        sentence = []
        speaker_tag = []
        timedur = []

        sentence = csv_elements["comment"]
        speaker_tag = csv_elements["speaker_tag"]
        timedur = csv_elements["time"]

        csv_data = open(output_file, "w")
        writer = csv.writer(csv_data, delimiter='|')

        print("Writing to output file.")

        for item, elem in enumerate(sentence):
            writer.writerow([audio_file] + [timedur[item]] + [speaker_tag[item]] + [elem.replace("'", "'").lstrip()])

        csv_data.close()

        with open(output_file, "rb") as f:
            s3.upload_fileobj(f, outputBUCKET, output_key)

        if file_name.startswith('redacted-'):
            DB = os.environ['DATABASEREDACTED']

        else:
            DB = os.environ['DATABASE']

        DB = DB.replace("-", "_")
        print("The database is " + DB)
        AthenResultsOutput = 's3://' + outputBUCKET + '/AthenaResults/'
        TABLENAME = os.environ['TABLENAME']

        WORKGROUP = os.environ['WORKGROUP']

        athena_client = boto3.client('athena')

        response = athena_client.start_query_execution(
            QueryString="CREATE DATABASE IF NOT EXISTS " + DB,
            ResultConfiguration={'OutputLocation': AthenResultsOutput},
            WorkGroup=WORKGROUP
        )

        print("Creating Database...")
        print(response)

        response = athena_client.start_query_execution(
            QueryString="CREATE EXTERNAL TABLE IF NOT EXISTS " + DB + "." + TABLENAME + " (file string, start_time string, speaker string, text string) ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe' WITH SERDEPROPERTIES ('serialization.format' = ',','field.delim' = '|') LOCATION 's3://" + outputBUCKET + "/" + "' TBLPROPERTIES ('has_encrypted_data'='false'); ",
            ResultConfiguration={'OutputLocation': AthenResultsOutput},
            WorkGroup=WORKGROUP
        )

        print("Creating Table...")
        print(response)

        return