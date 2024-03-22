
# Deploy sfdc-media-solution CDK Stack

## Set up CDK
The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization process also creates
a virtualenv within this project, stored under the .venv directory.  To create the virtualenv
it assumes that there is a `python3` executable in your path with access to the `venv` package.
If for any reason the automatic creation of the virtualenv fails, you can create the virtualenv
manually once the init process completes.

make sure to be in the `media-management-solution-cdk` directory. If you are in the root directory of this repo, run the following:
```shell script
cd deployment/media-management-solution-cdk
```

To manually create a virtualenv on MacOS and Linux:

```shell script
python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```shell script
source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```shell script
.venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```shell script
pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```shell script
cdk synth
```

## Change default parameters
You can modify parameters in [app.py](app.py):
- `enable_s3_kms_encryption`: Encrypt S3 with KMS (`True`) or SSE-S3 (`False`)
- `deploy_kendra`: Deploy Amazon Kendra (`True`/`False`)
- `kendra_index_edition`: `DEVELOPER_EDITION` (default) or `ENTERPRISE_EDITION`
- `deploy_video_rekognition`: Deploy Video Rekognition stack (`True`/`False`)
- `pub_cert`: Self-signed cert string from Salesforce

### Deployment Notes
- Changing the `deploy_kendra` to `False` will help reduce cost for evaluating the solution for your use case. This is not a blocker for deployment, and can be changed at a later time.
- Setting the `enable_s3_kms_encryption` value to `True` will require additional management of the KMS key. Any user or service roles that reads from the S3 buckets will also need to have encrypted and decrypt permissions for the KMS key used in S3.
- The Salesforce LWC does not currently have any functionality with the output of video rekognition. This is why `deploy_video_rekognition` has a default value of `False`.  This value can be changed after the initial deployment if you wish to process the video files with Amazon Rekognition.
- For `pub_cert`, if you overwrite [cert.crt](cert.crt) with the self-signed cert created in Salesforce, there is nothing to change here.

## Deploy this CloudFormation template.

If this is the first time deploying CDK in this account and region, you will need to bootstrap your environment.
```shell script
cdk bootstrap
```
once this runs, you will now be able to deploy the CDK into your account in the region you bootstrapped.

```shell script
cdk deploy
```

The outputs that will be used in configuring the Salesforce LWC can be found in the CloudFormation outputs tab:

<img src="../../assets/images/cloudformation-output.png" alt="cf-output" width="800" height="auto">

It is also avaiable in the CDK CLI after a sucessful deployment:

<img src="../../assets/images/cdk-output.png" alt="cdk-output" width="800" height="auto">


## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
