import os
import sys
import yaml
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
        if keys.split('-')[0] == '011275511485':
            creddict = dict(condict[keys])
            #print (creddict)  ##debug
            break
    return creddict

def getcftclient(region):
    client = boto3.client('cloudformation',
                              aws_access_key_id=creddict['aws_access_key_id'],
                              aws_secret_access_key=creddict['aws_secret_access_key'],
                              aws_session_token=creddict['aws_session_token'],
                              region_name=region)
    return client

def getiamroledata(type):
    if type == 'prod':
        file = expanduser('~')+'\Documents\\adfs-iam-roles\\02-IAMRoleSetup-PROD.yml'
    elif type == 'dev':
        file = expanduser('~')+''
    elif type == 'poc':
        file = expanduser('~')+''



creddict = getcreds()
client = getcftclient('us-east-1')
response = client.describe_stacks()['Stacks']
