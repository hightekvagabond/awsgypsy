#!/usr/bin/python


import sys

if len(sys.argv) < 3:
	print '''
Usage: ./find_instances_by.py <attribute> <value>
Example:
   To find all instances with a key of MyKeyPair:
   ./find_instnaces_by.py KeyName MyKeyPair
'''
	sys.exit(0) 



findby = sys.argv[1]
findval = sys.argv[2]

import boto3    
ec2client = boto3.client('ec2')





from array import array
conn = array('i')
i = 1
# Retrieves all regions/endpoints that work with EC2
regions =  ec2client.describe_regions()
for region in regions['Regions']:
	regionname = region["RegionName"]
	#based on this: https://www.slsmk.com/how-to-use-python-boto3-to-list-instances-in-amazon-aws/
#	ec2client.setup_default_session(region_name=region["RegionName"])
	boto3.Session(region_name=region["RegionName"])
	conn = boto3.client('ec2',region_name=region["RegionName"]) #need to connect to each region individually
	response = conn.describe_instances() #http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
	#response = conn.describe_instances()
	for reservation in response["Reservations"]:
	    for instance in reservation["Instances"]:
		if instance[findby] == findval:
			# This sample print will output entire Dictionary object
			#print(instance)
			# This will print will output the value of the Dictionary key 'InstanceId'
			print regionname,":",instance["Placement"]["AvailabilityZone"],instance["InstanceId"],":",findby,":",instance[findby]," (",instance["State"]["Name"],")"
