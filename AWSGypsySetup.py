import json, boto3, botocore, os

def setup_handler(event, context):
    # TODO implement
    s3client = boto3.client("s3")
    s3client.put_object(Body="this is the setup log", Bucket=os.environ['databucket'], Key='setup_log.txt')
    return {
        "statusCode": 200,
        "body": json.dumps('You Are Here, But No one else is')
    }

