from aws_cdk import (
    aws_kms as kms,
    aws_iam as iam,
    Duration
)
from constructs import Construct


class KmsStack(Construct):
    def __init__ (self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

    def master_key_create (self, id):
        kms_key_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=["kms:*"],
                    principals=[iam.AccountRootPrincipal()],
                    resources=["*"]),
                iam.PolicyStatement(
                    actions=["kms:generatedatakey*","kms:decrypt"],
                    principals=[iam.ServicePrincipal("s3.amazonaws.com")],
                    resources=["*"]),
                iam.PolicyStatement(
                    actions=["kms:generatedatakey*", "kms:decrypt"],
                    principals=[iam.ServicePrincipal("rekognition.amazonaws.com")],
                    resources=["*"])
            ]
        )
        master_key = kms.Key(self, id=id,
                             enable_key_rotation=True,
                             pending_window=Duration.days(20),
                             policy=kms_key_policy)
        return master_key
