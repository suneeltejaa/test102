import os
import csv
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

acctnames = {'299975258897':'amzcldenva',
             '128927813985':'amzcldenva-2',
             '130312249203':'amzcldtste',
             '011275511485':'amzcloud',
             '400387983702':'cim-box-prod',
             '277141866027':'cim-nonprod',
             '947044032016':'cim-prod-use1',
             '198052631016':'cim-prod-usw2',
             '304987092631':'ciqdev',
             '971173505912':'ciqprd',
             '160647469903':'claprd',
             '608515732360':'cspoc2',
             '063706574754':'incu',
             '538235630974':'infosec-dr',
             '530710445070':'midev',
             '245930108294':'mipoc',
             '027532563197':'miprd',
             '190101517450':'misprd',
             '452127281478':'plugprd',
             '703722312672':'poclab',
             '854422766513':'sp-infosec-prod',
             '396496193604':'symprd',
             '347927465314': 'No-Name-347927465314',
             '299602398622': 'No-Name-299602398622'}
data = {}

creds = getcreds()

for keys in creds:
    if keys != 'DEFAULT':
        if keys.split('-')[3] != 'Level1' or keys.split('-')[3] != 'ViewOnlyAccess':
            print (keys)
            creddict = dict(creds[keys])
            ct = {}
            for region in regions:
                client = getec2client(region,creddict)
                out = client.describe_vpcs()['Vpcs']
                ct[region] = len(out)
                print("{0}:{1}".format(region,ct[region]))
            data[keys.split('-')[0]] = ct

csvdata = [['Account/Region','ap-northeast-1','ap-southeast-2','eu-central-1','sa-east-1','us-west-2',
            'ap-northeast-2','ca-central-1','eu-west-1','us-east-1','ap-south-1','eu-west-2',
            'us-east-2','ap-southeast-1','eu-west-3','us-west-1']]

for keys in data:
    ll = []
    acctn = acctnames[keys]
    ll.append(acctn)
    ll.append(data[keys]['ap-northeast-1'])
    ll.append(data[keys]['ap-southeast-2'])
    ll.append(data[keys]['eu-central-1'])
    ll.append(data[keys]['sa-east-1'])
    ll.append(data[keys]['us-west-2'])
    ll.append(data[keys]['ap-northeast-2'])
    ll.append(data[keys]['ca-central-1'])
    ll.append(data[keys]['eu-west-1'])
    ll.append(data[keys]['us-east-1'])
    ll.append(data[keys]['ap-south-1'])
    ll.append(data[keys]['eu-west-2'])
    ll.append(data[keys]['us-east-2'])
    ll.append(data[keys]['ap-southeast-1'])
    ll.append(data[keys]['eu-west-3'])
    ll.append(data[keys]['us-west-1'])
    csvdata.append(ll)

out = expanduser("~")+'\Documents\outputs\\reports\\vpc-report.csv'
with open(out, mode='w',newline='') as outf:
    wr = csv.writer(outf,dialect='excel')
    wr.writerows(csvdata)
