import os
import os.path as path

from aws_cdk import (
    Stack,
    CfnOutput,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_s3_notifications as s3n,
    aws_s3 as s3,
    Aws, aws_iam as iam, aws_lambda as lambda_,
    Duration)
from constructs import Construct
from media_management_solutions_library.containers import ContainerRecipeStack
from media_management_solutions_library.kendra import MediaManagementKendraStack
from media_management_solutions_library.kms_key import KmsStack
from media_management_solutions_library.s3buckets import MediaManagementS3BucketsStack
from media_management_solutions_library.auth import MediaManagementAuthStack


def s3_notification_destination_filter (notification_bucket: s3.IBucket, sns_topic: sns.ITopic, suffix_list: list):
    """
    S3 bucket notification destination filter
    :param notification_bucket: s3 bucket that will publish notification
    :param sns_topic: sns topic
    :param suffix_list: list of suffix to acted from the s3 bucket object key.  e.g. ['.mp4', '.mov', '.avi']
    :return: None
    """
    for i in suffix_list:
        notification_bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                                   s3n.SnsDestination(sns_topic),
                                                   s3.NotificationKeyFilter(suffix=i))


class MediaManagementSolutionsLibraryStack(Stack):
    def __init__ (self, scope: Construct, construct_id: str, enable_s3_kms_encryption: bool = False,
                  deploy_kendra: bool = False, kendra_index_edition='DEVELOPER_EDITION', **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Default names for resources
        self.construct_id = construct_id
        self.enable_s3_kms_encryption = enable_s3_kms_encryption
        self.deploy_kendra = deploy_kendra
        self.kendra_index_edition = kendra_index_edition

        account_id = Aws.ACCOUNT_ID
        construct_name = self.construct_id.replace("-", "").replace("_", "").lower()
        defaultnameing = [construct_name[0:30], account_id]
        # Default names for S3
        input_bucket_name = "{}-input-{}".format(defaultnameing[0], defaultnameing[1])
        output_bucket_name = "{}-output-{}".format(defaultnameing[0], defaultnameing[1])
        transcription_bucket_name = "{}-transcription-{}".format(defaultnameing[0], defaultnameing[1])
        logging_bucket_name = "{}-logging-{}".format(defaultnameing[0], defaultnameing[1])

        ################
        # Master KMS Key#
        ################
        kms_key = KmsStack(self, "KmsStack")
        master_key = kms_key.master_key_create(id="media-management-master-key")

        if self.enable_s3_kms_encryption:
            s3_master_key = master_key
        else:
            s3_master_key = None
        ###########################
        # Create Container Recipe #
        ###########################
        container_stack = ContainerRecipeStack(self, "ContainerStack")
        with open(path.join(os.getcwd(), "media_management_solutions_library", "container_assets", "ExifToolRecipe",
                            "Dockerfile"), "r") as f:
            dockerfile_template_data = f.read()
        exif_tool_image = container_stack.container_image_create(
            ecr_repo_name='exif_tool_repo_{}'.format(defaultnameing[0]),
            dockerfile_template_data=dockerfile_template_data,
            container_recipe_name='exif_tool_recipe_{}'.format(defaultnameing[0]))
        with open(path.join(os.getcwd(), "media_management_solutions_library", "container_assets", "EncoderRecipe",
                            "Dockerfile"), "r") as f:
            dockerfile_template_data = f.read()
        encoder_image = container_stack.container_image_create(
            ecr_repo_name='encoder_repo_{}'.format(defaultnameing[0]),
            dockerfile_template_data=dockerfile_template_data,
            container_recipe_name='encoder_recipe_{}'.format(defaultnameing[0]))
        with open(path.join(os.getcwd(), "media_management_solutions_library", "container_assets", "json2wordrecipe",
                            "Dockerfile"), "r") as f:
            dockerfile_template_data = f.read()
        json2word_image = container_stack.container_image_create(
            ecr_repo_name='json2word_repo_{}'.format(defaultnameing[0]),
            dockerfile_template_data=dockerfile_template_data,
            container_recipe_name='json2word_recipe_{}'.format(defaultnameing[0]))
        ##############
        # SNS Topics #
        ##############
        image_input_topic = sns.Topic(self, "ImageTopic",
                                      display_name="ImageTopic_{}".format(defaultnameing[0]),
                                      master_key=master_key,
                                      topic_name="ImageTopic_{}".format(defaultnameing[0]))
        video_input_topic = sns.Topic(self, "VideoTopic",
                                      display_name="VideoTopic_{}".format(defaultnameing[0]),
                                      master_key=master_key,
                                      topic_name="VideoTopic_{}".format(defaultnameing[0]))
        audio_input_topic = sns.Topic(self, "AudioTopic",
                                      display_name="AudioTopic_{}".format(defaultnameing[0]),
                                      master_key=master_key,
                                      topic_name="AudioTopic_{}".format(defaultnameing[0]))

        video_rek_job_complete_topic = sns.Topic(self, "VidRekJobCompleteTopic",
                                                 display_name="VidRekJobCompleteTopic_{}".format(defaultnameing[0]),
                                                 master_key=master_key,
                                                 topic_name="AmazonRekognitionVidJobCompleteTopic_{}".format(
                                                     defaultnameing[0]))
        transcription_topic = sns.Topic(self, "TranscriptionTopic",
                                        display_name="TranscriptionTopic_{}".format(defaultnameing[0]),
                                        master_key=master_key,
                                        topic_name="TranscriptionTopic_{}".format(defaultnameing[0]))

        #########################
        # IAM Policy for sns to publish to Rekognition
        #########################
        rekognition_sns_policy = iam.Policy(self, "rekognition-sns-policy",
                                            statements=[
                                                iam.PolicyStatement(
                                                    effect=iam.Effect.ALLOW,
                                                    actions=["sns:Publish"],
                                                    resources=[video_rek_job_complete_topic.topic_arn])])
        rekognition_sns_role = iam.Role(self, "RekognitionSNSRole",
                                        assumed_by=iam.ServicePrincipal("rekognition.amazonaws.com"))
        rekognition_sns_role.attach_inline_policy(rekognition_sns_policy)
        #####################
        # Create S3 buckets #
        #####################
        # the MediaManagementS3BucketsStack class is used to create S3 buckets.
        # it is preconfigured to create a dedicated logging bucket that all buckets will write to, and enforce ssl and block public access.

        s3_bucket_stack = MediaManagementS3BucketsStack(self, "MediaManagementS3",
                                                        id="MediaManagementS3",
                                                        logging_bucket_name=logging_bucket_name,
                                                        input_bucket_name=input_bucket_name,
                                                        output_bucket_name=output_bucket_name,
                                                        encryption_key=s3_master_key)
        logging_bucket = s3_bucket_stack.access_logs_bucket

        input_bucket = s3_bucket_stack.input_bucket

        output_bucket = s3_bucket_stack.output_bucket

        transcription_bucket = s3_bucket_stack.create_s3_bucket_stack(id="transcritpion_s3_bucket",
                                                                      bucket_name=transcription_bucket_name,
                                                                      log_file_prefix=transcription_bucket_name + "/")

        ###########################
        # S3 bucket notifications #
        ###########################
        # suffix variables are used to filter S3 bucket notifications by media type.
        # These sames variables are used in defining iam permissions based on media type.
        image_suffix = ["jpg", "jpeg", "png"]  # supported formats by Rekognition
        video_suffix = ['mpeg4', 'mp4', 'mov']  # supported formats by Rekognition
        audio_suffix = ["mp3", "wav", "aac", "flac"]  # add support for m4a for apple memo files?
        transcription_suffix = ["-transcribed.json"]

        s3_notification_destination_filter(input_bucket, image_input_topic, image_suffix)
        s3_notification_destination_filter(input_bucket, video_input_topic, video_suffix)
        s3_notification_destination_filter(input_bucket, audio_input_topic, audio_suffix)
        s3_notification_destination_filter(transcription_bucket, transcription_topic, transcription_suffix)

        ##########
        # lambda #
        ##########
        lambda_function_exif_tool = lambda_.Function(self,
                                                     id='ExifTool',
                                                     function_name='exif-metadata-{}'.format(defaultnameing[0]),
                                                     code=lambda_.Code.from_ecr_image(
                                                         repository=exif_tool_image['repo'],
                                                         tag_or_digest="1.0.0-1"),
                                                     environment={"OUTPUT_BUCKET": output_bucket.bucket_name},
                                                     memory_size=1024,
                                                     timeout=Duration.seconds(300),
                                                     handler=lambda_.Handler.FROM_IMAGE,
                                                     runtime=lambda_.Runtime.FROM_IMAGE)
        lambda_function_exif_tool.node.add_dependency(exif_tool_image['image'])
        lambda_function_encoder = lambda_.Function(self, id='encoder',
                                                   function_name='encoder-{}'.format(defaultnameing[0]),
                                                   code=lambda_.Code.from_ecr_image(
                                                       repository=encoder_image['repo'],
                                                       tag_or_digest="1.0.0-1"),
                                                   environment={"OUTPUT_BUCKET": output_bucket.bucket_name,
                                                                "INPUT_BUCKET": input_bucket.bucket_name},
                                                   memory_size=1024,
                                                   timeout=Duration.seconds(900),
                                                   handler=lambda_.Handler.FROM_IMAGE,
                                                   runtime=lambda_.Runtime.FROM_IMAGE)
        lambda_function_encoder.node.add_dependency(encoder_image['image'])
        lambda_function_json2word = lambda_.Function(self, id='json2word',
                                                     function_name='json2word-{}'.format(defaultnameing[0]),
                                                     code=lambda_.Code.from_ecr_image(
                                                         repository=json2word_image['repo'],
                                                         tag_or_digest="1.0.0-1"),
                                                     environment={"OUTPUT_BUCKET": output_bucket.bucket_name},
                                                     memory_size=1024,
                                                     timeout=Duration.seconds(900),
                                                     handler=lambda_.Handler.FROM_IMAGE,
                                                     runtime=lambda_.Runtime.FROM_IMAGE)
        lambda_function_json2word.node.add_dependency(json2word_image['image'])
        lambda_function_image_rekognition = lambda_.Function(self, id='image_rekognition_function',
                                                             function_name='start-image-rekognition-{}'.format(
                                                                 defaultnameing[0]),
                                                             code=lambda_.Code.from_asset(
                                                                 path.join(os.getcwd(),
                                                                           "media_management_solutions_library",
                                                                           "lambda_assets",
                                                                           "image_rekognition_function"))
                                                             ,
                                                             environment={"OUTPUT_BUCKET": output_bucket.bucket_name},
                                                             memory_size=1024, timeout=Duration.seconds(300)
                                                             , handler="index.lambda_handler",
                                                             runtime=lambda_.Runtime.PYTHON_3_11)
        lambda_function_video_rekognition_complete = lambda_.Function(self, id='video_rekognition_complete_function',
                                                                      function_name='complete-video-rekognition-{}'.format(
                                                                          defaultnameing[0]),
                                                                      code=lambda_.Code.from_asset(
                                                                          path.join(os.getcwd(),
                                                                                    "media_management_solutions_library",
                                                                                    "lambda_assets",
                                                                                    "video_rekognition_complete_function"))
                                                                      ,
                                                                      environment={
                                                                          "OUTPUT_BUCKET": output_bucket.bucket_name},
                                                                      memory_size=1024, timeout=Duration.seconds(300)
                                                                      , handler="index.lambda_handler",
                                                                      runtime=lambda_.Runtime.PYTHON_3_11)
        lambda_function_video_rekognition = lambda_.Function(self, id='video_rekognition_function',
                                                             function_name='start-video-rekognition-{}'.format(
                                                                 defaultnameing[0]),
                                                             code=lambda_.Code.from_asset(
                                                                 path.join(os.getcwd(),
                                                                           "media_management_solutions_library",
                                                                           "lambda_assets",
                                                                           "video_rekognition_function"))
                                                             ,
                                                             environment={
                                                                 "VidRekJobCompleteArn": video_rek_job_complete_topic.topic_arn,
                                                                 "RekognitionToSNSRole": rekognition_sns_role.role_arn},
                                                             memory_size=1024,
                                                             timeout=Duration.seconds(300),
                                                             handler="index.lambda_handler",
                                                             runtime=lambda_.Runtime.PYTHON_3_11)
        lambda_function_transcription = lambda_.Function(self, id='transcription_function',
                                                         function_name='start-transcription-{}'.format(
                                                             defaultnameing[0]),
                                                         code=lambda_.Code.from_asset(
                                                             path.join(os.getcwd(),
                                                                       "media_management_solutions_library",
                                                                       "lambda_assets",
                                                                       "transcription_function"))
                                                         ,
                                                         environment={
                                                             "TRANSCRIPTION_BUCKET": transcription_bucket.bucket_name},
                                                         memory_size=1024,
                                                         timeout=Duration.seconds(300),
                                                         handler="index.lambda_handler",
                                                         runtime=lambda_.Runtime.PYTHON_3_11)

        ##############################
        # Lambda Permissions #
        ##############################
        lambda_function_image_rekognition.add_to_role_policy(
            statement=iam.PolicyStatement(actions=["rekognition:StartLabelDetection", "rekognition:DetectLabels"],
                                          resources=["*"]))
        lambda_function_video_rekognition.add_to_role_policy(
            statement=iam.PolicyStatement(actions=["rekognition:StartLabelDetection", "rekognition:DetectLabels"],
                                          resources=["*"]))
        lambda_function_video_rekognition_complete.add_to_role_policy(
            statement=iam.PolicyStatement(actions=["rekognition:GetLabelDetection"], resources=["*"]))
        rekognition_sns_role.grant_pass_role(lambda_function_video_rekognition)
        lambda_function_transcription.add_to_role_policy(
            statement=iam.PolicyStatement(actions=["transcribe:StartTranscriptionJob"], resources=["*"]))

        # Lambda S3 permissions #
        output_bucket.grant_put(lambda_function_image_rekognition)
        output_bucket.grant_put(lambda_function_exif_tool)
        output_bucket.grant_put(lambda_function_encoder)
        output_bucket.grant_put(lambda_function_json2word)
        output_bucket.grant_put(lambda_function_video_rekognition_complete)
        transcription_bucket.grant_put(lambda_function_transcription)
        transcription_bucket.grant_read(lambda_function_json2word)
        transcription_bucket.grant_read(lambda_function_encoder)

        # Granting Read on input bucket based on media type
        image_processing_lambda = [lambda_function_exif_tool, lambda_function_image_rekognition]
        video_processing_lambda = [lambda_function_video_rekognition, lambda_function_encoder,
                                   lambda_function_transcription]
        audio_processing_lambda = [lambda_function_encoder, lambda_function_transcription]

        for i in image_processing_lambda:
            for j in image_suffix:
                input_bucket.grant_read(i, objects_key_pattern=f"*.{j}")
                input_bucket.grant_read(i, objects_key_pattern=f"*.{j.upper()}")

        for i in video_processing_lambda:
            for j in video_suffix:
                input_bucket.grant_read(i, objects_key_pattern=f"*.{j}")
                input_bucket.grant_read(i, objects_key_pattern=f"*.{j.upper()}")

        for i in audio_processing_lambda:
            for j in audio_suffix:
                input_bucket.grant_read(i, objects_key_pattern=f"*.{j}")
                input_bucket.grant_read(i, objects_key_pattern=f"*.{j.upper()}")

        #############################
        # Lambda Topic Subscription #
        #############################
        image_input_topic.add_subscription(subscriptions.LambdaSubscription(lambda_function_exif_tool))
        image_input_topic.add_subscription(subscriptions.LambdaSubscription(lambda_function_image_rekognition))
        video_input_topic.add_subscription(subscriptions.LambdaSubscription(lambda_function_video_rekognition))
        video_input_topic.add_subscription(subscriptions.LambdaSubscription(lambda_function_encoder))
        video_input_topic.add_subscription(subscriptions.LambdaSubscription(lambda_function_transcription))
        video_rek_job_complete_topic.add_subscription(
            subscriptions.LambdaSubscription(lambda_function_video_rekognition_complete))
        audio_input_topic.add_subscription(subscriptions.LambdaSubscription(lambda_function_encoder))
        audio_input_topic.add_subscription(subscriptions.LambdaSubscription(lambda_function_transcription))
        transcription_topic.add_subscription(subscriptions.LambdaSubscription(lambda_function_json2word))
        transcription_topic.add_subscription(subscriptions.LambdaSubscription(lambda_function_encoder))

        ################
        # Kendra Stack #
        ################
        # This stack is deployed if the parameter deploy_kendra is set to True.
        if self.deploy_kendra:
            media_kendra_stack = MediaManagementKendraStack(self, "MediaKendraStack",
                                                            kendra_index_name="sfdc-media-management",
                                                            index_edition=self.kendra_index_edition)
            output_datasource=media_kendra_stack.create_kendra_datasource(data_source_name="OutputS3Bucket",s3_bucket=output_bucket)
            transcription_datasource=media_kendra_stack.create_kendra_datasource(data_source_name="TranscriptionS3Bucket",s3_bucket=transcription_bucket)

        else:
            pass

        ################
        #  Auth Stack  #
        ################
        auth_stack = MediaManagementAuthStack(self, "MediaManagementAuthStack",
                                              input_bucket=input_bucket,
                                              output_bucket=output_bucket,
                                              transcription_bucket=transcription_bucket)

        ###########
        # Outputs #
        ###########
        CfnOutput(self, "LoggingBucket", value=logging_bucket.bucket_name)
        CfnOutput(self, "InputBucket", value=input_bucket.bucket_name)
        CfnOutput(self, "OutputBucket", value=output_bucket.bucket_name)
        CfnOutput(self, "TranscriptionBucket", value=transcription_bucket.bucket_name)
        # CfnOutput(self, "MasterKeyID", value=master_key.key_id)
        # CfnOutput(self, "repository_uri", value=encoder_image.repository_uri)
