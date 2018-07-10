def SaveToS3(bucket,id,message):
    s3client = boto3.client('s3')
    s3client.put_object(Body=message, Bucket=bucket, Key='Logs/' + myscriptname + '/' + id + '.json')
    
def PublishToSNS(sns,message):
    client = boto3.client('sns')
    response = client.publish( TopicArn=sns,  Message=message)
