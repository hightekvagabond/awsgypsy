#!/bin/bash

#move these out to config once it's tested
snstopic='ai-infra-cloudtrail-toggle'
#account=$1
account='830488934692'
email='grogers@nvidia.com'
tmpdir='/tmp/keep_on_cloudtrail'
region='us-west-2'


#Note: in my .aws/credentials file I keep a profile for each account by account number for this to work for you then you need to do the same
#      Long term, when we move to running these things with roles via lambda it will get easier
#
# ie.
# for account 123456789
# there would be an entry in my ~/.aws/credentials that looks like this:
# [123456789]
# aws_access_key_id =  xxxxxxxxxxxxx
# aws_secret_access_key = xxxxxxxxxxxxx
#


snsarn="arn:aws:sns:us-west-2:${account}:${snstopic}"

#delete the sns if it already exists to make it all clean
aws sns --profile "${account}" --region us-west-2 delete-topic --topic-arn "${snsarn}"

#create the sns 
aws sns --profile "${account}" --region us-west-2 create-topic --name "${snstopic}"

#subscribe to the sns
#aws sns --profile "${account}" --region us-west-2 subscribe --topic-arn "${snsarn}" --protocol email --notification-endpoint "${email}"



mkdir -p  "${tmpdir}/"

cp CloudTrailToggleProcessing.js "${tmpdir}/"

#Note: sed requires the empty string after -i on MacOsX, you need to take it out on linux
eval "sed -i '.bak' 's/##sns-arn##/${snsarn}/g' ${tmpdir}/CloudTrailToggleProcessing.js"
#uncomment for linux:
#eval "sed -i 's/##sns-arn##/${snsarn}/g' ${tmpdir}/CloudTrailToggleProcessing.js"





echo "you should delete the temp dir:"
echo "        rm -rf ${tmpdir}"
