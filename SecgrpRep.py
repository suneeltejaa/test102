import os
flist = os.listdir("C:/Users/sri_pavan_tipirneni/Documents/outputs/out/")

import json

# accounts = ['amzcldenva','amzcldenva-2','amzcloud','amzcldtste',
#             'cim-box-prod','cim-nonprod','cim-prod-use1','cim-prod-usw2',
#             'ciqdev','ciqprd','claprd','cspoc2',
#             'incu','infosec-dr',
#             'midev','mipoc','miprd','misprd',
#             'plugprd','poclab',
#             'sp-infosec-prod','symprd']

accounts = ['mipoc']

regions = ['ap-northeast-1','ap-southeast-2','eu-central-1','sa-east-1','us-west-2','ap-northeast-2',
           'ca-central-1','eu-west-1','us-east-1','ap-south-1','eu-west-2','us-east-2','ap-southeast-1',
           'eu-west-3','us-west-1']

path = "C:/Users/sri_pavan_tipirneni/Documents/outputs/out/"

for region in regions:
    fpath = path+region+"/secgrps/resources.json"
    file = open(fpath)
    data = json.load(file)
    print("")
    print (region)
    if len(data) != 0 :
        for ll in data:
            print (ll['GroupName']+"    "+ll["GroupId"])
    else:
        print ("No Impacts")
