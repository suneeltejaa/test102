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

def getec2client(region,creddict):
    client = boto3.client('ec2',
                              aws_access_key_id=creddict['aws_access_key_id'],
                              aws_secret_access_key=creddict['aws_secret_access_key'],
                              aws_session_token=creddict['aws_session_token'],
                              region_name=region)
    return client

regions = ['ap-northeast-1','ap-southeast-2','eu-central-1','sa-east-1','us-west-2','ap-northeast-2',
           'ca-central-1','eu-west-1','us-east-1','ap-south-1','eu-west-2','us-east-2','ap-southeast-1',
           'eu-west-3','us-west-1']

def gettagdata(tgdat,tagval):
    for tags in tgdat:
        if tags['Key'] == tagval:
            return tags['Value']
            break
    defa = 'No'+' '+tagval+' '+'tag'
    return defa

def gettagdatacomp(tgdat):
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

def getec2data(dat,region):
    li = []
    if 'Tags' in dat['Instances'][0].keys():
        own,bu,appid,env = (gettagdatacomp(dat['Instances'][0]['Tags']))
    else:
        own,bu,appid,env = 'No Owner Tag','No BU Tag','No AppID Tag','No Environment Tag'

    if 'Tags' in dat['Instances'][0].keys():
        li.append(gettagdata(dat['Instances'][0]['Tags'],'Name'))
    else:
        li.append('No Name Tag')
    li.append(dat['Instances'][0]['InstanceId'])
    li.append(dat['Instances'][0]['State']['Name'])
    li.append(own)
    li.append(bu)
    li.append(appid)
    li.append(env)
    li.append(dat['OwnerId'])
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
    csvdata = [['Name','Instance ID','Instance State','Owner','BU',
                'AppID','Environment','Account Owner ID','Region']]
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
                client = getec2client(region,creddict)
                out = client.describe_instances()['Reservations']
                if len(out) !=0:
                    for data in out:
                        ll =  getec2data(data,region)
                        if ll[3] == 'No Owner Tag' or ll[4] == 'No BU Tag' or ll[5] == 'No AppID Tag' or ll[6] == 'No Environment Tag':
                            csvdata.append(ll)
            if keys.split('-')[0] not in acctnames.keys():
                fname = keys.split('-')[0]+'-'+'-ec2-report.csv'
            else:
                fname =acctnames[keys.split('-')[0]]+'-ec2-report.csv'
            outdir = expanduser("~")+'\Documents\\reports\\ec2-tag-comp\\'
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            foutf = outdir+'\\'+fname
            with open(foutf, mode='w+',newline='') as outf:
                wr = csv.writer(outf,dialect='excel')
                wr.writerows(csvdata)

print ('LOG:The Reports are saved at {0}'.format(expanduser("~")+'\Documents\\reports'))
input("Press enter to exit")
