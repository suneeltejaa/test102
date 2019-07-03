import boto3
import configparser
from os.path import expanduser

## corp account

# acctnums = ['130312249203']

##mi acct numbers

acctnums = ['027532563197']

##acctnums = ['304987092631','027532563197','530710445070','245930108294','396496193604','160647469903',
##            '190101517450','971173505912','063706574754','452127281478',
##            '703722312672']

regions = ['ap-northeast-1','ap-southeast-2','eu-central-1','sa-east-1','us-west-2','ap-northeast-2',
            'ca-central-1','eu-west-1','ap-south-1','eu-west-2','us-east-2','ap-southeast-1',
            'eu-west-3','us-west-1','eu-north-1']

def getcreds(acctnum):
    home = expanduser("~")
    credslo = home+'\.aws\credentials'
    configParser = configparser.RawConfigParser()
    configParser.read(credslo)
    ### account is fixed as of change the variable when needed
    ## get the specific account creds from user
    ## account numer input future extension
    condict = dict(configParser.items())
    for keys in condict:
        if str(keys.split('-')[0]) == acctnum:
            creddict = dict(condict[keys])
            #print (creddict)  ##debug
            break
    return creddict

def getlamclient(region,creddict):
    client = boto3.client('lambda',
                              aws_access_key_id=creddict['aws_access_key_id'],
                              aws_secret_access_key=creddict['aws_secret_access_key'],
                              aws_session_token=creddict['aws_session_token'],
                              region_name=region)
    return client

def getrulesclient(region,creddict):
    client = boto3.client('events',
                              aws_access_key_id=creddict['aws_access_key_id'],
                              aws_secret_access_key=creddict['aws_secret_access_key'],
                              aws_session_token=creddict['aws_session_token'],
                              region_name=region)
    return client

if __name__ == "__main__":
    print ("---------------START---------------")
    print ('INPUT:Custodian Policy Name:',end=" ")
    lamfuncname = 'custodian-'+str(input())
    for acctnum in acctnums:
        creddict = getcreds(acctnum)
        for region in regions:
            client = getlamclient(region,creddict)
            try:
                response = client.delete_function(FunctionName=lamfuncname)
                if response['ResponseMetadata']['HTTPStatusCode'] == 204:
                    print ("Deleted Lambda Funtion {0} in Region {1} account {2}".format(lamfuncname,region,acctnum))
                else:
                    print("ERROR")
                clientrules = getrulesclient(region,creddict)
                responser = clientrules.delete_rule(Name=lamfuncname,Force=True)
                print (responser)
            except:
                continue

    print ("---------------END---------------")
    input("Press enter to exit")
