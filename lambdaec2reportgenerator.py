import json
import boto3,os
from os.path import expanduser

arns = ["arn:aws:iam::299975258897:role/CloudCustodian-amzcldenva",
"arn:aws:iam::128927813985:role/CloudCustodian-amzcldenva-2",
"arn:aws:iam::130312249203:role/CloudCustodian-amzcldtste",
"arn:aws:iam::011275511485:role/CloudCustodian-amzcloud",
"arn:aws:iam::400387983702:role/CloudCustodian-cim-box-prod",
"arn:aws:iam::277141866027:role/CloudCustodian-cim-nonprod",
"arn:aws:iam::947044032016:role/CloudCustodian-cim-prod-use1",
"arn:aws:iam::198052631016:role/CloudCustodian-cim-prod-usw2",
"arn:aws:iam::304987092631:role/CloudCustodian-ciqdev",
"arn:aws:iam::971173505912:role/CloudCustodian-ciqprod",
"arn:aws:iam::160647469903:role/CloudCustodian-claprd",
"arn:aws:iam::608515732360:role/CloudCustodian-cspoc2",
"arn:aws:iam::063706574754:role/CloudCustodian-incu",
"arn:aws:iam::538235630974:role/CloudCustodian-infosec-dr",
"arn:aws:iam::530710445070:role/CloudCustodian-midev",
"arn:aws:iam::245930108294:role/CloudCustodian-mipoc",
"arn:aws:iam::027532563197:role/CloudCustodian-miprd",
"arn:aws:iam::190101517450:role/CloudCustodian-mispprd",
"arn:aws:iam::452127281478:role/CloudCustodian-plugprd",
"arn:aws:iam::703722312672:role/CloudCustodian-poclab",
"arn:aws:iam::854422766513:role/CloudCustodian-sp-infosec-prod",
"arn:aws:iam::772448015211:role/CloudCustodian-spg-billing",
"arn:aws:iam::396496193604:role/CloudCustodian-symprd",
"arn:aws:iam::557350676069:role/CloudCustodian-pltssb",
"arn:aws:iam::266472205365:role/CloudCustodian-miqa",
"arn:aws:iam::228748083573:role/CloudCustodian-mipprod",
"arn:aws:iam::681141260920:role/CloudCustodian-mipdev",
"arn:aws:iam::111588580784:role/CloudCustodian-miintprodstg",
"arn:aws:iam::524234064850:role/CloudCustodian-miintdev",
"arn:aws:iam::172185050124:role/CloudCustodian-cladrstg"]

regions = ['ap-northeast-1','ap-southeast-2','eu-central-1','sa-east-1','us-west-2','ap-northeast-2',
           'ca-central-1','eu-west-1','us-east-1','ap-south-1','eu-west-2','us-east-2','ap-southeast-1',
           'eu-west-3','us-west-1']

def getec2client(region,creddict):
    client = boto3.client('ec2',
                              aws_access_key_id=creddict['AccessKeyId'],
                              aws_secret_access_key=creddict['SecretAccessKey'],
                              aws_session_token=creddict['SessionToken'],
                              region_name=region)
    return client

def getsecgrps(secdat):
    a=0
    if len(secdat) != 0:
        if len(secdat) ==5:
            a=1
    return a

def getec2data(dat,region):
    li=''
    a=getsecgrps(dat['Instances'][0]['SecurityGroups'])
    if a ==1:
        li=dat['Instances'][0]['InstanceId']
    return li

def getcreds(arn):
    client = boto3.client('sts')
    response = client.assume_role(RoleArn=arn,RoleSessionName='ReportGenerator')['Credentials']
    #print (response)
    return response

def getname(arn):
    li =  arn.split('-')
    if len(li) == 2:
        return li[1]
    else:
        acctname=''
        i =1
        a = len(li)
        while True:
            if i<a:
                acctname = acctname+str(li[i])
                i=i+1
            else:
                break
        return acctname

def sendemail(data,arn):
    acctname = getname(arn)
    print ("sending email account {0} in all regions".format(acctname))
    sescli = boto3.client('ses')
    toemaillist = ['sri.pavan.tipirneni@spglobal.com','r.innamuri@spglobal.com','Patrick.Horrigan@spglobal.com']
    strTable = "<tr><th>InstanceID</th></tr>"
    for values in data:
        strRW = "<tr><td>"+values+"</td></tr>"
        strTable = strTable+strRW
    BODY_HTML = """<html><head><style>table, th, td {border: 1px solid black;}</style></head><body><h2>EC2 with high number of secuirty groups attached"""+"""</h2><p> Below is the list of Instances that have 5 secuirty groups attached</p><table style="width:30%">"""+strTable+"""</table></body></html>"""
    data = "EC2 Instances with more than 4 Security Groups attached"+'----'+acctname
    sescli.send_email(
                        Source= 'corp-aws-cloudcustodian@spglobal.com',
                        Destination={'ToAddresses': toemaillist},
                        Message={
                            'Subject': { 'Data': data},
                            'Body': {'Html': {'Charset': "UTF-8",'Data': BODY_HTML}}})
    print ("Sent Email")

def runmain():
    for arn in arns:
        ll=[]
        daou=[]
        creddict = getcreds(arn)
        for region in regions:
            client = getec2client(region,creddict)
            out = client.describe_instances()['Reservations']
            if len(out) !=0:
                for data in out:
                    ll =  getec2data(data,region)
                    if len(ll)!=0:
                        daou.append(ll)
        #print (daou)
        if len(daou) != 0:
            sendemail(daou,arn)

def lambda_handler(event, context):
    print("Starting Execution")
    runmain()
    print("Ending Execution")
