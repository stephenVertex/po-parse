#!/bin/bash
clear
echo "BUILD: Building SAM resources..."
sam build

echo "DEPLOY: Creating CloudFront changeset and deploying..."
sam deploy

if [ $? -eq 0 ]
then 
    say po-parse deploy is complete
else
    say po-parse deploy failed
fi
