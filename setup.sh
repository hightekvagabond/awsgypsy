#!/bin/bash


pip install awscli --upgrade --user

npm install -g serverless

sls create -n awsgypsy -t aws-python3

sls plugin install -n serverless-python-requirements


