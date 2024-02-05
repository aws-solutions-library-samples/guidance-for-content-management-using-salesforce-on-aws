import os
import os.path as path

from aws_cdk import (
    aws_s3 as s3,
    aws_kms as kms,
    aws_iam as iam,
    aws_sns as sns, aws_lambda as lambda_,
    Duration,
    aws_sns_subscriptions as subscriptions,
)
from constructs import Construct


class MediaManagementVideoRekognitionStack(Construct):
    def __init__ (self, scope: Construct, construct_id: str, defaultnaming: str, video_input_topic: sns.ITopic,
                  output_bucket: s3.IBucket, input_bucket: s3.IBucket, master_key: kms.Key,video_suffix:list,
                  **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.defaultnaming = defaultnaming
        self.video_input_topic = video_input_topic
        self.output_bucket = output_bucket
        self.input_bucket = input_bucket
        self.master_key = master_key
        self.video_suffix = video_suffix
        self.video_rek_complete_topic = sns.Topic(self, "VidRekJobCompleteTopic",
                                             display_name="AmazonRekognitionCompleteTopic_{}".format(
                                                 self.defaultnaming),
                                             master_key=self.master_key,
                                             topic_name="AmazonRekognitionCompleteTopic_{}".format(
                                                 self.defaultnaming))
        rekognition_sns_role = iam.Role(self, "SNSRekogRole",
                                        assumed_by=iam.ServicePrincipal("rekognition.amazonaws.com"))
        self.video_rek_complete_topic.grant_publish(rekognition_sns_role)
        self.master_key.grant_encrypt_decrypt(rekognition_sns_role)
        self.lambda_function_video_rekognition_complete = lambda_.Function(self,
                                                                      id='video_rekognition_complete_function',
                                                                      function_name='complete-video-rekognition-{}'.format(
                                                                          self.defaultnaming),
                                                                      code=lambda_.Code.from_asset(
                                                                          path.join(os.getcwd(),
                                                                                    "media_management_solutions_library",
                                                                                    "lambda_assets",
                                                                                    "video_rekognition_complete_function"))
                                                                      ,
                                                                      environment={
                                                                          "OUTPUT_BUCKET": self.output_bucket.bucket_name},
                                                                      memory_size=1024,
                                                                      timeout=Duration.seconds(300)
                                                                      , handler="index.lambda_handler",
                                                                      runtime=lambda_.Runtime.PYTHON_3_11)
        self.lambda_function_video_rekognition = lambda_.Function(self, id='video_rekognition_function',
                                                             function_name='start-video-rekognition-{}'.format(
                                                                 self.defaultnaming),
                                                             code=lambda_.Code.from_asset(
                                                                 path.join(os.getcwd(),
                                                                           "media_management_solutions_library",
                                                                           "lambda_assets",
                                                                           "video_rekognition_function"))
                                                             ,
                                                             environment={
                                                                 "VidRekJobCompleteArn": self.video_rek_complete_topic.topic_arn,
                                                                 "RekognitionToSNSRole": rekognition_sns_role.role_arn},
                                                             memory_size=1024,
                                                             timeout=Duration.seconds(300),
                                                             handler="index.lambda_handler",
                                                             runtime=lambda_.Runtime.PYTHON_3_11)
        self.lambda_function_video_rekognition.add_to_role_policy(
            statement=iam.PolicyStatement(actions=["rekognition:StartLabelDetection", "rekognition:DetectLabels"],
                                          resources=["*"]))
        self.lambda_function_video_rekognition_complete.add_to_role_policy(
            statement=iam.PolicyStatement(actions=["rekognition:GetLabelDetection"], resources=["*"]))
        rekognition_sns_role.grant_pass_role(self.lambda_function_video_rekognition)
        self.output_bucket.grant_put(self.lambda_function_video_rekognition_complete)
        for j in self.video_suffix:
            self.input_bucket.grant_read(self.lambda_function_video_rekognition, objects_key_pattern=f"*.{j}")
            self.input_bucket.grant_read(self.lambda_function_video_rekognition, objects_key_pattern=f"*.{j.upper()}")
        self.video_input_topic.add_subscription(subscriptions.LambdaSubscription(self.lambda_function_video_rekognition))
        self.video_rek_complete_topic.add_subscription(
            subscriptions.LambdaSubscription(self.lambda_function_video_rekognition_complete))
