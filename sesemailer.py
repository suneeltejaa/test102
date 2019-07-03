import os
import sys
import pytz
import time
import boto3
import configparser
from os.path import expanduser
from datetime import datetime, timedelta

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
    for keys in condict:
        if keys.split('-')[0] == '245930108294':
            creddict = dict(condict[keys])
            #print (creddict)  ##debug
            break
    return creddict

def getsesclient(region,creddict):
    client = boto3.client('ses',
                              aws_access_key_id=creddict['aws_access_key_id'],
                              aws_secret_access_key=creddict['aws_secret_access_key'],
                              aws_session_token=creddict['aws_session_token'],
                              region_name=region)
    return client

def getec2client(region,creddict):
    client = boto3.client('ec2',
                              aws_access_key_id=creddict['aws_access_key_id'],
                              aws_secret_access_key=creddict['aws_secret_access_key'],
                              aws_session_token=creddict['aws_session_token'],
                              region_name=region)
    return client


creddict = getcreds()
sesclient = getsesclient('us-east-1',creddict)
ec2client = getec2client('us-east-1',creddict)

response = ec2client.describe_instances(
                Filters=[
                    {
                        'Name': 'tag-key',
                        'Values': ['auto_patching']}])['Reservations']
len(response)

tolist = []
if len(response) != 0:
    for values in response:
        taglist = values['Instances'][0]['Tags']
        for keys in taglist:
            if keys['Key'] == 'Owner' or keys['Key'] == 'owner' or keys['Key'] == 'creatorid' or keys['Key'] == 'CreatorId':
                if keys['Value'] not in tolist:
                    tolist.append(keys['Value'])
for add in tolist:
    #print (add) ## debug
    if add.find('@') < 0:
        tolist.remove(add)
        #print ('removed:',add) ##debug

idlist = []
if len(response) != 0:
    for data in response:
        if data['Instances'][0]['InstanceId'] not in idlist:
            idlist.append(values['Instances'][0]['InstanceId'])

print ("ID",idlist)
print("TO",tolist)

# response = sesclient.send_email(
#                     Source= 'sri.pavan.tipirneni@spglobal.com',
#                     Destination={'ToAddresses': ['sri.pavan.tipirneni@spglobal.com']},
#                     Message={
#                         'Subject': { 'Data': 'TEST'},
#                         'Body': {'Text': {'Data': 'SUCCESS'}}})
#
