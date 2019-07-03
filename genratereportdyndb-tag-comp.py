import csv, os
import boto3
import configparser
from os.path import expanduser
############Functions##########################################
############## Get AWS Creds ##############
def getcreds():
    home = expanduser("~")
    credslo = home+'\.aws\credentials'
    configParser = configparser.RawConfigParser()
    configParser.read(credslo)
    ### account is fixed as of change the variable when needed
    ## get the specific account creds from user
    ## account numer input future extension
    condict = dict(configParser.items())
    # for keys in condict:
    #     creddict = dict(condict[keys])
        #print (creddict)  ##debug
    return condict

def getddbclient(region,creddict):
    client = boto3.client('dynamodb',
                              aws_access_key_id=creddict['aws_access_key_id'],
                              aws_secret_access_key=creddict['aws_secret_access_key'],
                              aws_session_token=creddict['aws_session_token'],
                              region_name=region)
    return client

regions = ['ap-northeast-1','ap-southeast-2','eu-central-1','sa-east-1','us-west-2','ap-northeast-2',
           'ca-central-1','eu-west-1','us-east-1','ap-south-1','eu-west-2','us-east-2','ap-southeast-1',
           'eu-west-3','us-west-1']

def gettagdata(tgdat):
    own,bu,appid,env = 'No Owner Tag','No BU Tag','No AppID Tag','No Environment Tag'
    for tags in tgdat:
        if tags['Key'] == 'Owner':
            own = tags['Value']
        elif tags['Key'] == 'BU':
            bu = tags['Value']
        elif tags['Key'] == 'AppID':
            bu = tags['Value']
        elif tags['Key'] == 'Environment':
            bu = tags['Value']
    return own,bu,appid,env

def getddbdata(dat,tagdata,region):
    li = []
    if len(tagdata) != 0:
        own,bu,appid,env = gettagdata(tagdata)
    else:
        own,bu,appid,env = 'No Owner Tag','No BU Tag','No AppID Tag','No Environment Tag'
    li.append(dat['TableName'])
    li.append(dat['TableStatus'])
    li.append(dat['CreationDateTime'])
    li.append(dat['TableSizeBytes'])
    li.append(own)
    li.append(bu)
    li.append(appid)
    li.append(env)
    li.append(region)
    return li

acctnames = {'299975258897':'amzcldenva',
             '128927813985':'amzcldenva-2',
             '130312249203':'amzcldtste',
             '011275511485':'amzcloud',
             '400387983702':'cim-box-prod',
             '277141866027':'cim-nonprod',
             '947044032016':'cim-prod-use1',
             '198052631016':'cim-prod-usw2',
             '304987092631':'mi-capiq-dev',
             '971173505912':'mi-capiq-prod',
             '160647469903':'mi-clarifi-dr-prod',
             '608515732360':'cspoc2',
             '063706574754':'dti-security',
             '538235630974':'infosec-dr',
             '530710445070':'mi-dev',
             '245930108294':'mi-poc-sandbox',
             '027532563197':'mi-prod-stage',
             '190101517450':'mi-spias-prod',
             '452127281478':'mi-domino-prd',
             '703722312672':'dti-shared-services',
             '854422766513':'sp-infosec-prod',
             '396496193604':'mi-symphony-prod-qa',
             '347927465314':'No-Name-347927465314',
             '299602398622':'No-Name-299602398622',
             '82176615813':'platts-dev',
             '31686868338':'platts-qa',
             '557350676069': 'platts-poc',
             '736176406297':'ratings-dev',
             '896639151772':'ratings-dr',
             '156884057084':'ratings-prod'}

creds = getcreds()
for keys in creds:
    csvdata = [['TableName','TableStatus','CreationDateTime','TableSizeBytes',
                'Owner','BU','AppID','Environment','Region']]
    if keys != 'DEFAULT':
        if keys.split('-')[3] != 'Level1':
            creddict = dict(creds[keys])
            for region in regions:
                #print (region)
                if keys.split('-')[0] not in acctnames.keys():
                    print ('LOG:Generating report for account {0} in region {1}'.format(keys.split('-')[0],region))
                else:
                    print ('LOG:Generating report for account {0} in region {1}'.format(acctnames[keys.split('-')[0]],region))
                ll = []
                client = getddbclient(region,creddict)
                out = client.list_tables()['TableNames']
                if len(out) !=0:
                    for data in out:
                        oot = client.describe_table(TableName=data)['Table']
                        tagdata = client.list_tags_of_resource( ResourceArn=oot['TableArn'])['Tags']
                        ll =  getddbdata(oot,tagdata,region)
                        if ll[4] == 'No Owner Tag' or ll[5] == 'No BU Tag' or ll[6] == 'No AppID Tag' or ll[7] == 'No Environment Tag':
                            csvdata.append(ll)
            if keys.split('-')[0] not in acctnames.keys():
                fname = keys.split('-')[0]+'-'+'-dynamodb-report.csv'
            else:
                fname =acctnames[keys.split('-')[0]]+'-dynamodb-report.csv'
            outdir = expanduser("~")+'\Documents\\reports\\dynamodb-tag-comp\\'
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            foutf = outdir+'\\'+fname
            with open(foutf, mode='w+',newline='') as outf:
                wr = csv.writer(outf,dialect='excel')
                wr.writerows(csvdata)

print ('LOG:The Reports are saved at {0}'.format(expanduser("~")+'\Documents\\reports'))
input("Press enter to exit")
