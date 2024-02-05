import os
import os.path as path

from aws_cdk import (
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_lambda as lambda_,
    CfnOutput,
    aws_s3 as s3
)
from constructs import Construct


class MediaManagementAuthStack(Construct):
    def __init__ (self, scope: Construct, id: str, input_bucket: s3.IBucket, output_bucket: s3.IBucket,
                  transcription_bucket: s3.IBucket, pub_cert: str):
        super().__init__(scope, id)

        codePath = path.join(os.getcwd(),
                             "media_management_solutions_library",
                             "auth_assets",
                             "get_creds_function")

        # install dependencies before packaging
        os.chdir(codePath)
        os.system("npm install")

        handler = lambda_.Function(self, "getCreds",
                                   runtime=lambda_.Runtime.NODEJS_18_X,
                                   code=lambda_.Code.from_asset(codePath),
                                   handler="get-creds.handler",
                                   environment=dict(
                                       CERT=pub_cert
                                   )
                                   )

        iam_role = iam.Role(self, "EndUserRole", assumed_by=iam.ArnPrincipal(handler.role.role_arn))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonKendraFullAccess"))
        input_bucket.grant_write(iam_role)
        output_bucket.grant_read(iam_role)
        transcription_bucket.grant_read(iam_role)

        #
        # iam_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, actions=["s3:*"], resources=[
        #     input_bucket.bucket_arn,
        #     input_bucket.bucket_arn + '/*',
        #     output_bucket.bucket_arn,
        #     output_bucket.bucket_arn + '/*',
        #     transcription_bucket.bucket_arn,
        #     transcription_bucket.bucket_arn + '/*'
        # ]))
        # iam_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, actions=["kms:*"], resources=["*"]))

        handler.add_environment('ROLE_ARN', iam_role.role_arn)

        api = apigateway.RestApi(self, "authCredsApi",
                                 rest_api_name="Media Management Auth API",
                                 description="This handles auth for Salesforce users",
                                 default_cors_preflight_options=apigateway.CorsOptions(
                                     allow_origins=apigateway.Cors.ALL_ORIGINS,
                                     allow_methods=apigateway.Cors.ALL_METHODS
                                 ))

        auth_api_integration = apigateway.LambdaIntegration(handler,
                                                            request_templates={
                                                                "application/json": '{"statusCode":"200"}'})

        api.root.add_method("GET", auth_api_integration)

        CfnOutput(self, "AuthAPI", value=api.url)
