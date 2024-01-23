from aws_cdk import (
    aws_kendra as kendra,
    aws_iam as iam,
    aws_s3 as s3,
    Aws
)
from constructs import Construct


class MediaManagementKendraStack(Construct):
    # create a logging bucket and any bucket created loggs to that bucket.
    def __init__ (self, scope: Construct, construct_id: str, kendra_index_name: str,
                  index_edition: str = 'DEVELOPER_EDITION', **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.construct_id = construct_id
        self.index_edition = index_edition
        self.kendra_index_name = kendra_index_name
        kendra_index_role = iam.Role(self, f'KendraIndexRole{self.construct_id}',
                                     assumed_by=iam.ServicePrincipal('kendra.amazonaws.com'))
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_kendra/CfnDataSource.html

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_kendra/CfnIndex.html

        self.kendra_index = kendra.CfnIndex(self, f"KendraIndex{self.construct_id}",
                                            edition=self.index_edition,
                                            name=self.kendra_index_name,
                                            role_arn=kendra_index_role.role_arn)
        index_policy = iam.Policy(self, f"KendraIndexPolicy{self.construct_id}",
                                  statements=[
                                      iam.PolicyStatement(
                                          effect=iam.Effect.ALLOW,
                                          actions=["cloudwatch:PutMetricData"],
                                          resources=['*'],
                                          conditions={'StringEquals':
                                                          {'cloudwatch:namespace': 'AWS/Kendra'}
                                                      }
                                      ),
                                      iam.PolicyStatement(
                                          effect=iam.Effect.ALLOW,
                                          actions=["cloudwatch:PutMetricData"],
                                          resources=['*'],
                                          conditions={'StringEquals':
                                                          {'cloudwatch:namespace': 'AWS/Kendra'}
                                                      }
                                      ),
                                      iam.PolicyStatement(
                                          effect=iam.Effect.ALLOW,
                                          actions=["logs:DescribeLogGroups"],
                                          resources=['*']
                                      ),
                                      iam.PolicyStatement(
                                          effect=iam.Effect.ALLOW,
                                          actions=["logs:CreateLogGroup"],
                                          resources=[
                                              f'arn:{Aws.PARTITION}:logs:{Aws.REGION}:{Aws.ACCOUNT_ID}:log-group:/aws/kendra/*']
                                      ),
                                      iam.PolicyStatement(
                                          effect=iam.Effect.ALLOW,
                                          actions=["logs:DescribeLogStreams",
                                                   "logs:CreateLogStream",
                                                   "logs:PutLogEvents"],
                                          resources=[
                                              f'arn:{Aws.PARTITION}:logs:{Aws.REGION}:{Aws.ACCOUNT_ID}:log-group:/aws/kendra/*:log-stream:*']
                                      )
                                  ]
                                  )

        kendra_index_role.attach_inline_policy(index_policy)

    def create_kendra_datasource (self, data_source_name: str, s3_bucket: s3.IBucket):
        kendra_datasource_role = iam.Role(self, f'{data_source_name}{self.construct_id}Role',
                                          assumed_by=iam.ServicePrincipal('kendra.amazonaws.com'))
        s3_bucket.grant_read(kendra_datasource_role)
        data_source_configuration_property = kendra.CfnDataSource.DataSourceConfigurationProperty(
            s3_configuration=kendra.CfnDataSource.S3DataSourceConfigurationProperty(
                bucket_name=s3_bucket.bucket_name))
        data_source_props = kendra.CfnDataSourceProps(
            index_id=self.kendra_index.attr_id,
            name=data_source_name,
            type="S3", schedule='cron(0 0/1 * * ? *)',
            data_source_configuration=data_source_configuration_property)
        data_source = kendra.CfnDataSource(self, f"{data_source_name}{self.construct_id}DataSource",
                                                  index_id=data_source_props.index_id,
                                                  name=data_source_props.name,
                                                  type=data_source_props.type,
                                                  role_arn=kendra_datasource_role.role_arn,
                                                  data_source_configuration=data_source_props.data_source_configuration,
                                                  schedule=data_source_props.schedule
                                                  )
        kendra_datasource_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW,
                                                                 actions=['kendra:BatchPutDocument',
                                                                          'kendra:BatchDeleteDocument'],
                                                                 resources=[self.kendra_index.attr_arn]))
        return data_source
