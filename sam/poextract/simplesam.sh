#!/bin/bash
clear



if pylint -E po_extract/app.py ; then
    echo "Pylint succeeded. Building."
    sam build

    echo "DEPLOY: Creating CloudFront changeset and deploying..."
    sam deploy

    if [ $? -eq 0 ]
    then 
	cowsay "po-parse deploy is complete"
    else
	cowsay "po-parse deploy failed"
    fi
else
    echo "Pylint failed"
fi


echo "BUILD: Building SAM resources..."
