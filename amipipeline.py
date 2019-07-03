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
        if keys.split('-')[0] == '011275511485':
            creddict = dict(condict[keys])
            #print (creddict)  ##debug
            break
    return creddict

############### START the SSM and EC2 Client #############
def getssmclient(region):
    client = boto3.client('ssm',
                              aws_access_key_id=creddict['aws_access_key_id'],
                              aws_secret_access_key=creddict['aws_secret_access_key'],
                              aws_session_token=creddict['aws_session_token'],
                              region_name=region)
    return client

def getec2client(region):
    client = boto3.client('ec2',
                              aws_access_key_id=creddict['aws_access_key_id'],
                              aws_secret_access_key=creddict['aws_secret_access_key'],
                              aws_session_token=creddict['aws_session_token'],
                              region_name=region)
    return client

#####################################################
### Put the Latest AMIs in the parameter store###
def putparam(na,val,ty,client):
    response = client.put_parameter(
               Name = na,
               Value = val,
               Type = ty,
               Overwrite = True)
    return response

def changeintialparams(RHEL7,win2012,win2016,ssm_client):
    params = ssm_client.describe_parameters()['Parameters']
    for data in params:
        if data['Name'] == 'latestAMIRHEL7':
            Value = RHEL7
        elif data['Name'] == 'latestAmiWin2012':
            Value = win2012
        elif data['Name'] == 'latestAmiWin2016':
            Value = win2016
        response = putparam(data['Name'],Value,data['Type'],ssm_client)
        if response['Version']>data['Version']:
            print("SUCCESS:{0} parameter updated".format(data['Name']))
        else:
            print("FAILED:{0} parameter NOT-updated".format(data['Name']))
            sys.exit("LOG:Please Verify in the AWS Console")

def changeregionparams(images):
    for keys in images:
        client = getssmclient(keys)
        params = client.describe_parameters()['Parameters']
        for data in params:
            if data['Name'] == 'latestAMIRHEL7':
                Value = images[keys][amill[2]]
            elif data['Name'] == 'latestAmiWin2012':
                Value = images[keys][amill[1]]
            elif data['Name'] == 'latestAmiWin2016':
                Value = images[keys][amill[0]]
            response = putparam(data['Name'],Value,data['Type'],client)
            if response['Version']>data['Version']:
                print("SUCCESS:{0} parameter updated in region {1}".format(data['Name'],keys))
            else:
                print("FAILED:{0} parameter NOT-updated in region {1}".format(data['Name'],keys))
                sys.exit("LOG:Please Verify in the AWS Console")

#############################################################
### print and wait for status
def printautstat(autoID):
    while True:
        stat,name = getautstatus(autoID)
        if stat == 'InProgress':
            print ('PROGRESS:{0} with id {1} is {2}'.format(name,autoID,stat))
            time.sleep(30)
        elif stat == 'Failed':
            getfailuredata(autoID)
            print ('FAILED:{0} with id {1} has {2}'.format(name,autoID,stat))
            return 0
            break
        elif stat == 'Success':
            print ('SUCCESS:{0} with id {1} has SUCCEEDED'.format(name,autoID))
            return 1
            break

### This loop may be infinite check redundancy with other methods
def printallstats(lis):
    f = 0
    while True:
        ll = {}
        i = 0
        if len(lis) != 0:
            stat = getallstatus(lis)
        else:
            return f
        for data in stat:
            ll[data['AutomationExecutionId']]=data['AutomationExecutionStatus']
        for values in ll:
            if ll[values] == 'InProgress':
                print ('PROGRESS:{0} is {1}'.format(values,ll[values]))
                i = i+1
            if ll[values] == 'Success':
                print ('SUCCESS:{0} has SUCCEEDED'.format(values))
                lis.remove(values)
            elif ll[values] == 'Failed':
                print ('FAILED:{0} has {1}'.format(values,ll[values]))
                f = f+1
                lis.remove(values)
        if i > 0:
            time.sleep(30)
    return f
########### Get automation status ##################
def getautstatus(autoID):
    try:
        status = ssm_client.describe_automation_executions(
            Filters=[
                {'Key': 'ExecutionId',
                 'Values': [autoID]}])
        stat = status['AutomationExecutionMetadataList'][0]['AutomationExecutionStatus']
        name = status['AutomationExecutionMetadataList'][0]['DocumentName']
    except:
        print ("ERROR:Token Expired")
        sys.exit("ERROR:Token Expired")
    return stat,name

def getallstatus(lis):
    status = ssm_client.describe_automation_executions(
        Filters=[
            {'Key': 'ExecutionId',
             'Values': lis}])['AutomationExecutionMetadataList']
    return status

######### Get Failure data for the automation #########
def getfailuredata(autoID):
    try:
        fdata = ssm_client.describe_automation_step_executions(
            AutomationExecutionId=autoID)['StepExecutions']
    except:
        print ("ERROR:Token Expired")
        sys.exit("ERROR:Token Expired")
    for values in fdata:
        if values['StepStatus'] == 'Failed':
            print ('FAILED:Failed at step {0}'.format(values['StepName']))

############################################################
############# Full Release Status #########################
def getfullreleasestatus(tt):
    yo = {}
    ll = []
    response = ssm_client.describe_automation_executions(
        Filters=[{
            'Key':'DocumentNamePrefix',
            'Values': ['Win2016','RHEL7','Win2012R2-64bit']},
                 {
                     'Key': 'ExecutionStatus',
                     'Values': ['InProgress']
                 }])['AutomationExecutionMetadataList']
    if len(response) != 0 :
        for data in response:
            print ("LOG:{0} started with Execution ID {1}".format(data['DocumentName'],data['AutomationExecutionId']))
            yo[data['DocumentName']] = data['AutomationExecutionId']
        for values in yo:
            ll.append(yo[values])
        f = printallstats(ll)
        return f
    else:
        print ("LOG: No Execution started")
        sys.exit("LOG:Please check AWS console")

###########################################################
########### Share to Regions ####################

def sharetoregions():
    shrg = ssm_client.start_automation_execution(DocumentName='copyAMItoRegions')
    print ('LOG:Execution Started with ID {0}'.format(shrg['AutomationExecutionId']))
    ss = printautstat(shrg['AutomationExecutionId'])
    return ss

#### Check full release or one release ###

def getreleasetype():
    if len(RHEL7) == 0 and len(win2012) == 0:
        return "WIN2016"
    elif len(RHEL7) == 0 and len(win2016) == 0:
        return "WIN2012"
    elif len(win2012) == 0 and len(win2016) == 0 :
        return "RHEL7"
    else:
        return 'all'

######################################################################
############# sharing functions ##########

def getamistate(region):
    while True:
        a = 0
        amlis = {}
        datlis = {}
        client = getec2client(region)
        response = client.describe_images(
            Filters=[
                {
                    'Name':'name',
                    'Values': amill},])['Images']
        for data in response:
            amlis[data['ImageId']] = data['State']
        for state in amlis:
            print ("LOG:AMI {0} in region {1} is in the state {2}".format(state,region,amlis[state]))
            if amlis[state] == 'pending':
                time.sleep(30)
            elif amlis[state] == 'available':
                a = a+1
        if a == 3:
            for data in response:
                datlis[data['Name']] = data['ImageId']
                print ("LOG:AMID for {0} in region {2} is {1}".format(data['Name'],data['ImageId'],region))
            return datlis

def checkamistatus():
    regions = ['us-east-1','us-west-2','ap-southeast-1','eu-west-1']
    data= {}
    for region in regions:
        print ("LOG: Checking AMI Status in Region {0}".format(region))
        data[region] = getamistate(region)
    return data

def sharetoaccts():
    li = ['shareAMIRHEL7','shareAMIwin2012','shareAMIwin2016']
    regions = ['us-east-1','us-west-2','ap-southeast-1','eu-west-1']
    for region in regions:
        client = getssmclient(region)
        sharerh = client.start_automation_execution(DocumentName= li[0])
        sharew12 = client.start_automation_execution(DocumentName= li[1])
        sharew16 = client.start_automation_execution(DocumentName= li[2])
        print ('LOG:{0} Execution Started in region {1} with ID {2}'
               .format(li[0],region,sharerh['AutomationExecutionId']))
        print ('LOG:{0} Execution Started in region {1} with ID {2}'
               .format(li[1],region,sharew12['AutomationExecutionId']))
        print ('LOG:{0} Execution Started in region {1} with ID {2}'
               .format(li[2],region,sharew16['AutomationExecutionId']))
        execli = [sharerh['AutomationExecutionId'],sharew12['AutomationExecutionId'],
                  sharew16['AutomationExecutionId']]
        st = printallstats(execli)
        if st != 0 :
            print ("FAILED: Sharing AMI to Accounts Failed")
            sys.exit("LOG:Please Verify in the AWS Console or Previous Logs")
    return 1

def printimages(images):
    amioutll = [{}]
    rhel7 = [{"current":{"us-east-1":"","us-west-2":"","ap-southeast-1":"","eu-west-1":""}}]
    win2k12 = [{"current":{"us-east-1":"","us-west-2":"","ap-southeast-1":"","eu-west-1":""}}]
    win2k16 = [{"current":{"us-east-1":"","us-west-2":"","ap-southeast-1":"","eu-west-1":""}}]
    for image in images:
        rhel7[0]['current'][image] = images[image][amill[2]]
        win2k12[0]['current'][image] = images[image][amill[2]]
        win2k12[0]['current'][image] = images[image][amill[2]]
    amioutll[0]['rhel7']=rhel7
    amioutll[0]['win2k12']=win2k12
    amioutll[0]['win2k16']=win2k16
    return amioutll

################## MAIN EXECUTIONS ##################################
########## Request the Inputs of Latest AMIS from the User ########
utc=pytz.UTC
currenttime = utc.localize(datetime.now())
print ('INFO:Leave input empty if its just One AMI Update')
print ('INPUT:Latest RHEL7 image ID:',end=" ")
RHEL7 = str(input())
print ('INPUT:Latest win2012R2 image ID:',end=" ")
win2012 = str(input())
print ('INPUT:Latest WIN2016 image ID:',end=" ")
win2016 = str(input())

rtype = getreleasetype()

### get credentials start boto client

creddict = getcreds()
ssm_client = getssmclient('us-east-1')
changeintialparams(RHEL7,win2012,win2016,ssm_client)

############# Start the Automation for creation of AMI ############
## Request Parameters check
### Note Time of execution
automationstart = ssm_client.start_automation_execution(DocumentName='amiAutoALL')
### Get automation ID from response
print ('LOG:Execution Started with ID {0}'.format(automationstart['AutomationExecutionId']))
ss = printautstat(automationstart['AutomationExecutionId'])
### Individual Image Automations
# response = ssm_client.start_automation_execution(DocumentName='Win2016',
#                                                 Parameters= {'sourceAMIid':[win2016]})
if ss == 1:
    fail = getfullreleasestatus(currenttime)
else:
    print ("ERROR:Automation Failed please check the AWS console")

##### Share to Regions #############
if fail == 0:
    reg = sharetoregions()
else:
    print ("FAILED: Automation failed")
    sys.exit("LOG:Please Verify in the AWS Console or Previous Logs")

#######Share to Accounts Region Wise and print AMI########################
w216aminame = 'SPGi.Win-2016-'+str(currenttime).split(" ")[0]
w212aminame = 'SPGi.W2K12.R2-'+str(currenttime).split(" ")[0]
rhel7aminame = 'SPGi-RHEL-7-HVM_'+str(currenttime).split(" ")[0]
amill = [w216aminame,w212aminame,rhel7aminame]

if reg == 1:
    images = checkamistatus()
    changeregionparams(images)
    act = sharetoaccts()
    if act == 1:
        outdic = printimages(images)
        print ("SUCCESS: AMID's propogation successful")
        print ("OUTPUT: The following are the latest ImageID's")
        print (outdic)
    else:
        print ("FAILED: Sharing AMI to accounts Failed")
        sys.exit("LOG:Please Verify in the AWS Console or Previous Logs")
else:
    print ("FAILED: Sharing AMI to regions Failed")
    sys.exit("LOG:Please Verify in the AWS Console or Previous Logs")
