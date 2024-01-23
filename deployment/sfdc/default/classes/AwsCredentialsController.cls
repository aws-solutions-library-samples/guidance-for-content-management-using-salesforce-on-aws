public with sharing class AwsCredentialsController {

    @AuraEnabled
    public static String getJwt() {
        Auth.JWT token = new Auth.JWT();
        token.setIss(UserInfo.getOrganizationId());
        token.setSub(UserInfo.getUserId());
        token.setAud('AWSS3Component');
        
        Map<String, String> claims = new Map<String, String> {};
        
        claims.put('email', UserInfo.getUserEmail());
        claims.put('name', UserInfo.getName());
        
        token.setAdditionalClaims(claims);
        
        Auth.JWS stoken = new Auth.JWS(token, 'devCert');
        
        String jwt = stoken.getCompactSerialization();
        
        return jwt;
    }
}