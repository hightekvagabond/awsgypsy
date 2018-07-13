

########################
# This function saves a lot to an aws bucket for later review, 
# keeping them in a specific place makes it easier to find and so 
# that it won't be auto deleted before it's reviewed
# 
#Example of How to call:
#
#eventlog = ""
#if 'awsgypsybucket' in os.environ.keys():
#        eventlog = SaveToS3(os.environ['awsgypsybucket'],event['id'],json.dumps(event, indent=2))
#
########################
def SaveToS3(bucket,id,message):
    s3client = boto3.client('s3')
    mykeyname = 'Logs/' + myscriptname + '/' + id + '.json'
    s3client.put_object(Body=message, Bucket=bucket, Key=mykeyname)
    return("s3://" + bucket + "/" + mykeyname)


        
########################
# This function sends a message to an SNS,
# in theory an admin is subscribed to that SNS and receives an email
#
#Example of How to call:
#
#if 'snsarn' in os.environ.keys():
#   PublishToSNS(os.environ['snsarn'],'This is my message')
########################
   
    
def PublishToSNS(sns,message):
    client = boto3.client('sns')
    response = client.publish( TopicArn=sns,  Message=message)
