import os
flist = os.listdir("C:/Users/sri_pavan_tipirneni/Documents/outputs/out/")

import csv

accounts = ['amzcldenva','amzcldenva-2','amzcloud','amzcldtste',
            'cim-box-prod','cim-nonprod','cim-prod-use1','cim-prod-usw2',
            'ciqdev','ciqprd','claprd','cspoc2',
            'incu','infosec-dr',
            'midev','mipoc','miprd','misprd',
            'plugprd','poclab',
            'sp-infosec-prod','symprd']

regions = ['ap-northeast-1','ap-southeast-2','eu-central-1','sa-east-1','us-west-2','ap-northeast-2',
           'ca-central-1','eu-west-1','us-east-1','ap-south-1','eu-west-2','us-east-2','ap-southeast-1',
           'eu-west-3','us-west-1']

exdata = [['Account','Region','Total Instances', 'Non Compliant Instances', 'Compliance Percentage']]

def splitdata(account,region,ty):
    if ty == 'count':
        datatot = open('C:/Users/sri_pavan_tipirneni/Documents/outputs/out/'+account+'/'+region+'/ec2-count/custodian-run.log','r')
    else:
        datatot = open('C:/Users/sri_pavan_tipirneni/Documents/outputs/out/'+account+'/'+region+'/ec2-cft-usage/custodian-run.log','r')
    temp = datatot.read()
    if len(temp) != 0:
        ll = temp.split()
        ret = ll[11].split(':')[1]
        return int(ret)
    else:
        return 'ACCESS DENIED'


def getper(total,cft):
    if total == 0 or cft == 0:
        return int(0)
    elif total == 'ACCESS DENIED' or cft == 'ACCESS DENIED':
        return 'ACCESS DENIED'
    else :
        per = float((cff*100)/total)
        return per

for account in accounts:
    for region in regions:
        ll = []
        ll.append(account)
        ll.append(region)
        tot = splitdata(account,region,'count')
        cff = splitdata(account,region,'cff')
        percentage = getper(tot,cff)
        ll.append(tot)
        ll.append(cff)
        ll.append(percentage)
        exdata.append(ll)


with open('output.csv', mode='w') as outf:
    wr = csv.writer(outf,dialect='excel')
    wr.writerows(exdata)

##data.split()
##data[2].split(':')
##region==data[1]
##count == data[2]
