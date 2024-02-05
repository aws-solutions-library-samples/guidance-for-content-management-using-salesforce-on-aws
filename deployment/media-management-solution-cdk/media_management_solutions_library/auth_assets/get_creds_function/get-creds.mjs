// Create clients and set shared const values outside of the handler.
import { STSClient, AssumeRoleCommand } from "@aws-sdk/client-sts"; 
import jwt from "jsonwebtoken";

export const handler = async (event) => {
    const token = event.headers?.Authorization;

    var cert = process.env.CERT;  // get public key

    const decoded = jwt.verify(token, cert);

    if (decoded) {
        const client = new STSClient();
  
        const assumeRoleCmd = new AssumeRoleCommand({
            RoleArn: process.env.ROLE_ARN,
            RoleSessionName:decoded.sub
        })
    
        const role = await client.send(assumeRoleCmd);

        const response = {
            statusCode: 200,
            headers: {
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                accessKeyId: role.Credentials?.AccessKeyId,
                secretAccessKey: role.Credentials?.SecretAccessKey,
                sessionToken: role.Credentials?.SessionToken
            })
        };
        return response;

    }
    else {
        const response = {
            statusCode: 200,
            body: JSON.stringify({auth:false})
        };
    
        // All log statements are written to CloudWatch
        console.info(`response from: ${event.path} statusCode: ${response.statusCode} body: ${response.body}`);
        return response;

    }


}
