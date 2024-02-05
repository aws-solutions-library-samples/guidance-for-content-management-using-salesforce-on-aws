# S3 WIP

This project consists of two components, which have to be deployed seperately.  One to Salesforce, and one to AWS.

**Editor's Note:**
_This is a **work in progress**, and most of this will be parameterized and streamlined for deployment in the near future._

**BEFORE DEPLOYING**
This requires a certificate that can be used in both Salesforce and AWS.  For _DEV_ purposes, a self-signed cert is probably easiest, but must be initiated on the Salesforce side.

1. In the target Salesforce org, go to Setup > Certificate and Key Management > Create Self-Signed Certificate. 
* Here are instructions from Salesforce for creating a self-signed certificate: [Generate a Self-Signed Certificate](https://help.salesforce.com/s/articleView?id=sf.security_keys_creating.htm&type=5).
**Important: Name that certificate `awsJWTCert`.  The component will only look for a certificate with that name.**
1. Create and download the certificate.
2. Overwrite ([media-management-solution-cdk/cert.crt](media-management-solution-cdk/cert.crt)) with the new certificate you just downloaded.

## Deploy AWS
1. The CDK must first be deployed on AWS to create the necessary resources needed for the Salesforce Lightning Web Component.
2. Follow these instruction to configure CDK, and deploy the CDK stack in your AWS Account: [Deploy ](deployment/media-management-solution-cdk/README.md)

## On Salesforce
1. Run `sf project deploy start`
2. Add component to pages as desired.
