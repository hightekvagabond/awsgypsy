import json, boto3, botocore, os, requests#, urllib2

def setup_handler(event, context):
    uidir="http://raw.githubusercontent.com/hightekvagabond/awsgypsy/" + os.environ['githubbranch'] + "/ui/" 
    indexfile=uidir + "setup_index.html"
    s3client = boto3.client("s3")
    s3client.put_object(Body="this is the setup log", Bucket=os.environ['databucket'], Key='setup_log.txt')
    s3client.put_object(Body=getfilesfromurl(indexfile), Bucket=os.environ['uibucket'], Key='index.html', ContentType='text/html' ) 
    for myfile in event['files'].split(','):
        s3client.put_object(Body=getfilesfromurl(uidir + myfile), Bucket=os.environ['uibucket'], Key=myfile, ContentType='text/html' ) 
        
    return {
        "statusCode": 200,
        #"body": json.dumps('You Are Here, But No one else is')
        "body": 'You Are Here, But No one else is'
        }


def getfilesfromurl(filename):
    #txt = urllib.urlopen(filename).read()
    r = requests.get(filename)
    #txt = '<html><body>testme</body></html>'
    return r.text


