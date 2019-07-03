import os
import boto3
from datetime import datetime
import csv
cspoc2
accounts = {'amzcldenva':'299975258897-ADFS-MHF-SystemAdministrator',
            'amzcldenva-2':'128927813985-ADFS-MHF-SystemAdministrator',
            'amzcloud':'011275511485-ADFS-MHF-SystemAdministrator',
            'amzcldtste':'130312249203-ADFS-MHF-SystemAdministrator',
            'cim-box-prod':'400387983702-ADFS-MHF-SystemAdministrator',
            'cim-nonprod':'277141866027-ADFS-MHF-SystemAdministrator',
            'cim-prod-use1':'947044032016-ADFS-MHF-SystemAdministrator',
            'cim-prod-usw2':'198052631016-ADFS-MHF-SystemAdministrator',
            'ciqdev':'304987092631-ADFS-MHF-PowerUser',
            'ciqprd':'971173505912-ADFS-MHF-PowerUser',
            'claprd':'160647469903-ADFS-MHF-PowerUser',
            'cspoc2':'608515732360-ADFS-MHF-SystemAdministrator',
            'incu':'063706574754-ADFS-MHF-PowerUser',
            'infosec-dr':'538235630974-ADFS-MHF-SystemAdministrator',
            'midev':'530710445070-ADFS-MHF-PowerUser',
            'mipoc':'245930108294-ADFS-MHF-PowerUser',
            'miprd':'027532563197-ADFS-MHF-PowerUser',
            'misprd':'190101517450-ADFS-MHF-PowerUser',
            'plugprd':'452127281478-ADFS-MHF-PowerUser',
            'poclab':'703722312672-ADFS-MHF-PowerUser',
            'sp-infosec-prod':'854422766513-ADFS-MHF-SystemAdministrator',
            'symprd':'396496193604-ADFS-MHF-PowerUser'}

regions = ['ap-northeast-1','ap-southeast-2','eu-central-1','sa-east-1','us-west-2','ap-northeast-2',
           'ca-central-1','eu-west-1','us-east-1','ap-south-1','eu-west-2','us-east-2','ap-southeast-1',
           'eu-west-3','us-west-1']

regionscsv = ['','ap-northeast-1','ap-southeast-2','eu-central-1','sa-east-1','us-west-2','ap-northeast-2',
           'ca-central-1','eu-west-1','us-east-1','ap-south-1','eu-west-2','us-east-2','ap-southeast-1',
           'eu-west-3','us-west-1']

policies = ['high-risk-security-groups-remediate','terminate-public-rds',
's3-global-acl-remediate','terminate-unencrypted-rds',
's3-configure-standards-real-time','s3-deny-http-traffic']

def getstats(funcname):
    response = client.get_metric_statistics(
        Namespace='AWS/Lambda',
        MetricName='Invocations',
        Dimensions=[
            {
                'Name': 'FunctionName',
                'Value': funcname
            },
        ],
        StartTime=datetime(2018, 12, 1),
        EndTime=datetime(2019, 1, 1),
        Period=86400,
        Statistics=[
            'Average',
        ],
    )
    data = response['Datapoints']
    i = 0
    for dat in data:
        i = i+int(dat['Average'])
    return i

a = []
for keys in accounts:
    lis = []
    lis.append([keys])
    lis.append(regionscsv)
    f1 = ['high-risk-security-groups-remediate']
    f2 = ['terminate-public-rds']
    f3 = ['s3-global-acl-remediate']
    f4 = ['terminate-unencrypted-rds']
    f5 = ['s3-configure-standards-real-time']
    f6 = ['s3-deny-http-traffic']
    profile= accounts[keys]
    print (keys)
    for region in regions:
        #print(region)
        i = 1
        session = boto3.Session(profile_name=profile,region_name=region)
        client = session.client('cloudwatch')
        for data in policies:
            print (i)
            funcname = 'custodian-'+data
            hh = getstats(funcname)
            if i == 1:
                f1.append(hh)
            elif i ==2:
                f2.append(hh)
            elif i ==3:
                f3.append(hh)
            elif i ==4:
                f4.append(hh)
            elif i ==5:
                f5.append(hh)
            else:
                f6.append(hh)
            i = i+1
    lis.append(f1)
    lis.append(f2)
    lis.append(f3)
    lis.append(f4)
    lis.append(f5)
    lis.append(f6)
    print (lis)
    a.append(lis)

with open('output.csv', mode='w') as outf:
    wr = csv.writer(outf,dialect='excel')
    for rows in a:
        wr.writerows(rows)
