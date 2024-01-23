#!/usr/bin/env python3
import aws_cdk as cdk
from media_management_solutions_library.media_management_solutions_library_stack import MediaManagementSolutionsLibraryStack


app = cdk.App()
deployment_stack=MediaManagementSolutionsLibraryStack(app, "sfdc-media-solution",
                                                      enable_s3_kms_encryption=False, # SSE-S3 encryption will be used if left to False.
                                                      deploy_kendra=True, # Bool value to determine if kendra will be deployed
                                                      kendra_index_edition="DEVELOPER_EDITION") # accepted values are: DEVELOPER_EDITION or ENTERPRISE_EDITION

app.synth()