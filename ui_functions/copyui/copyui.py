import json, boto3, botocore, os, requests#, urllib2

def setup_handler(event, context):
    uidir="http://raw.githubusercontent.com/hightekvagabond/awsgypsy/" + os.environ['githubbranch'] + "/ui/" 

    indexfile=uidir + event['setupindex']
    s3client = boto3.client("s3")
    #s3client.put_object(Body="this is the setup log", Bucket=os.environ['databucket'], Key='setup_log.txt')
    s3client.put_object(Body=getfilesfromurl(indexfile), Bucket=os.environ['uibucket'], Key='index.html', ContentType='text/html' ) 


    for myfile in event['files'].split(','):
        contenttype='text/plain'
        extention=myfile.split('.')[-1]

        if extention == 'html':
            contenttype='text/html'
        elif extention == 'htm':
            contenttype='text/html'
        elif extention == 'js':
            contenttype='text/javascript'
        elif extention == 'gif':
            contenttype='image/gif'
        elif extention == 'jpg':
            contenttype='image/jpeg'
        elif extention == 'jpeg':
            contenttype='image/jpeg'
        elif extention == 'png':
            contenttype='image/png'
        elif extention == 'css':
            contenttype='text/css'

        s3client.put_object(Body=getfilesfromurl(uidir + myfile), Bucket=os.environ['uibucket'], Key=myfile, ContentType=contenttype ) 


    bucket_location  = s3client.get_bucket_location( Bucket=os.environ['uibucket'])
        
    return {
        "statusCode": 200,
        #"body": json.dumps('You Are Here, But No one else is')
        "body": 'The UI has been copied to the location http://' + os.environ['uibucket'] + '.s3-website-' + bucket_location['LocationConstraint']  + '.amazonaws.com/'
        }


def getfilesfromurl(filename):
    #txt = urllib.urlopen(filename).read()
    r = requests.get(filename)
    #txt = '<html><body>testme</body></html>'
    return r.text


