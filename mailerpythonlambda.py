import boto3

def getec2details(event, context):
    tolist = []
    idlist = []
    fflist = []
    ec2client = boto3.client('ec2')
    response = ec2client.describe_instances(
                    Filters=[
                        {
                            'Name': 'tag-key',
                            'Values': ['auto_patching']}])['Reservations']
    # tolist = ['sri.pavan.tipirneni@spglobal.com'] #debug
    if len(response) != 0:
        for values in response:
            taglist = values['Instances'][0]['Tags']
            for keys in taglist:
                if keys['Key'] == 'Owner' or keys['Key'] == 'owner' or keys['Key'] == 'creatorid' or keys['Key'] == 'CreatorId':
                    if keys['Value'] not in tolist:
                        tolist.append(keys['Value'].lower())
    else:
        tolist.append('mi-aws-cloudcustodian@spglobal.com')
    for emails in tolist:
        if emails not in fflist:
            fflist.append(emails)
    if len(response) != 0:
        for data in response:
            if data['Instances'][0]['InstanceId'] not in idlist:
                idlist.append(data['Instances'][0]['InstanceId'])
    else:
        idlist.append("No Instances available for patching")
    for add in fflist:
        #print (add) ## debug
        if add.find('@') < 0:
            fflist.remove(add)
            #print ('removed:',add) ##debug
    return fflist,idlist

def lambda_handler(event, context):
    toemaillist,instanceslist = getec2details(event, context)
    sescli = boto3.client('ses')
    print("Sending email to {0}".format(toemaillist) )
    strTable = "<tr><th>InstanceID</th></tr>"
    for values in instanceslist:
        strRW = "<tr><td>"+values+"</td></tr>"
        strTable = strTable+strRW
    BODY_HTML = """<html><head><style>table, th, td {border: 1px solid black;}</style></head><body><h2>EC2 Patching"""+ event['processstage']+"""</h2><p> Below is the list of Instances that are being patched</p><table style="width:30%">"""+strTable+"""</table></body></html>"""
    data = 'EC2 Patching has'+event['processstage']
    sescli.send_email(
                        Source= 'mi-aws-cloudcustodian@spglobal.com',
                        Destination={'ToAddresses': toemaillist},
                        Message={
                            'Subject': { 'Data': data},
                            'Body': {'Html': {'Charset': "UTF-8",'Data': BODY_HTML}}})

#### Invoking payload details
##"Payload": "{\"processstage\":\"starting\"}"
##"Payload": "{\"processstage\":\"has ended\"}"
## lambda test event data
# {
#   "processstage": " has started."
# }
