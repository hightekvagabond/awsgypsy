import json, boto3, botocore, os#, urllib2

def setup_handler(event, context):
	indexfile="https://raw.githubusercontent.com/hightekvagabond/awsgypsy/work/ui/index.html"
	s3client = boto3.client("s3")
	s3client.put_object(Body="this is the setup log", Bucket=os.environ['databucket'], Key='setup_log.txt')
	#s3client.put_object(Body=getfilesfromurl(indexfile), Bucket=os.environ['uibucket'], Key='index.html', Metadata={'Content-Type': 'text/html'})
	return {
		"statusCode": 200,
		#"body": json.dumps('You Are Here, But No one else is')
		"body": 'You Are Here, But No one else is'
    		}


def getfilesfromurl(filename):
	txt = urllib.urlopen(filename).read()
	return txt


