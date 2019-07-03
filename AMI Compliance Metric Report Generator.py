import os
flist = os.listdir("C:/Users/sri_pavan_tipirneni/Documents/CC policy outputs")

import csv

accounts = ['amzcldenva','cim-prod-use1','cspoc1','migsnp', 'mispprd','symprd',
'amzcldenva-2','cim-prod-usw2','cspoc2','migsprd','plugprd',
'amzcloud','ciqdev', 'incu','mipoc','poclab',
'cim-box-prod','ciqprod','infosec-dr','miprd','spg-billing',
'cim-nonprod', 'claprd', 'midev', 'mispnp', 'sp-infosec-prod']

regions = ['ap-northeast-1','ap-southeast-2','eu-central-1','sa-east-1','us-west-2','ap-northeast-2',
'ca-central-1','eu-west-1','us-east-1','ap-south-1','eu-west-2','us-east-2','ap-southeast-1',
'eu-west-3','us-west-1']

exdata = [['Account','Region','Total Instances', 'Non Compliant Instances', 'Compliance Percentage']]

def splitdata(account,region,ty):
    if ty == 'count':
        datatot = open('/home/centos/sri-test-run/out/'+account+'/'+region+'/ec2-count/custodian-run.log','r')
    else:
        datatot = open('/home/centos/sri-test-run/out/'+account+'/'+region+'/ec2-invalid-ami/custodian-run.log','r')
    temp = datatot.read()
    if len(temp) != 0:
        ll = temp.split()
        ret = ll[11].split(':')[1]
        return int(ret)
    else:
        return 'ACCESS DENIED'
    

def getper(total,invalid):
    if total == 0 or invalid == 0:
        print 'yes'
        return int(100)
    elif total == 'ACCESS DENIED' or invalid == 'ACCESS DENIED':
        print 'yes22'
        return 'ACCESS DENIED'
    else :
        per = (float(total - invalid)/total)*100
        print (per)
        return per

for account in accounts:
    for region in regions:
        ll = []
        ll.append(account)
        ll.append(region)
        tot = splitdata(account,region,'count')
        inv = splitdata(account,region,'inv')
        percentage = getper(tot,inv)
        ll.append(tot)
        ll.append(inv)
        ll.append(percentage)
        exdata.append(ll)


with open('output.csv', mode='w') as outf:
    wr = csv.writer(outf,dialect='excel')
    wr.writerows(exdata)

##data.split()
##data[2].split(':')
##region==data[1]
##count == data[2]
