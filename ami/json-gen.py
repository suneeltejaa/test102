import json
import boto3

### reading ami-list.json with the latest AMI
def oldAMIid():
	with open('ami-list.json') as data_file:
    	data = json.load(data_file)
		return(data['latest-ami'])

### starting automation
response = client.start_automation_execution(
    DocumentName='amiAution2',
    DocumentVersion='1',
    Parameters={
        'sourceAMIid':'oldAMIid()'
    }
)

### querying AWS for newly created AMI


### creating ami-list.json with the newly created AMI.
response = client.get_automation_execution(
    AutomationExecutionId='string'
)

def writeToJSONFile(path, fileName, data):
	filePathNameWExt = './' + path + "/" + fileName + ".json"
	with open(filePathNameWExt, 'w') as fp:
		json.dump(data, fp)

path = './'
fileName = 'ami-list'

data = {}
data['latest-ami'] = 'ami-123abcd'

writeToJSONFile(path, fileName, data)