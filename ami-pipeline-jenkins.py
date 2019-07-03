import os
import sys
import pytz
import json
import time
import boto3
import configparser
from os.path import expanduser
from datetime import datetime, timedelta

############Functions##########################################
############## Get AWS Creds ##############
def getcreds():
    arn = 'arn:aws:iam::011275511485:role/AMI-Auto-Deploy-amzcloud-assume-role'
    client = boto3.client('sts',region_name='us-east-1')
    response = client.assume_role(RoleArn=arn,RoleSessionName='AMIAutoDeploy',DurationSeconds=28800)
    ### account is fixed as of change the arn when needed
    ## get the specific account creds from IAM role
    if 'Credentials' in response.keys():
        creddict = response['Credentials']
        return creddict
    else:
        print("ERROR: Unable to fetch credentials")
        sendfailureemail("Unable to Fetch Credentials.Deployment Failed. PLease verify IAM roles")

############### START the SSM and EC2 Client #############
def getssmclient(region):
    client = boto3.client('ssm',
                              aws_access_key_id=creddict['AccessKeyId'],
                              aws_secret_access_key=creddict['SecretAccessKey'],
                              aws_session_token=creddict['SessionToken'],
                              region_name=region)
    return client

def getec2client(region):
    client = boto3.client('ec2',
                              aws_access_key_id=creddict['AccessKeyId'],
                              aws_secret_access_key=creddict['SecretAccessKey'],
                              aws_session_token=creddict['SessionToken'],
                              region_name=region)
    return client

############# send failure emails ##########

def sendfailureemail(sendstring):
    path= "/home/jenkins-cc/jenkins-prod-cc/workspace/Cloud-Custodian/AMI-Auto-Deploy/AMI.json"
    file = open(path)
    data = json.load(file)
    toemaillist =data[0]['TOLIST']
    sescli = boto3.client('ses',
                              aws_access_key_id=creddict['AccessKeyId'],
                              aws_secret_access_key=creddict['SecretAccessKey'],
                              aws_session_token=creddict['SessionToken'],
                              region_name='us-east-1')
    print("Sending failure email to {0}".format(toemaillist))
    sescli.send_email(
                        Source= 'corp-aws-cloudcustodian@spglobal.com',
                        Destination={'ToAddresses': toemaillist},
                        Message={
                            'Subject': { 'Data': "AMI Automation FAILURE"},
                            'Body': {'Text': {'Data': sendstring}}})
    sys.exit()

def sendoutdata(sendstring):
    path= "/home/jenkins-cc/jenkins-prod-cc/workspace/Cloud-Custodian/AMI-Auto-Deploy/AMI.json"
    file = open(path)
    data = json.load(file)
    toemaillist =data[0]['TOLIST']
    sescli = boto3.client('ses',
                              aws_access_key_id=creddict['AccessKeyId'],
                              aws_secret_access_key=creddict['SecretAccessKey'],
                              aws_session_token=creddict['SessionToken'],
                              region_name='us-east-1')
    print("Sending success email to {0}".format(toemaillist) )
    emaildat= "The following is the list of published AMI"+"\r\n"
    for data in sendstring[0]:
        emaildat=emaildat+"\r\n"+data.upper()+"\r\n"+str(sendstring[0][data])+"\r\n"
    sescli.send_email(
                        Source= 'corp-aws-cloudcustodian@spglobal.com',
                        Destination={'ToAddresses': toemaillist},
                        Message={
                            'Subject': { 'Data': "AMI Automation SUCCESS"},
                            'Body': {'Text': {'Data': emaildat}}})


#####################################################
### Put the Latest AMIs in the parameter store###
def putparam(na,val,ty,client):
    response = client.put_parameter(
               Name = na,
               Value = val,
               Type = ty,
               Overwrite = True)
    return response

def changeintialparams(RHEL7,win2012,win2016,linux2,ssm_client,runtype):
    params = ssm_client.describe_parameters()['Parameters']
    for data in params:
        if data['Name'] == 'latestAMIRHEL7':
            if len(RHEL7) != 0:
                Value = RHEL7
        elif data['Name'] == 'latestAmiWin2012':
            if len(win2012) != 0:
                Value = win2012
        elif data['Name'] == 'latestAmiWin2016':
            if len(win2016) != 0:
                Value = win2016
        elif data['Name'] == 'latestAMILINUX2':
            if len(linux2) != 0:
                Value = linux2
        try:
            response = putparam(data['Name'],Value,data['Type'],ssm_client)
            if response['Version']>data['Version']:
                print("SUCCESS:{0} parameter updated".format(data['Name']))
            else:
                print("FAILED:{0} parameter NOT-updated".format(data['Name']))
                sendfailureemail("Parameter Updation Failed in us-east-1. Please Verify Parameter store in SSM")
        except:
            print ("FAILED: Parameters cannot be updated")
            sendfailureemail("Parameter Updation Failed in us-east-1. Please Verify Parameter store in SSM")

def changeregionparams(images,amill):
    for keys in images:
        if keys != 'us-east-1':
            client = getssmclient(keys)
            params = client.describe_parameters()['Parameters']
            for data in params:
                if data['Name'] == 'latestAMILINUX2':
                    Value = images[keys][amill[3]]
                elif data['Name'] == 'latestAMIRHEL7':
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
                    sendfailureemail("Parameter Updation Failed in different regions. Please Verify Parameter store in SSM")

#############################################################
### print and wait for status
def printautstat(autoID):
    while True:
        stat,name = getautstatus(autoID)
        if stat == 'InProgress':
            print ('PROGRESS:{0} with id {1} is {2}'.format(name,autoID,stat))
            time.sleep(15)
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
def printallstats(lis,region):
    f = 0
    while True:
        ll = {}
        i = 0
        if len(lis) != 0:
            stat = getallstatus(lis,region)
        else:
            return f
        for data in stat:
            ll[data['AutomationExecutionId']]=data['AutomationExecutionStatus']
        for values in ll:
            if ll[values] == 'InProgress' or ll[values] == 'Waiting':
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
            time.sleep(15)
    return f
########### Get automation status ##################
def getautstatus(autoID):
    ssm_client = getssmclient('us-east-1')
    status = ssm_client.describe_automation_executions(
        Filters=[
            {'Key': 'ExecutionId',
             'Values': [autoID]}])
    stat = status['AutomationExecutionMetadataList'][0]['AutomationExecutionStatus']
    name = status['AutomationExecutionMetadataList'][0]['DocumentName']
    return stat,name

def getallstatus(lis,region):
    ssm_client = getssmclient(region)
    status = ssm_client.describe_automation_executions(
        Filters=[
            {'Key': 'ExecutionId',
             'Values': lis}])['AutomationExecutionMetadataList']
    return status

######### Get Failure data for the automation #########
def getfailuredata(autoID):
    ssm_client = getssmclient('us-east-1')
    fdata = ssm_client.describe_automation_step_executions(
        AutomationExecutionId=autoID)['StepExecutions']
    for values in fdata:
        if values['StepStatus'] == 'Failed':
            print ('FAILED:Failed at step {0}'.format(values['StepName']))

############################################################
############# Full Release Status #########################
def getfullreleasestatus(tt):
    yo = {}
    ll = []
    time.sleep(15)
    ssm_client = getssmclient('us-east-1')
    response = ssm_client.describe_automation_executions(
        Filters=[{
                    'Key':'DocumentNamePrefix',
                    'Values': ['Win2016','RHEL7','Win2012R2-64bit','LINUX2']},
                 {
                     'Key': 'ExecutionStatus',
                     'Values': ['InProgress','Waiting','Pending']
                 }])['AutomationExecutionMetadataList']
    if len(response) != 0 :
        for data in response:
            print ("LOG:{0} started with Execution ID {1}".format(data['DocumentName'],data['AutomationExecutionId']))
            yo[data['DocumentName']] = data['AutomationExecutionId']
        for values in yo:
            ll.append(yo[values])
        f = printallstats(ll,'us-east-1')
        return f
    else:
        print ("LOG: No Execution started")
        sendfailureemail("Failed at automation initiation")

###########################################################
########### Share to Regions ####################

def sharetoregions():
    ssm_client = getssmclient('us-east-1')
    shrg = ssm_client.start_automation_execution(DocumentName='copyAMItoRegions')
    print ('LOG:Execution Started with ID {0}'.format(shrg['AutomationExecutionId']))
    ss = printautstat(shrg['AutomationExecutionId'])
    return ss

#### Check full release or one release ###

def getreleasetype(runtype,RHEL7,win2012,win2016,linux2):
    if len(RHEL7) == 0 and len(win2012) == 0 and len(linux2) == 0:
        return "WIN2016",'test'
    elif len(RHEL7) == 0 and len(win2016) == 0 and len(linux2) == 0:
        return "WIN2012",'test'
    elif len(win2012) == 0 and len(win2016) == 0 and len(linux2) == 0:
        return "RHEL7",'test'
    elif len(win2012) == 0 and len(win2016) == 0 and len(linux2) == 0:
        return "RHEL7",'test'
    elif len(win2012) == 0 and len(win2016) == 0 and len(RHEL7) == 0:
        return "LINUX2",'test'
    else:
        return 'all',runtype

######################################################################
############# sharing functions ##########

def getamistate(region,amill):
    while True:
        a = 0
        amlis = {}
        datlis = {}
        client = getec2client(region)
        ## debug if response = []
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
                time.sleep(15)
            elif amlis[state] == 'available':
                a = a+1
        if a == 4: ## this is the total number of AMI in a region
            for data in response:
                datlis[data['Name']] = data['ImageId']
                print ("LOG:AMID for {0} in region {2} is {1}".format(data['Name'],data['ImageId'],region))
            return datlis

def checkamistatus(amill):
    regions = ['us-east-1','us-west-2','ap-southeast-1','eu-west-1']
    data= {}
    for region in regions:
        print ("LOG: Checking AMI Status in Region {0}".format(region))
        data[region] = getamistate(region,amill)
    return data

def shareami(amiid,acctnum):
    try:
        source_ami = source_ec2.Image(amiid)
        source_snapshot = source_ec2.Snapshot(source_ami.block_device_mappings[0]['Ebs']['SnapshotId'])
        #### Share Snapshot ####
        source_snapshot.modify_attribute(
                Attribute='createVolumePermission',
                OperationType='add',
                UserIds=[acctnum]
                )
        print ("LOG:Sharing AMI {0} to account {1}".format(amiid,acctnum)")
        #### Share AMI ####
        source_ami.modify_attribute(
                LaunchPermission={
                    'Add': [
                        {
                            'UserId': acctnum
                        }
                    ]
                    }
                )
    except:
        print ("ERROR:Sharing Failed AMI {0} to account {1}".format(amiid,acctnum)")
        continue

def sharetoaccts(images,amill,acctlist):
    li = ['shareAMIRHEL7','shareAMIwin2012','shareAMIwin2016','shareAMILINUX2']
    regions = ['us-east-1','us-west-2','ap-southeast-1','eu-west-1']
    for region in regions:
        client = getssmclient(region)
        sharerh = client.start_automation_execution(DocumentName= li[0])
        sharew12 = client.start_automation_execution(DocumentName= li[1])
        sharew16 = client.start_automation_execution(DocumentName= li[2])
        shareli = client.start_automation_execution(DocumentName= li[3])
        print ('LOG:{0} Execution Started in region {1} with ID {2}'
               .format(li[0],region,sharerh['AutomationExecutionId']))
        print ('LOG:{0} Execution Started in region {1} with ID {2}'
               .format(li[1],region,sharew12['AutomationExecutionId']))
        print ('LOG:{0} Execution Started in region {1} with ID {2}'
               .format(li[2],region,sharew16['AutomationExecutionId']))
        print ('LOG:{0} Execution Started in region {1} with ID {2}'
               .format(li[3],region,shareli['AutomationExecutionId']))
        execli = [sharerh['AutomationExecutionId'],sharew12['AutomationExecutionId'],
                  sharew16['AutomationExecutionId'],shareli['AutomationExecutionId']]
        st = printallstats(execli,region)
        if st != 0 :
            print ("FAILED: Sharing AMI to Accounts Failed")
            sendfailureemail("Sharing to Accounts Failed")

##### fix this ####
def printimages(images,amill):
    amioutll = [{}]
    regions = ['us-east-1','us-west-2','ap-southeast-1','eu-west-1']
    rhel7=[{"current":{}}]
    win2k12=[{"current":{}}]
    win2k16=[{"current":{}}]
    linux2 = [{"current":{}}]
    for region in regions:
        for ids in images[region]:
            ids
            if ids == amill[3]:
                linux2[0]['current'][region] = images[region][ids]
            elif ids == amill[2]:
                rhel7[0]['current'][region] = images[region][ids]
            elif ids == amill[1]:
                win2k12[0]['current'][region] = images[region][ids]
            elif ids == amill[0]:
                win2k16[0]['current'][region] = images[region][ids]
    amioutll[0]['rhel7']=rhel7
    amioutll[0]['win2k12']=win2k12
    amioutll[0]['win2k16']=win2k16
    amioutll[0]['linux2']=linux2
    return amioutll

################## MAIN EXECUTIONS ##################################
########## Request the Inputs of Latest AMIS from the User ########
def amideploy():
    utc=pytz.UTC
    currenttime = utc.localize(datetime.now())
    ### Need to change the input from a json in github
    # print ('INFO:Leave input empty if its just One AMI Update')
    # print ('INPUT:Latest RHEL7 image ID:')
    # RHEL7 = str(raw_input())
    # print ('INPUT:Latest win2012R2 image ID:')
    # win2012 = str(raw_input())
    # print ('INPUT:Latest WIN2016 image ID:')
    # win2016 = str(raw_input())
    # print ('INPUT: Run Type (test/full):')
    # runtype = str(raw_input()).lower()
    # Workspace
    path= "/home/jenkins-cc/jenkins-prod-cc/workspace/Cloud-Custodian/AMI-Auto-Deploy/AMI.json"
    file = open(path)
    data = json.load(file)
    RHEL7 = data[0]['RHEL7']
    win2012 = data[0]['win2012']
    win2016 = data[0]['win2016']
    linux2 = data[0]['LINUX2']
    runtype = 'full'
    #### Sanity check
    if not (len(runtype) == 0 or runtype != 'test' or runtype != 'full'):
        print ("ERROR: Wrong runtype. Selecting default test")
        runtype = 'test'
    else:
        print ("LOG: Running {0} relese".format(runtype))
    if len(RHEL7) == 0 or len(win2012) == 0 or len(win2016) == 0:
        if runtype != 'test':
            print ("ERROR: Empty Inputs please try again")
            sendfailureemail("The values of AMI are empty please check")
    rtype,runtype = getreleasetype(runtype,RHEL7,win2012,win2016,linux2)
    inp = {'RHEL7':RHEL7,
           'LINUX2':linux2,
           'WIN2012':win2012,
           'WIN2016':win2016}
    ### get credentials start boto client
    ssm_client = getssmclient('us-east-1')
    if rtype == 'all':
        changeintialparams(RHEL7,win2012,win2016,linux2,ssm_client,runtype)

    ############# Start the Automation for creation of AMI ############
    ## Request Parameters check
    ### Note Time of execution
    if rtype == 'all':
        automationstart = ssm_client.start_automation_execution(DocumentName=
                                                                'amiAutoALL')
        ### Get automation ID from response
        print ('LOG:Execution Started with ID {0}'.format(automationstart['AutomationExecutionId']))
        ss = printautstat(automationstart['AutomationExecutionId'])
    else:
        ### Individual Image Automations
        automationstart = ssm_client.start_automation_execution(DocumentName=rtype,
                                                         Parameters= {'sourceAMIid':
                                                                          [inp[rtype]]})
        print ('LOG:Execution Started with ID {0}'.format(automationstart['AutomationExecutionId']))
        ss = printautstat(automationstart['AutomationExecutionId'])

    if ss == 1:
        fail = getfullreleasestatus(currenttime)
    else:
        print ("ERROR:Automation Failed please check the AWS console")
        sendfailureemail("Automation Failed please check the AWS console")
    ### exit here if you are just testing
    if runtype == 'test':
        print ("LOG:Finished Testing")
        sendfailureemail("Finished Testing")
    ### Full deploy
    ##### Share to Regions #############
    if fail == 0:
        reg = sharetoregions()
    else:
        print ("FAILED: Automation failed")
        sendfailureemail("Automation Failed please check the AWS console")
    #######Share to Accounts Region Wise and print AMI########################
    w216aminame = 'SPGi.Win-2016-'+str(currenttime).split(" ")[0]
    w212aminame = 'SPGi.W2K12.R2-'+str(currenttime).split(" ")[0]
    rhel7aminame = 'SPGi-RHEL-7-HVM_'+str(currenttime).split(" ")[0]
    linux2aminame = 'SPGi-LINUX2_'+str(currenttime).split(" ")[0]
    amill = [w216aminame,w212aminame,rhel7aminame,linux2aminame]
    if reg == 1:
        images = checkamistatus(amill)
        changeregionparams(images,amill)
        acctlist = "/home/jenkins-cc/jenkins-prod-cc/workspace/Cloud-Custodian/AMI-Auto-Deploy/Accounts.json"
        sharetoaccts(images,amill,acctlist)
        outdic = printimages(images,amill)
        print ("SUCCESS: Sharing AMI's to accounts successful")
        print ("OUTPUT: The following are the latest ImageID's")
        print (outdic)
        sendoutdata(outdic)
    else:
        print ("FAILED: Sharing AMI to regions Failed")
        sendfailureemail("Sharing AMI's to regions failed")

################

if __name__ == "__main__":
    print ("---------------START---------------")
    creddict = getcreds()
    amideploy()
    print ("---------------END---------------")
