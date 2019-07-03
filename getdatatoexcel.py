import json
import csv

file_directory = "C:/Users/sri_pavan_tipirneni/Documents/data.json" ## modify data here

json_data= open(file_directory).read()

data = json.loads(json_data)

exdata = [['InstanceID','ImageID','Owner','VpcID','State']]

def gettagdata(tagdata):
    ret = 'No Tag Data'
    if len(tagdata) == 0:
        return ret
    else :
        for data in tagdata:
            if data['Key'] == 'Owner' or 'owner':
                ret = data['Value']
                print (ret)
        return ret

def getstate(stdata):
    if len(stdata) == 0:
        return 'No State Data'
    else:
        return stdata['Name']

for info in data:
    ll = []
    ll.append(info['InstanceId'])
    ll.append(info['ImageId'])
    ll.append(gettagdata(info['Tags']))
    ll.append(info['VpcId'])
    ll.append(getstate(info['State']))
    exdata.append(ll)
    
with open('output.csv', mode='w') as outf:
    wr = csv.writer(outf,dialect='excel')
    wr.writerows(exdata)
