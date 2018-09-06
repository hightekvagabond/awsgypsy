#!/usr/bin/python

import  boto3
from botocore.client import ClientError

def main():
	getprefs()

def getprefs():
	CONFIG = dict()
	print "\n\nThis is the installation script for awsgypsy, to use it you must have admin access connected to your awscli profile for the account you wish to install into.\n\n"
	CONFIG["account"] = raw_input("What is the aws account number for the account you are installing into? ")
	CONFIG["profile"] = raw_input("Which awscli credentials profile do you wish to use to? [default]  ")
	if CONFIG["profile"] == "":
		CONFIG["profile"] = 'default'



        session = boto3.session.Session(profile_name=CONFIG["profile"])

	#check if the user has admin privs
	actions = blocked(session,actions=[ "iam:ListUsers", "iam:ListAccessKeys", "iam:DeleteAccessKey", "iam:ListGroupsForUser", "iam:RemoveUserFromGroup", "iam:DeleteUser" ])
	print(actions)


	
	default_databucket = "awsgypsy-data-" + CONFIG["account"]
	CONFIG["databucket"] = raw_input("S3 Data Bucket for storing policies and user data? [" + default_databucket + "] ")


	if CONFIG["databucket"] == default_databucket :
		s3 = session.client("s3")
		CONFIG["databucket"] = namedatabucket(s3,"awsgypsy-data-" + CONFIG["account"], 0)

	print("bucketname: " + CONFIG["databucket"])
#	print "Because of the way awsgypsy works it needs to be installed individually into each region, we recomend you install into all regions even the ones you are not using so that it can watch for intrusions in other regions that you are not likely to notice as you do not log into those.\n\n"
	return CONFIG


# this function figures out what the name of the bucket should be and creates it
def namedatabucket (s3, name, count):
	bucketexists = False
	bucketname = name
	if count > 0:
		bucketname = bucketname + "-" + str(count)
	try:
    		s3.head_bucket(Bucket=bucketname)
		keep_bucket = raw_input("This bucket already exists and you have access to it. Would you like to use the existing data bucket? [y/n] ")
		if (keep_bucket.lower()[:1] == "y"):
			print("Using existing bucket '" + bucket_name + "' for data and configuration")
		else:
			print("Adding a count index to the bucket name and trying again....")
			bucketexists = True
	except ClientError:
    		# The bucket does not exist or you have no access.
		try:
	    		s3.create_bucket(Bucket=bucketname) 
		except ClientError:
 	    		#print("failed to create " + bucketname)
			bucketexists = True
	if bucketexists == True:
	    count = count + 1 #this bucket exists, give it a number
	    bucketname = namedatabucket(s3,name,count)

	return bucketname


def blocked(session, actions, resources=None, context=None):
    """test whether IAM user is able to use specified AWS action(s)

    Args:
        actions (list): AWS action(s) to verify the IAM user can use.
        resources (list): Check if action(s) can be used on resource(s). 
            If None, action(s) must be usable on all resources ("*").
        context (dict): Check if action(s) can be used with context(s). 
            If None, it is expected that no context restrictions were set.

    Returns:
        list: Actions denied by IAM due to insufficient permissions.
    """



    aws_iam_client = session.client('iam')
    current_user_arn  = session.client('sts').get_caller_identity()['Arn']



    if not actions:
        return []
    actions = list(set(actions))

    if resources is None:
        resources = ["*"]

    if context is not None:
        # Convert context dict to what ContextEntries expects.
        context_temp = []
        for context_key in context:
            context_temp.append({
                'ContextKeyName': context_key,
                'ContextKeyValues': [str(val) for val in context[context_key]],
                'ContextKeyType': "string"
            })
        context = context_temp
    else:
        context = [{}]

    # You'll need to create an IAM client for this
    results = aws_iam_client.simulate_principal_policy(
        PolicySourceArn=current_user_arn, # Put your IAM user's ARN here
        ActionNames=actions,
        ResourceArns=resources,
        ContextEntries=context
    )['EvaluationResults']

    blocked_actions = []
    for result in results:
        if result['EvalDecision'] != "allowed":
            blocked_actions.append(result['EvalActionName'])

    return sorted(blocked_actions)


main()
