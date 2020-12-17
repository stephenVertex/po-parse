#!/bin/bash

aws --profile bredal2 ecr create-repository --repository-name bredal/tabularunner  --region ap-southeast-2

# {
#     "repository": {
#         "repositoryArn": "arn:aws:ecr:ap-southeast-2:750813457616:repository/bredal/tabularunner",
#         "registryId": "750813457616",
#         "repositoryName": "bredal/tabularunner",
#         "repositoryUri": "750813457616.dkr.ecr.ap-southeast-2.amazonaws.com/bredal/tabularunner",
#         "createdAt": "2020-12-17T10:41:07+11:00",
#         "imageTagMutability": "MUTABLE",
#         "imageScanningConfiguration": {
#             "scanOnPush": false
#         },
#         "encryptionConfiguration": {
#             "encryptionType": "AES256"
#         }
#     }
# }
