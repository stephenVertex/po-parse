#!/bin/bash

echo "Uploading AWS Lambda bundle"
aws --profile bredal2 lambda update-function-code --function-name bredal-po-parser --zip-file fileb://my-deployment-package.zip
echo "DONE"
