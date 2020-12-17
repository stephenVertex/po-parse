#!/bin/bash

aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 750813457616.dkr.ecr.ap-southeast-2.amazonaws.com
docker build . -t docker-lambda
docker tag docker-lambda 750813457616.dkr.ecr.ap-southeast-2.amazonaws.com/bredal/tabularunner:latest
docker push 750813457616.dkr.ecr.ap-southeast-2.amazonaws.com/bredal/tabularunner:latest
