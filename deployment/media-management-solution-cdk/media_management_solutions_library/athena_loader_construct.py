import os
from os import path

from aws_cdk import (
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_athena as athena,
    Aws,
    Duration,
    aws_sns_subscriptions as subscriptions,
    aws_sns as sns,
)
from constructs import Construct

from media_management_solutions_library.s3buckets import MediaManagementS3BucketsStack


class AthenaStack(Construct):
    # create a logging bucket and any bucket created loggs to that bucket.
    def __init__ (self, scope: Construct, construct_id: str, stack_id: str,
                  s3_bucket_stack: MediaManagementS3BucketsStack,
                  transcription_bucket: s3.IBucket, transcription_topic: sns.ITopic, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.construct_id = construct_id
        self.stack_id = stack_id
        account_id = Aws.ACCOUNT_ID
        construct_name = self.stack_id.replace("-", "").replace("_", "").lower()
        defaultnameing = [construct_name[0:30], account_id]
        results_bucket_name = "{}-results-{}".format(defaultnameing[0], defaultnameing[1])
        athena_output_redacted_bucket_name = "{}-athena-output-redacted-{}".format(defaultnameing[0][:20],
                                                                                   defaultnameing[1])
        athena_output_bucket_name = "{}-athena-output-{}".format(defaultnameing[0][:20], defaultnameing[1])
        athena_database_name = "database_{}".format(defaultnameing[0])
        athena_table_name = "transcribe_output"
        athena_redacted_database_name = "database_redacted{}".format(defaultnameing[0])
        athena_wg_name = 'media_management_wg'

        athena_query_results_bucket = s3_bucket_stack.create_s3_bucket_stack(id="athena_query_results_s3_bucket",
                                                                             bucket_name=results_bucket_name,
                                                                             log_file_prefix=results_bucket_name + "/")
        athena_output_bucket = s3_bucket_stack.create_s3_bucket_stack(id="athena_output_s3_bucket",
                                                                      bucket_name=athena_output_bucket_name,
                                                                      log_file_prefix=athena_output_bucket_name + "/")
        athena_output_redacted_bucket = s3_bucket_stack.create_s3_bucket_stack(id="athena_output_redacted_s3_bucket",
                                                                               bucket_name=athena_output_redacted_bucket_name,
                                                                               log_file_prefix=athena_output_redacted_bucket_name + "/")

        # Athena
        athena_wg = athena.CfnWorkGroup(self, "appflow_workgroup",
                                        name=athena_wg_name,
                                        description='Workgroup for Athena queries',
                                        work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                                            result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                                                output_location=f's3://{athena_query_results_bucket.bucket_name}/results/',
                                                encryption_configuration=athena.CfnWorkGroup.EncryptionConfigurationProperty(
                                                    encryption_option='SSE_S3'
                                                ),
                                            )
                                        )
                                        )

        lambda_function_athena_loader = lambda_.Function(self, id='athena_loader_function',
                                                         function_name='athena-transcription-loader-{}'.format(
                                                             defaultnameing[0]),
                                                         code=lambda_.Code.from_asset(path.join(os.getcwd(),
                                                                                                "media_management_solutions_library",
                                                                                                "lambda_assets",
                                                                                                "athena_loader_function"))
                                                         ,
                                                         environment={
                                                             "DATABASE": athena_database_name,
                                                             "DATABASEREDACTED": athena_redacted_database_name,
                                                             "PROCSDBUCKET": athena_output_bucket.bucket_name,
                                                             "REDACTEDBUCKET": athena_output_redacted_bucket.bucket_name,
                                                             "TABLENAME": athena_table_name,
                                                             "WORKGROUP": athena_wg.name
                                                         },

                                                         memory_size=1024, timeout=Duration.seconds(900)
                                                         , handler="index.lambda_handler",
                                                         runtime=lambda_.Runtime.PYTHON_3_11)
        lambda_function_athena_loader.add_to_role_policy(
            statement=iam.PolicyStatement(actions=["athena:StartQueryExecution"], resources=["*"]))

        athena_output_redacted_bucket.grant_put(lambda_function_athena_loader)
        athena_output_bucket.grant_put(lambda_function_athena_loader)
        athena_query_results_bucket.grant_read(lambda_function_athena_loader)
        transcription_bucket.grant_read(lambda_function_athena_loader, objects_key_pattern="transcribed_files/*")
        transcription_topic.add_subscription(subscriptions.LambdaSubscription(lambda_function_athena_loader))

        # to deploy:
        # test=AthenaStack(self, "AthenaStack",stack_id=self.construct_id,s3_bucket_stack=s3_bucket_stack,transcription_bucket=transcription_bucket,transcription_topic=transcription_topic )
