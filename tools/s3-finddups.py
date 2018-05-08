import boto3
import botocore

def s3_md5sum(bucket_name, resource_name):
    try:
        md5sum = boto3.client('s3').head_object(
            Bucket=bucket_name,
            Key=resource_name
        )['ETag'][1:-1]
    except botocore.exceptions.ClientError:
        md5sum = None
        pass
    return md5sum
