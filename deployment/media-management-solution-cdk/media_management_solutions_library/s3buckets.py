from aws_cdk import (
    aws_s3 as s3,
    aws_kms as kms,
    aws_iam as iam
)
from constructs import Construct


class MediaManagementS3BucketsStack(Construct):
    # create a logging bucket and any bucket created loggs to that bucket.
    def __init__ (self, scope: Construct, construct_id: str, id, logging_bucket_name, input_bucket_name,
                  output_bucket_name, cors_allowed_origin: str = "https://*.force.com", encryption_key: kms.IKey = None,
                  **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.id = id
        self.logging_bucket_name = logging_bucket_name
        self.input_bucket_name = input_bucket_name
        self.output_bucket_name = output_bucket_name
        self.encryption_key = encryption_key
        self.cors_allowed_origin = cors_allowed_origin

        if encryption_key is None:
            self.encryption = s3.BucketEncryption.S3_MANAGED
        else:
            self.encryption = s3.BucketEncryption.KMS
        self.cors_rule = s3.CorsRule(id=self.id + 'CORSRule',
                                     allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST,
                                                      s3.HttpMethods.DELETE],
                                     allowed_origins=[self.cors_allowed_origin],
                                     allowed_headers=["*"],
                                     exposed_headers=["ETag"])
        self.access_logs_bucket = s3.Bucket(self,
                                            id=self.id + 'LogsBucket',
                                            versioned=True,
                                            bucket_name=self.logging_bucket_name,
                                            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                            enforce_ssl=True,
                                            encryption=self.encryption,
                                            encryption_key=self.encryption_key
                                            )
        self.input_bucket = s3.Bucket(self,
                                      id=self.id + 'InputBucket',
                                      versioned=True,
                                      bucket_name=self.input_bucket_name,
                                      block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                      server_access_logs_bucket=self.access_logs_bucket,
                                      server_access_logs_prefix=self.input_bucket_name + "/",
                                      cors=[self.cors_rule],
                                      enforce_ssl=True,
                                      encryption=self.encryption,
                                      encryption_key=self.encryption_key)
        self.input_bucket.add_to_resource_policy(iam.PolicyStatement(effect=iam.Effect.DENY, actions=["s3:put*"],
                                                                     resources=[f'{self.input_bucket.bucket_arn}/* *'],
                                                                     principals=[iam.AnyPrincipal()]))
        self.input_bucket.add_to_resource_policy(iam.PolicyStatement(effect=iam.Effect.DENY, actions=["s3:put*"],
                                                                     resources=[f'{self.input_bucket.bucket_arn}/*+*'],
                                                                     principals=[iam.AnyPrincipal()]))
        self.output_bucket = s3.Bucket(self,
                                       id=self.id + 'OutputBucket',
                                       versioned=True,
                                       cors=[self.cors_rule],
                                       bucket_name=self.output_bucket_name,
                                       block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                       server_access_logs_bucket=self.access_logs_bucket,
                                       server_access_logs_prefix=self.output_bucket_name + "/",
                                       enforce_ssl=True,
                                       encryption=self.encryption,
                                       encryption_key=self.encryption_key)

    # Create s3 Bucket with pre-configured logging and security
    def create_s3_bucket_stack (self, id, bucket_name: str, log_file_prefix: str, cors_rules: s3.CorsRule = None,
                                **kwargs) -> s3.Bucket:

        bucket = s3.Bucket(self,
                           id=id,
                           versioned=True,
                           bucket_name=bucket_name,
                           block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                           server_access_logs_bucket=self.access_logs_bucket,
                           server_access_logs_prefix=log_file_prefix,
                           enforce_ssl=True,
                           encryption=self.encryption,
                           encryption_key=self.encryption_key,
                           cors=[cors_rules])
        # if cors_rules is not None:
        #     bucket.add_cors_rule(cors_rules)
        # return bucket
        #
        # bucket = s3.Bucket(self,
        #                    id=id,
        #                    versioned=True,
        #                    bucket_name=bucket_name,
        #                    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        #                    server_access_logs_bucket=self.access_logs_bucket,
        #                    server_access_logs_prefix=log_file_prefix,
        #                    enforce_ssl=True,
        #                    encryption=self.encryption,
        #                    encryption_key=self.encryption_key)
        # iam.Policy(iam.PolicyStatement(effect=iam.Effect.DENY,actions=["s3:put*"], resources=[f'{bucket.bucket_arn}/* *']))
        # iam.Policy(iam.PolicyStatement(effect=iam.Effect.DENY,actions=["s3:put*"], resources=[f'{bucket.bucket_arn}/*+*']))

        return bucket
