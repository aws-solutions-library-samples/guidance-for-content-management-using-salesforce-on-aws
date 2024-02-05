# S3 WIP

This project consists of two components, which have to be deployed seperately.  One to Salesforce, and one to AWS.

**Editor's Note:**
_This is a **work in progress**, and most of this will be parameterized and streamlined for deployment in the near future._

**BEFORE DEPLOYING**
This requires a certificate that can be used in both Salesforce and AWS.  For _DEV_ purposes, a self-signed cert is probably easiest, but must
be initiated on the Salesforce side.

1. In the target Salesforce org, go to Setup > Certificate and Key Management > Create Self-Signed Certificate.
    **Important: Name that certificate `awsJWTCert`.  The component will only look for a certificate with that name.**
2. Create and download the certificate.
3. Overwrite ([cert.crt](media-management-solution-cdk/cert.crt)) with the new certificate you just downloaded.

## On AWS
1. Create an IAM role that has sufficient permissions for any actions you wish the user to be able to take.
2. Copy the .crt file from earlier into the `src/handlers` directory, and update line 11 of `get-creds.mjs` to point to the correct file name.
3. Make sure the ARN on line 19 matches the ARN of the role.
4. Run `sam deploy`
5. Make a note of the API Gateway URL (i.e. `https://yc5dfnvtcg.execute-api.us-east-1.amazonaws.com/Prod/`)

## On Salesforce
1. Change the URL on line 89 of `awsS3Files.js` to the API Gateway URL from the AWS steps.
2. Make sure the cert referenced on line 17 of `AwsCredentialsController.cls` matches the name of the certificate created in the first step.
3. Run `sf project deploy start`
4. Add component to pages as desired.
