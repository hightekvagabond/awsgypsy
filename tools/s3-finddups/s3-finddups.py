#!/usr/bin/python

#this script finds all your duplicate files across multiple buckets, but you need to have read access to all buckets

import boto3
import botocore
import random
import time
import psycopg2




def main():
	dbuser = 'awsgypsy'
	dbpass = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(10))
	stackinfo = createcloudformation(dbuser,dbpass)
	walk_buckets(stackinfo[1],dbuser,dbpass)
	#deletecloudformation(stackinfo[0])


#This function walks through all the buckets in your account and finds all the objects pulling out identifying information
def walk_buckets(dbhost,dbuser,dbpass):
	#s3 = boto3.resource('s3')
	s3_conn = boto3.client(service_name='s3')
    	connect_str = "dbname='awsgypsy_s3_dups_tmp_db' user='awsgypsy' host='" + dbhost + "'  password='" + dbpass + "'"
	print connect_str
    	db_conn = psycopg2.connect(connect_str)
    	# create a psycopg2 cursor that can execute queries
    	cursor = db_conn.cursor()
    	# create a new table with a single column called "name"
    	cursor.execute("""CREATE TABLE s3objects (account text, bucket text, path text, filename text, isdir boolean, md5sum text, size text);""")
	db_conn.commit()
	for bucket in s3_conn.list_buckets()['Buckets']:
	    bucketname = bucket['Name']
	    print("Checking Bucket: " + bucketname)
	    #for obj in bucket.objects.all():
	    objects = []
	    try: 
		objects = s3_conn.list_objects(Bucket=bucketname)['Contents'] #this fails on empty buckets, so we have to use the try
	    except:
    		print( bucketname + ' was empty')
	    
	    for obj in objects:
		#md5sum = s3_conn.head_object(Bucket=bucketname,Key=obj['Key'])['ETag'][1:-1]
		md5sum = obj['ETag']
		pathparts = obj['Key'].split('/')
		filename = pathparts.pop()
		path = "/"+"/".join(pathparts)
		print('{0}:{1}/{2} {3} {4}'.format(bucketname, path.encode('ascii', 'ignore'), filename.encode('ascii', 'ignore'), md5sum, obj['Size']))
		#cursor.execute("""INSERT INTO s3objects (account, bucket, path , filename , isdir , md5sum , size ) VALUES ('default', '" + join("','",[ bucketname, path.encode('ascii', 'ignore'), filename.encode('ascii', 'ignore'), False, md5sum, obj['Size'] ]) +  "'" );""")


		#sqlcmd = "INSERT INTO s3objects (account, bucket, path , filename , isdir , md5sum , size ) VALUES ('default', '" + "','".join( [ bucketname, path.encode('ascii', 'ignore'), filename.encode('ascii', 'ignore'), "False", md5sum, str(obj['Size']) ] ) +  "')"
		#cursor.execute(sqlcmd)
		cursor.execute("INSERT INTO s3objects (account, bucket, path , filename , isdir , md5sum , size ) VALUES ('default', %s, %s, %s, %s, %s )", ( [ bucketname, path.encode('ascii', 'ignore'), filename.encode('ascii', 'ignore'), "False", md5sum, str(obj['Size']) ] ) )




	db_conn.commit()
    	cursor.execute("""SELECT * from s3objects""")
    	rows = cursor.fetchall()
    	print(rows)

def createcloudformation(dbuser,dbpass):
	with open('cloudformation-db-s3-finddups.cf', 'r') as mytemplate:
    		formation_template=mytemplate.read()
	cf_client = boto3.resource('cloudformation')
	stackname = 'awsgypsy-s3-dupfinder-tmp-' + str(int(time.time()))
	response = cf_client.create_stack(
	    StackName=stackname,
	    TemplateBody=formation_template,
	    Parameters=[
		{
		    'ParameterKey': 'dbuser',
		    'ParameterValue': dbuser
		},
		{
		    'ParameterKey': 'dbpass',
		    'ParameterValue': dbpass
		}

	    ],
	    Tags=[ { 'Key': 'Name', 'Value': 'awsgypsy-s3-dup-temp-db-cf' }, ]
	)
	print "Creating stack " + stackname + " ...this may take a while (7 to 10 minutes) because it's creating a database..."
	stackstatus = 'creating'
	while stackstatus != 'CREATE_COMPLETE':
		time.sleep(60)
		stackstatus = cf_client.meta.client.describe_stacks(StackName=stackname)['Stacks'][0]['StackStatus']
		print stackstatus + "..."
	print cf_client.meta.client.describe_stacks(StackName=stackname)['Stacks'][0]['Outputs']
	dbhost = cf_client.meta.client.describe_stacks(StackName=stackname)['Stacks'][0]['Outputs'][0]['OutputValue']
	#print "dbhost:" + dbhost
	print "Stack Created"
	#print response
	return [ stackname, dbhost ]


def deletecloudformation(mystack):
	cf_client = boto3.resource('cloudformation')
	response = cf_client.meta.client.delete_stack( StackName=mystack )
	print "deleting stack " + mystack





main()
